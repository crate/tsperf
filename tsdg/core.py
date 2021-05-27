# -*- coding: utf-8; -*-
#
# Licensed to Crate.io GmbH ("Crate") under one or more contributor
# license agreements.  See the NOTICE file distributed with this work for
# additional information regarding copyright ownership.  Crate licenses
# this file to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  You may
# obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations
# under the License.
#
# However, if you have executed another commercial license agreement
# with Crate these terms will supersede the license and you may use the
# software solely pursuant to the terms of the relevant commercial agreement.

import json
import logging
import sys
import time
from queue import Empty, Queue
from threading import Thread, current_thread
from typing import Optional, Tuple

from prometheus_client import start_http_server
from tqdm import tqdm

from tsdg.adapter.cratedb import CrateDbAdapter
from tsdg.adapter.influxdb import InfluxDbAdapter
from tsdg.adapter.mongodb import MongoDbAdapter
from tsdg.adapter.mssql import MsSQLDbAdapter
from tsdg.adapter.postgresql import PostgresDbAdapter
from tsdg.adapter.timescaledb import TimescaleDbAdapter
from tsdg.adapter.timestream import TimeStreamAdapter
from tsdg.cli import parse_arguments
from tsdg.config import DataGeneratorConfig
from tsdg.model.database import AbstractDatabaseAdapter
from tsdg.model.edge import Edge
from tsdg.model.metrics import (
    c_generated_values,
    c_inserted_values,
    c_inserts_failed,
    c_inserts_performed_success,
    c_values_queue_was_empty,
    g_batch_size,
    g_best_batch_rps,
    g_best_batch_size,
    g_insert_percentage,
    g_insert_time,
    g_rows_per_second,
)
from tsdg.util import tictrack
from tsdg.util.batch_size_automator import BatchSizeAutomator
from tsdg.util.common import setup_logging

# global variables shared accross threads
config = DataGeneratorConfig()
model = {}
last_ts = 0
current_values_queue = Queue(10000)
inserted_values_queue = Queue(10000)
stop_queue = Queue(1)
insert_finished_queue = Queue(1)
insert_exceptions = Queue()

logger = logging.getLogger(__name__)


def get_database_adapter() -> AbstractDatabaseAdapter:  # noqa
    if config.database == 0:  # crate
        adapter = CrateDbAdapter(
            config.host,
            config.username,
            config.password,
            model,
            config.table_name,
            config.shards,
            config.replicas,
            config.partition,
        )
    elif config.database == 1:  # timescale
        adapter = TimescaleDbAdapter(
            config.host,
            config.port,
            config.username,
            config.password,
            config.db_name,
            model,
            config.table_name,
            config.partition,
            config.copy,
            config.distributed,
        )
    elif config.database == 2:  # influx
        adapter = InfluxDbAdapter(
            config.host, config.token, config.organization, model, config.db_name
        )
    elif config.database == 3:  # mongo
        adapter = MongoDbAdapter(
            config.host, config.username, config.password, config.db_name, model
        )
    elif config.database == 4:  # postgres
        adapter = PostgresDbAdapter(
            config.host,
            config.port,
            config.username,
            config.password,
            config.db_name,
            model,
            config.table_name,
            config.partition,
        )
    elif config.database == 5:  # timestream
        adapter = TimeStreamAdapter(
            config.aws_access_key_id,
            config.aws_secret_access_key,
            config.aws_region_name,
            config.db_name,
            model,
        )
    elif config.database == 6:  # ms_sql
        adapter = MsSQLDbAdapter(
            config.host,
            config.username,
            config.password,
            config.db_name,
            model,
            port=config.port,
            table_name=config.table_name,
        )
    else:
        adapter = None
    return adapter


@tictrack.timed_function()
def create_edges() -> dict:
    # this function creates metric objects in the given range [id_start, id_end]
    edges = {}
    for i in tqdm(range(config.id_start, config.id_end + 1)):
        edges[i] = Edge(i, get_sub_element("tags"), get_sub_element("metrics"))
    return edges


def get_sub_element(sub: str) -> dict:
    element = {}
    for key in model.keys():
        if key != "description" and sub in model[key]:
            element = model[key][sub]
    if "description" in element:
        element.pop("description")
    return element


@tictrack.timed_function()
def get_next_value(edges: dict):
    global last_ts
    # for each edge in the edges list all next values are calculated and saved to the edge_value list
    # this list is then added to the FIFO queue, so each entry of the FIFO queue contains all next values for each edge
    # in the edge list
    edge_values = []
    for edge in edges.values():
        edge_values.append(edge.calculate_next_value())
    if len(edge_values) > 0:
        c_generated_values.inc(len(edge_values))
        if config.ingest_mode == 1:
            ts = last_ts + config.ingest_delta
            ingest_ts_factor = 1 / config.ingest_delta
            last_ts = round(ts * ingest_ts_factor) / ingest_ts_factor
            timestamps = [int(last_ts * 1000)] * len(edge_values)
            current_values_queue.put({"timestamps": timestamps, "batch": edge_values})
        else:
            current_values_queue.put(edge_values)


