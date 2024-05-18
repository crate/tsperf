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
import io
import logging
import shutil
import statistics
import sys
import time
from contextlib import redirect_stdout
from queue import Queue
from threading import Thread

import numpy
from blessed import Terminal

from tsperf.engine import TsPerfEngine, load_schema
from tsperf.model.interface import AbstractDatabaseInterface
from tsperf.read.config import QueryTimerConfig
from tsperf.util.tictrack import tic_toc, timed_function

terminal = Terminal()
logger = logging.getLogger(__name__)


# TODO: Get rid of global variables.
engine: TsPerfEngine = None
config: QueryTimerConfig = None
schema = {"value": "none"}
start_time = time.time()
success = 0
failure = 0
queries_done = Queue(1)


def get_database_adapter_old() -> AbstractDatabaseInterface:  # pragma: no cover
    """
    if config.database == 0:
        adapter = CrateDbAdapter(config=config, schema=schema)
    elif config.database == 1:
        adapter = TimescaleDbAdapter(
            config.address,
            config.port,
            config.username,
            config.password,
            config.database,
            schema,
        )
    elif config.database == 2:
        adapter = InfluxDbAdapter(
            config.address, config.token, config.organization, schema
        )
    elif config.database == 3:
        raise ValueError(
            "MongoDB queries are not supported (but can be manually added to the script - see "
            "read documentation)"
        )
        # adapter = MongoDbAdapter(config.address, config.username, config.password, config.database, schema)
    elif config.database == 4:
        adapter = PostgreSQLAdapter(
            config.address,
            config.port,
            config.username,
            config.password,
            config.database,
            schema,
        )
    elif config.database == 5:
        adapter = AmazonTimestreamAdapter(
            config.aws_access_key_id,
            config.aws_secret_access_key,
            config.aws_region_name,
            config.database,
            schema,
        )
    elif config.database == 6:
        adapter = MsSQLDbAdapter(
            config.address,
            config.username,
            config.password,
            config.database,
            schema,
            port=config.port,
        )
    else:
        raise ValueError("Unknown database adapter")

    return adapter
    """


def percentage_to_rgb(percentage):
    red = (percentage - 50) / 100.0 if percentage > 50 else 1.0
    green = 1.0 if percentage > 50 else 2 * percentage / 100.0
    blue = 0.0
    return red * 255, green * 255, blue * 255


@timed_function()
def print_progressbar(iteration, total, prefix="", suffix="", decimals=1, length=100, fill="█"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """

    screen_position_y = 30

    duration = time.time() - start_time
    percentage = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    # Prevent "division by zero" errors.
    percent = max(float(percentage), 0.1)

    r, g, b = percentage_to_rgb(percent)
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + "-" * (length - filled_length)

    if "execute_query" in tic_toc:
        values = tic_toc["execute_query"]

        f = io.StringIO()
        # ruff: noqa: T201
        with redirect_stdout(f):
            print(
                terminal.move_y(screen_position_y)
                + f"{prefix} |{terminal.color_rgb(r, g, b)}{bar}{terminal.normal}| {percentage}% "
                f"{suffix} {round(duration, 2)}s"
            )
            print(f"time left: {round(((duration / percent) * 100) - duration, 2)}s                              ")
            if len(values) > 1:
                print(
                    terminal.move_y(screen_position_y + 3)
                    + f"rate   : {round((1 / numpy.mean(values)) * config.concurrency, 3)}qps       "
                )
                print(f"mean   : {round(numpy.mean(values) * 1000, 3)}ms       ")
                print(f"stdev  : {round(numpy.std(values) * 1000, 3)}ms      ")
                print(f"min    : {round(min(values) * 1000, 3)}ms       ")
                print(f"max    : {round(max(values) * 1000, 3)}ms       ")
                print(f"success: {terminal.green}{success}{terminal.normal}      ")
                print(f"failure: {terminal.red}{failure}{terminal.normal}        ")
        report = f.getvalue()
        sys.stderr.write(f"\n{report}\n")
        sys.stderr.flush()


def probe_query():
    try:
        engine.create_adapter().run_query(config.query)
        return True
    except Exception:
        logger.exception(f"Failure executing query '{config.query}'")
        return False


def start_query_run():
    global success, failure
    adapter = engine.create_adapter()
    for _ in range(0, config.iterations):
        try:
            adapter.execute_query(config.query)
            success += 1
        except Exception:
            failure += 1
            logger.exception(f"Failure executing query '{config.query}'")


def print_progress_thread():
    while queries_done.empty():
        time.sleep(config.refresh_interval)
        total_queries = success + failure
        terminal_size = shutil.get_terminal_size()
        print_progressbar(
            total_queries,
            config.concurrency * config.iterations,
            prefix="Progress:",
            suffix="Complete",
            length=(terminal_size.columns - 40),
        )


def run_qt():
    logger.info(f"Starting query timer with {config} and schema {config.schema}")
    global start_time
    start_time = time.time()

    logger.info("Starting progress monitor thread")
    progress_thread = Thread(target=print_progress_thread, name="ProgressMonitor")
    progress_thread.start()

    logger.info("Starting worker threads")
    threads = []
    logger.info(f"Invoking query »{config.query}«")
    for i in range(0, config.concurrency):
        thread = Thread(target=start_query_run, name=f"WorkerThread-{i}")
        threads.append(thread)
    for thread in threads:
        thread.start()

    logger.info("Waiting for worker threads")
    for thread in threads:
        thread.join()
    queries_done.put_nowait(True)

    logger.info("Waiting for progress monitor thread")
    progress_thread.join()


def start(configuration: QueryTimerConfig):
    global engine, schema, config

    # TODO: Move schema loading to engine.
    schema = load_schema(configuration.schema)
    engine = TsPerfEngine(config=configuration, schema=schema)
    engine.bootstrap()
    config = engine.config

    logger.info(f"Probing query »{config.query}«")
    if not probe_query():
        raise RuntimeError("Error probing database. Not starting machinery.")

    logger.info(f"Running {config.iterations} iterations with concurrency {config.concurrency}")

    with terminal.hidden_cursor():
        terminal_size = shutil.get_terminal_size()
        print_progressbar(
            0,
            config.concurrency * config.iterations,
            prefix="Progress:",
            suffix="Complete",
            length=(terminal_size.columns - 40),
        )

        run_qt()

        if "execute_query" in tic_toc:
            values = tic_toc["execute_query"]
            qus = statistics.quantiles(values, n=100, method="inclusive")
            f = io.StringIO()
            with redirect_stdout(f):
                for i in range(0, len(qus)):
                    if str(i + 1) in config.quantiles:
                        print(f"p{i+1}  : {round(qus[i]*1000, 3)}ms")
            report = f.getvalue()
            logger.info("\n")
            logger.info(f"Statistics:\n{report}")
