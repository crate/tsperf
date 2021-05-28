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
from tsperf.tsdg.cli import TSDG_README_URL
from tsperf.util.common import read_configuration

from .config import QueryTimerConfig

args_info = {
    "database": {
        "help": "Value which defines what database will be used: 0-CrateDB, 1-TimescaleDB, 2-InfluxDB, 3-MongoDB, "
        "4-PostgreSQL, 5-Timestream, 6-MSSQL",
        "choices": range(0, 7),
        "type": int,
    },
    "host": {
        "help": "hostname according to the database client requirements. See documentation for further details:"
        f"{TSDG_README_URL}#host",
        "type": str,
    },
    "port": {
        "help": "Defines the port number of the host where the DB is reachable. Integer between 1 to 65535",
        "type": int,
    },
    "username": {
        "help": "username of user used for authentication against the database. Used with CrateDB, TimescaleDB, "
        "MongoDB, Postgresql, MSSQL",
        "type": str,
    },
    "password": {
        "help": "password of user used for authentication against the database. used with CrateDB, TimescaleDB, "
        "MongoDB, Postgresql, MSSQL.",
        "type": str,
    },
    "db_name": {
        "help": "Name of the database where query will be executed. Used with InfluxDB, TimescaleDB, MongoDB, "
        "AWS Timestream, Postgresql, MSSQL. See the documentation for more details: "
        f"{TSDG_README_URL}#db_name",
        "type": str,
    },
    "token": {
        "help": "token gotten from InfluxDB V2: https://v2.docs.influxdata.com/v2.0/security/tokens/view-tokens/",
        "type": str,
    },
    "organization": {
        "help": "org_id gotten from InfluxDB V2: https://v2.docs.influxdata.com/v2.0/organizations/",
        "type": str,
    },
    "aws_access_key_id": {
        "help": "AWS Access Key ID",
        "type": str,
    },
    "aws_secret_access_key": {
        "help": "AWS Secret Access Key",
        "type": str,
    },
    "aws_region_name": {
        "help": "AWS region name",
        "type": str,
    },
    "concurrency": {
        "help": "Defines how many threads run in parallel executing queries.",
        "type": int,
    },
    "iterations": {
        "help": "Defines how many times each thread executes the query.",
        "type": int,
    },
    "quantiles": {
        "help": "Which quantiles should be displayed at the end of the run. Values "
        "are separated by ','",
        "type": str,
    },
    "refresh_rate": {
        "help": "Output refresh interval in seconds.",
        "type": float,
    },
    "query": {
        "help": "The query that will be timed. It must be a valid query in string format for the chosen database",
        "type": str,
    },
}


def parse_arguments(config: QueryTimerConfig) -> QueryTimerConfig:  # pragma: no cover
    return read_configuration(
        config=config,
        args_info=args_info,
        description="Timeseries Database Query Timer - A program to benchmark TSDBs.",
    )