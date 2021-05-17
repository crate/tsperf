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
import statistics

import numpy
import time
import shutil
from queue import Queue

import urllib3
from blessed import Terminal

from tsqt.cli import parse_arguments
from tsqt.config import QueryTimerConfig
from tsdg.util.tictrack import tic_toc, timed_function
from threading import Thread
from tsdg.adapter.cratedb import CrateDbAdapter
from tsdg.adapter.postgresql import PostgresDbAdapter
from tsdg.adapter.timescaledb import TimescaleDbAdapter
from tsdg.adapter.influxdb import InfluxDbAdapter

# from tsdg.adapter.mongodb import MongoDbAdapter
from tsdg.adapter.mssql import MsSQLDbAdapter
from tsdg.adapter.timestream import TimeStreamAdapter
from tsdg.model.database import AbstractDatabaseAdapter

model = {"value": "none"}
start_time = time.time()
success = 0
failure = 0
queries_done = Queue(1)

config = QueryTimerConfig()

terminal = Terminal()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


def get_database_adapter() -> AbstractDatabaseAdapter:  # noqa
    if config.database == 0:
        adapter = CrateDbAdapter(config.host, config.username, config.password, model)
    elif config.database == 1:
        adapter = TimescaleDbAdapter(
            config.host,
            config.port,
            config.username,
            config.password,
            config.db_name,
            model,
        )
    elif config.database == 2:
        adapter = InfluxDbAdapter(
            config.host, config.token, config.organization, model
        )
    elif config.database == 3:
        raise ValueError(
            "MongoDB queries are not supported (but can be manually added to the script - see "
            "tsqt documentation)"
        )
        # adapter = MongoDbAdapter(config.host, config.username, config.password, config.db_name, model)
    elif config.database == 4:
        adapter = PostgresDbAdapter(
            config.host,
            config.port,
            config.username,
            config.password,
            config.db_name,
            model,
        )
    elif config.database == 5:
        adapter = TimeStreamAdapter(
            config.aws_access_key_id,
            config.aws_secret_access_key,
            config.aws_region_name,
            config.db_name,
            model,
        )
    elif config.database == 6:
        adapter = MsSQLDbAdapter(
            config.host,
            config.username,
            config.password,
            config.db_name,
            model,
            port=config.port,
        )
    else:
        raise ValueError("Unknown database adapter")

    return adapter


def percentage_to_rgb(percentage):
    red = (percentage - 50) / 100.0 if percentage > 50 else 1.0
    green = 1.0 if percentage > 50 else 2 * percentage / 100.0
    blue = 0.0
    return red * 255, green * 255, blue * 255


@timed_function()
def print_progressbar(
    iteration, total, prefix="", suffix="", decimals=1, length=100, fill="█"
):  # pragma: no cover
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
    duration = time.time() - start_time
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    r, g, b = percentage_to_rgb(float(percent))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + "-" * (length - filled_length)

    if "execute_query" in tic_toc:
        values = tic_toc["execute_query"]
        print(
            terminal.move_y(3)
            + f"{prefix} |{terminal.color_rgb(r, g, b)}{bar}{terminal.normal}| {percent}% "
            f"{suffix} {round(duration, 2)}s"
        )
        print(
            f"time left: {round(((duration / float(percent)) * 100) - duration, 2)}s                                "
        )
        if len(values) > 1:
            pass
            print(
                terminal.move_y(6)
                + f"rate   : {round((1 / numpy.mean(values)) * config.concurrency, 3)}qs/s       "
            )
            print(f"mean   : {round(numpy.mean(values) * 1000, 3)}ms       ")
            print(f"stdev  : {round(numpy.std(values) * 1000, 3)}ms      ")
            print(f"min    : {round(min(values) * 1000, 3)}ms       ")
            print(f"max    : {round(max(values) * 1000, 3)}ms       ")
            print(f"success: {terminal.green}{success}{terminal.normal}      ")
            print(f"failure: {terminal.red}{failure}{terminal.normal}        ")


def start_query_run():
    global success, failure
    adapter = get_database_adapter()
    for x in range(0, config.iterations):
        try:
            adapter.execute_query(config.query)
            success += 1
        except Exception:
            failure += 1


def print_progress_thread():  # pragma: no cover
    while queries_done.empty():
        time.sleep(config.refresh_rate)
        total_queries = success + failure
        terminal_size = shutil.get_terminal_size()
        print_progressbar(
            total_queries,
            config.concurrency * config.iterations,
            prefix="Progress:",
            suffix="Complete",
            length=(terminal_size.columns - 40),
        )


def run_qt():  # pragma: no cover
    global start_time
    start_time = time.time()
    progress_thread = Thread(target=print_progress_thread)
    progress_thread.start()
    threads = []
    for y in range(0, config.concurrency):
        thread = Thread(target=start_query_run)
        threads.append(thread)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    queries_done.put_nowait(True)
    progress_thread.join()


def main():  # pragma: no cover
    global config
    with terminal.hidden_cursor():
        # load configuration an set everything up
        config = parse_arguments(config)
        valid_config = config.validate_config()
        if not valid_config:
            logging.error(f"invalid configuration: {config.invalid_configs}")
            exit(-1)

        print(f"concurrency: {config.concurrency}\niterations : {config.iterations}")
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
            print("")
            for i in range(0, len(qus)):
                if str(i + 1) in config.quantiles:
                    print(f"p{i+1}  : {round(qus[i]*1000, 3)}ms")


if __name__ == "__main__":  # pragma: no cover
    main()