def log_stat_delta(last_stat_ts_local: float) -> float:
    if time.time() - last_stat_ts_local >= config.stat_delta:
        for key, value in tictrack.tic_toc_delta.items():
            logger.info(f"Average time for {key}: {(sum(value) / len(value))}")
        tictrack.tic_toc_delta = {}
    return time.time()


def stat_delta_thread_function():  # pragma: no cover
    last_stat_ts_local = time.time()
    while not stop_process():
        if time.time() - last_stat_ts_local >= config.stat_delta:
            last_stat_ts_local = log_stat_delta(last_stat_ts_local)
        else:
            # we could calculate the exact time to sleep until next output but this would block the
            # the thread until it happens, this would mean at the end the whole data generator could
            # sleep for another `config.stat_delta` seconds before finishing
            time.sleep(1)


def do_insert(adapter, timestamps, batch):
    try:
        adapter.insert_stmt(timestamps, batch)
        c_inserts_performed_success.inc()
        inserted_values_queue.put_nowait(len(batch))
    except Exception as e:
        # if an exception is thrown while inserting we don't want the whole tsdg to crash
        # as the values have not been inserted we remove them from our runtime_metrics
        # TODO: more sophistic error handling on adapter level
        c_inserts_failed.inc()
        logger.error(e)


def get_insert_values(batch_size: int) -> Tuple[list, list]:
    batch = []
    timestamps = []
    while len(batch) < batch_size:
        try:
            batch_values = current_values_queue.get_nowait()
            batch.extend(batch_values["batch"])
            timestamps.extend(batch_values["timestamps"])
        except Empty:
            # if there are no more values in the queue the insert is done
            # without proper batch_size
            c_values_queue_was_empty.inc()
            break
    return batch, timestamps


def insert_routine():
    name = current_thread().name
    adapter = get_database_adapter()
    try:
        adapter.prepare_database()
    except Exception as ex:
        logger.exception("Failed communicating with database")
        insert_exceptions.put(sys.exc_info())
        return
    data_batch_size = config.id_end - config.id_start + 1
    insert_bsa = BatchSizeAutomator(
        batch_size=config.batch_size,
        active=bool(config.ingest_mode),
        data_batch_size=data_batch_size,
    )

    while not current_values_queue.empty() or not stop_process():
        local_batch_size = insert_bsa.get_next_batch_size()
        if insert_bsa.auto_batch_mode:
            g_batch_size.labels(thread=name).set(local_batch_size)

        batch, timestamps = get_insert_values(local_batch_size)

        if len(batch) > 0:
            start = time.time()
            do_insert(adapter, timestamps, batch)

            if insert_bsa.auto_batch_mode and len(batch) == local_batch_size:
                duration = time.time() - start
                g_insert_time.labels(thread=name).set(duration)
                g_rows_per_second.labels(thread=name).set(len(batch) / duration)
                g_best_batch_size.labels(thread=name).set(
                    insert_bsa.batch_times["best"]["size"]
                )
                g_best_batch_rps.labels(thread=name).set(
                    insert_bsa.batch_times["best"]["batch_per_second"]
                )
                insert_bsa.insert_batch_time(duration)

    adapter.close_connection()


def spawn_insert_threads():  # pragma: no cover
    insert_threads = []
    for i in range(config.num_threads):
        insert_threads.append(Thread(target=insert_routine, name=f"insert_thread_{i}"))
    for thread in insert_threads:
        thread.start()
    for thread in insert_threads:
        thread.join()
    # signal the prometheus thread that insert is finished
    insert_finished_queue.put_nowait(True)


def fast_insert():  # pragma: no cover
    fast_insert_threads = [
        Thread(target=spawn_insert_threads, name="spawn_insert_threads"),
        Thread(target=stat_delta_thread_function, name="stat_delta_thread"),
    ]
    for thread in fast_insert_threads:
        thread.start()
    for thread in fast_insert_threads:
        thread.join()


