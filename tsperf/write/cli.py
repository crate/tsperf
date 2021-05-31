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
from tsperf.util.common import read_configuration
from tsperf.write.config import DataGeneratorConfig

TSPERF_WRITE_README_URL = "https://github.com/crate/tsperf/blob/main/write/README.md"

args_info = {
    "ingest_ts": {
        "help": "The start UNIX timestamp of the generated data. If not provided will be the timestamp when the data "
        "generator has been started.",
        "type": int,
    },
    "ingest_delta": {
        "help": "A positive number to define the interval between timestamps of generated values. "
        "With `ingest_mode = False`, this is the actual time between inserts.",
        "type": float,
    },
    "stat_delta": {
        "help": "Interval in seconds to emit statistic outputs to the log",
        "type": float,
    },
    "db_name": {
        "help": "Name of the database where table will be created. Used with InfluxDB, TimescaleDB, MongoDB, "
        "AWS Timestream, Postgresql, MSSQL. See the documentation for more details: "
        f"{TSPERF_WRITE_README_URL}#db-name",
        "type": str,
    },
    "table_name": {
        "help": "Name of the table where values are stored. Used with CrateDB, Postgresql, MSSQL and TimescaleDB.",
        "type": str,
    },
    "partition": {
        "help": "Is used to partition table by a specified value. Used with CrateDB, Postgresql and TimescaleDB.",
        "choices": [
            "second",
            "minute",
            "hour",
            "day",
            "week",
            "month",
            "quarter",
            "year",
        ],
        "type": str,
    },
}


def parse_arguments(
    config: DataGeneratorConfig,
) -> DataGeneratorConfig:  # pragma: no cover
    return read_configuration(
        config=config,
        args_info=args_info,
        description="Timeseries Database Data Generator - A program to benchmark TSDBs.",
    )
