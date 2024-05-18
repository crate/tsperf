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
import logging
import time
from queue import Empty, Queue
from threading import Thread, current_thread
from typing import Optional, Tuple

from prometheus_client import start_http_server
from tqdm import tqdm

from tsperf.engine import TsPerfEngine, load_schema
from tsperf.model.interface import AbstractDatabaseInterface
from tsperf.util import tictrack
from tsperf.util.batch_size_automator import BatchSizeAutomator
from tsperf.write.config import DataGeneratorConfig
from tsperf.write.model import IngestMode
from tsperf.write.model.channel import Channel
from tsperf.write.model.metrics import (
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

logger = logging.getLogger(__name__)


# Global variables shared across threads
# TODO: Get rid of global variables.
engine: TsPerfEngine = None
config: DataGeneratorConfig = None
schema = {}
last_ts = 0
current_values_queue = Queue(10000)
inserted_values_queue = Queue(10000)
stop_queue = Queue(1)
insert_finished_queue = Queue(1)
insert_exceptions = Queue()


def get_database_adapter_old() -> AbstractDatabaseInterface:  # pragma: no cover
    """
    if config.database == 0:  # crate
        adapter = CrateDbAdapter(config=config, schema=schema)
        # adapter = AdapterManager.create(
        #    interface=DatabaseInterfaceType.CrateDB, config=config, schema=schema
        # )
    elif config.database == 1:  # timescale
        adapter = TimescaleDbAdapter(
            config.address,
            config.port,
            config.username,
            config.password,
            config.database,
            schema,
            config.table,
            config.partition,
            config.copy,
            config.distributed,
        )
    elif config.database == 2:  # influx
        adapter = InfluxDbAdapter(
            config.address, config.token, config.organization, schema, config.database
        )
    elif config.database == 3:  # mongo
        adapter = MongoDbAdapter(
            config.address, config.username, config.password, config.database, schema
        )
    elif config.database == 4:  # postgres
        adapter = PostgreSQLAdapter(
            config.address,
            config.port,
            config.username,
            config.password,
            config.database,
            schema,
            config.table,
            config.partition,
        )
    elif config.database == 5:  # timestream
        adapter = AmazonTimestreamAdapter(
            config.aws_access_key_id,
            config.aws_secret_access_key,
            config.aws_region_name,
            config.database,
            schema,
        )
    elif config.database == 6:  # ms_sql
        adapter = MsSQLDbAdapter(
            config.address,
            config.username,
            config.password,
            config.database,
            schema,
            port=config.port,
            table=config.table,
        )
    else:
        adapter = None
    return adapter
    """


@tictrack.timed_function()
def create_channels() -> dict:
    """
    Create channel objects in the given range [id_start, id_end]
    """
    id_start = config.id_start
    id_end = config.id_end + 1
    count = id_end - id_start
    logger.info(f"Creating {count} channels [{id_start}, {id_end}]")
    channels = {}
    for i in tqdm(range(config.id_start, config.id_end + 1)):
        channels[i] = Channel(i, get_sub_element("tags"), get_sub_element("fields"))
    return channels


def get_sub_element(sub: str) -> dict:
    element = {}
    for key in schema.keys():
        if key != "description" and sub in schema[key]:
            element = schema[key][sub]
    if "description" in element:
        element.pop("description")
    return element


@tictrack.timed_function()
def get_next_value(channels: dict):
    global last_ts
    # for each channel in the channels list all next values are calculated and
    # saved to the `channel_values` list. This list is then added to the FIFO
    # queue, so each entry of the FIFO queue contains all next values for each
    # channel in the channel list.
    channel_values = []
    for channel in channels.values():
        channel_values.append(channel.calculate_next_value())
    if len(channel_values) > 0:
        c_generated_values.inc(len(channel_values))
        if config.ingest_mode == IngestMode.FAST:
            ts = last_ts + config.timestamp_delta
            timestamp_factor = 1 / config.timestamp_delta
            last_ts = round(ts * timestamp_factor) / timestamp_factor
            timestamps = [int(last_ts * 1000)] * len(channel_values)
            current_values_queue.put({"timestamps": timestamps, "batch": channel_values})
        else:
            current_values_queue.put(channel_values)


def statistics_logger(last_stat_ts_local: float) -> float:
    if time.time() - last_stat_ts_local >= config.statistics_interval:
        for key, value in tictrack.tic_toc_delta.items():
            logger.info(f"Average time for {key}: {(sum(value) / len(value))}")
        tictrack.tic_toc_delta = {}
    return time.time()


def statistics_thread():
    logger.info("Starting statistics thread")
    last_stat_ts_local = time.time()
    while not stop_process():
        if time.time() - last_stat_ts_local >= config.statistics_interval:
            last_stat_ts_local = statistics_logger(last_stat_ts_local)
        else:
            # we could calculate the exact time to sleep until next output but this would block the
            # the thread until it happens, this would mean at the end the whole data generator could
            # sleep for another `config.statistics_interval` seconds before finishing
            time.sleep(1)


def do_insert(adapter, timestamps, batch):
    try:
        adapter.insert_stmt(timestamps, batch)
        c_inserts_performed_success.inc()
        inserted_values_queue.put_nowait(len(batch))
    except Exception as e:
        # if an exception is thrown while inserting we don't want the whole write to crash
        # as the values have not been inserted we remove them from our runtime metrics
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


def probe_insert():
    logger.info("Probing insert")
    try:
        engine.create_adapter().prepare_database()
        return True
    except Exception:
        logger.exception("Failure communicating with or preparing database")
        return False


def insert_routine():
    name = current_thread().name
    data_batch_size = config.id_end - config.id_start + 1
    insert_bsa = BatchSizeAutomator(
        batch_size=config.batch_size,
        active=bool(config.ingest_mode),
        data_batch_size=data_batch_size,
    )

    adapter = engine.create_adapter()
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
                g_best_batch_size.labels(thread=name).set(insert_bsa.batch_times["best"]["size"])
                g_best_batch_rps.labels(thread=name).set(insert_bsa.batch_times["best"]["batch_per_second"])
                insert_bsa.insert_batch_time(duration)

    adapter.close_connection()

    return True


def spawn_insert_threads():
    logger.info(f"Starting {config.concurrency} database writer thread(s)")
    insert_threads = []
    for i in range(config.concurrency):
        insert_threads.append(Thread(target=insert_routine, name=f"InsertThread-{i}"))
    for thread in insert_threads:
        thread.start()
    for thread in insert_threads:
        thread.join()

    # Signal the Prometheus thread that insert is finished.
    insert_finished_queue.put_nowait(True)


def fast_insert():
    fast_insert_threads = [
        Thread(target=spawn_insert_threads, name="InsertThreadSpawner"),
        Thread(target=statistics_thread, name="StatisticsThread"),
    ]
    for thread in fast_insert_threads:
        thread.start()
    for thread in fast_insert_threads:
        thread.join()


def consecutive_insert():
    global last_ts
    logger.info("Starting single database writer thread")
    adapter = engine.create_adapter()

    adapter.prepare_database()
    last_insert = config.timestamp_start
    last_stat_ts_local = time.time()
    while not current_values_queue.empty() or not stop_process():
        # we calculate the time delta from the last insert to the current timestamp
        insert_delta = time.time() - last_insert
        # delta needs to be bigger than timestamp_delta
        # if delta is smaller than timestamp_delta the time difference is waited (as we want an insert
        # every `config.timestamp_delta` second
        if insert_delta > config.timestamp_delta:
            last_stat_ts_local = statistics_logger(last_stat_ts_local)
            c_inserted_values.inc(config.id_end - config.id_start + 1)
            try:
                batch = current_values_queue.get_nowait()
                ts = time.time()
                # we want the same timestamp for each value this timestamp should be the same
                # even if the write runs in multiple containers therefore we round the
                # timestamp to match timestamp_delta this is done by multiplying
                # by timestamp_delta and then dividing the result by timestamp_delta
                timestamp_factor = 1 / config.timestamp_delta
                last_insert = round(ts * timestamp_factor) / timestamp_factor
                timestamps = [int(last_insert * 1000)] * len(batch)
                do_insert(adapter, timestamps, batch)
            except Empty:
                c_values_queue_was_empty.inc()

        else:
            time.sleep(config.timestamp_delta - insert_delta)
    adapter.close_connection()

    # Signal the Prometheus thread that insert is finished.
    insert_finished_queue.put_nowait(True)


def stop_process() -> bool:
    return not stop_queue.empty()


def prometheus_insert_percentage():
    while not inserted_values_queue.empty() or insert_finished_queue.empty():
        try:
            inserted_values = inserted_values_queue.get_nowait()
            c_inserted_values.inc(inserted_values)
            g_insert_percentage.set(
                (c_inserted_values._value.get() / (config.ingest_size * (config.id_end - config.id_start + 1))) * 100
            )
        except Empty:
            # get_nowait throws Empty exception which might happen if the inserted_values_queue
            # is empty and the insert_finished_queue is as well
            pass


@tictrack.timed_function()
def run_dg():
    logger.info(f"Starting data generator with config »{config}« and schema »{config.schema}«")

    logger.info("Starting database writer subsystem")
    if config.ingest_mode == IngestMode.CONSECUTIVE:
        logger.info("Using insert mode »consecutive«")
        adapter_thread = Thread(target=consecutive_insert, name="ConsecutiveInsert")
    else:
        logger.info("Using insert mode »fast«")
        adapter_thread = Thread(target=fast_insert, name="ParallelInsert")
    adapter_thread.start()

    logger.info("Starting metrics collector thread")
    prometheus_insert_percentage_thread = Thread(target=prometheus_insert_percentage, name="PrometheusThread")
    prometheus_insert_percentage_thread.start()

    try:
        channels = create_channels()

        # We are either in endless mode or have a certain amount of values to create.
        # TODO: This should not have an endless loop. For now, stop with CTRL+C.
        logger.info(f"Starting insert operation with ingest size {config.ingest_size}")
        while_count = 0
        progress = tqdm(total=config.ingest_size)
        while config.ingest_size == 0 or while_count < config.ingest_size:
            while_count += 1
            get_next_value(channels)
            progress.update()
        progress.close()
    except Exception as e:
        logger.exception(e)
    finally:
        # Once value creation is finished, signal the worker threads to stop.
        logger.info("Shutting down")
        stop_queue.put(True)
        logger.info("Waiting for database writer thread(s)")
        wait_for_thread(adapter_thread, insert_exceptions)

        if config.prometheus_enable:
            logger.info("Waiting for metrics collector thread")
            prometheus_insert_percentage_thread.join()


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
        break


def start(configuration: DataGeneratorConfig):
    # TODO: Get rid of global variables.
    global engine, config
    global schema, last_ts

    # TODO: Move schema loading to engine.
    schema = load_schema(configuration.schema)
    engine = TsPerfEngine(config=configuration, schema=schema)
    engine.bootstrap()

    # TODO: Get rid of global variables.
    config = engine.config

    if not probe_insert():
        raise Exception(f"Failure communicating with or preparing database at {config.address}")

    if config.prometheus_enable:
        logger.info(f"Starting Prometheus HTTP server on {config.prometheus_host}:{config.prometheus_port}")
        start_http_server(config.prometheus_port, addr=config.prometheus_host)

    data_batch_size = config.id_end - config.id_start + 1
    last_ts = config.timestamp_start

    # start the write logic
    run_dg()

    # we analyze the runtime of the different function
    run = 0
    for k, v in tictrack.tic_toc.items():
        if k == "run_dg":
            run = sum(v) / len(v)
        logger.info(f"Average time for {k}: {(sum(v) / len(v))}")

    logger.info(
        f"Values per second: {data_batch_size * config.ingest_size * len(get_sub_element('fields').keys()) / run}"
    )
    logger.info(f"Records per second: {data_batch_size * config.ingest_size / run}")