def consecutive_insert():
    global last_ts
    adapter = get_database_adapter()
    adapter.prepare_database()
    last_insert = config.ingest_ts
    last_stat_ts_local = time.time()
    while not current_values_queue.empty() or not stop_process():
        # we calculate the time delta from the last insert to the current timestamp
        insert_delta = time.time() - last_insert
        # delta needs to be bigger than ingest_delta
        # if delta is smaller than ingest_delta the time difference is waited (as we want an insert
        # every `config.ingest_delta` second
        if insert_delta > config.ingest_delta:
            last_stat_ts_local = log_stat_delta(last_stat_ts_local)
            c_inserted_values.inc(config.id_end - config.id_start + 1)
            try:
                batch = current_values_queue.get_nowait()
                ts = time.time()
                # we want the same timestamp for each value this timestamp should be the same
                # even if the tsdg runs in multiple containers therefore we round the
                # timestamp to match ingest_delta this is done by multiplying
                # by ingest_delta and then dividing the result by ingest_delta
                ingest_ts_factor = 1 / config.ingest_delta
                last_insert = round(ts * ingest_ts_factor) / ingest_ts_factor
                timestamps = [int(last_insert * 1000)] * len(batch)
                do_insert(adapter, timestamps, batch)
            except Empty:
                c_values_queue_was_empty.inc()

        else:
            time.sleep(config.ingest_delta - insert_delta)
    adapter.close_connection()
    # signal the prometheus thread that insert is finished
    insert_finished_queue.put_nowait(True)


def stop_process() -> bool:
    return not stop_queue.empty()


def prometheus_insert_percentage():  # pragma: no cover
    while not inserted_values_queue.empty() or insert_finished_queue.empty():
        try:
            inserted_values = inserted_values_queue.get_nowait()
            c_inserted_values.inc(inserted_values)
            g_insert_percentage.set(
                (
                    c_inserted_values._value.get()
                    / (config.ingest_size * (config.id_end - config.id_start + 1))
                )
                * 100
            )
        except Empty:
            # get_nowait throws Empty exception which might happen if the inserted_values_queue
            # is empty and the insert_finished_queue is as well
            pass


@tictrack.timed_function()
def run_dg():  # pragma: no cover
    logger.info("Starting data generator")

    logger.info("Starting database writer thread")
    if config.ingest_mode == 0:
        adapter_thread = Thread(
            target=consecutive_insert, name="consecutive_insert_thread"
        )
    else:
        adapter_thread = Thread(target=fast_insert, name="fast_insert_thread")
    adapter_thread.start()

    logger.info("Starting metrics collector thread")
    prometheus_insert_percentage_thread = Thread(
        target=prometheus_insert_percentage, name="prometheus_insert_percentage_thread"
    )
    prometheus_insert_percentage_thread.start()

    try:
        edges = create_edges()

        # We are either in endless mode or have a certain amount of values to create.
        # TODO: This should not have an endless loop. For now, stop with CTRL+C.
        logger.info("Starting insert operation")
        while_count = 0
        progress = tqdm(total=config.ingest_size)
        while config.ingest_size == 0 or while_count < config.ingest_size:
            while_count += 1
            get_next_value(edges)
            progress.update()
        progress.close()
    except Exception as e:
        logger.exception(e)
    finally:
        # Once value creation is finished, signal the worker threads to stop.
        logger.info("Shutting down")
        stop_queue.put(True)
        logger.info("Waiting for database writer thread")
        wait_for_thread(adapter_thread, insert_exceptions)

def wait_for_thread(thread: Thread, error_channel: Optional[Queue] = None):
    """
    Wait for thread to finish and, on failure, catch the thread's exception in
    the caller thread.

    - https://stackoverflow.com/a/2830127
    """
    while True:
        if error_channel:
            try:
                exc = error_channel.get(block=False)
            except Empty:
                pass
            else:
                exc_type, exc_obj, exc_trace = exc
                # Re-raise the exception.
                raise exc_obj

        thread.join(0.1)
        if thread.is_alive():
            continue
        else:
            break


def main():  # pragma: no cover
    global last_ts, model, config

    setup_logging()

    # load configuration an set everything up
    config = parse_arguments(config)
    valid_config = config.validate_config()
    if not valid_config:
        logger.error(f"Invalid configuration: {config.invalid_configs}")
        exit(-1)

    logger.info(f"Loading model from {config.model_path}")
    f = open(config.model_path, "r")
    model = json.load(f)

    start_http_server(config.prometheus_port)
    data_batch_size = config.id_end - config.id_start + 1
    last_ts = config.ingest_ts

    # start the tsdg logic
    run_dg()

    # we analyze the runtime of the different function
    run = 0
    for k, v in tictrack.tic_toc.items():
        if k == "run_dg":
            run = sum(v) / len(v)
        logger.info(f"Average time for {k}: {(sum(v) / len(v))}")

    logger.info(f"Records per second: {data_batch_size * config.ingest_size / run}")
    logger.info(
        f"Metrics per second: {data_batch_size * config.ingest_size * len(get_sub_element('metrics').keys()) / run}"
    )


if __name__ == "__main__":  # pragma: no cover
    main()
