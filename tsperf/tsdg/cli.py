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
from tsperf.tsdg.config import DataGeneratorConfig
from tsperf.util.common import read_configuration

TSDG_README_URL = "https://github.com/crate/tsperf/blob/main/tsdg/README.md"

args_info = {
    "database": {
        "help": "Value which defines what database will be used: 0-CrateDB, 1-TimescaleDB, 2-InfluxDB, 3-MongoDB, "
        "4-PostgreSQL, 5-Timestream, 6-MSSQL",
        "choices": range(0, 7),
        "type": int,
    },
    "id_start": {
        "help": "The Data Generator will create `(id_end + 1) - id_start` edges. Must be smaller or equal to id_end.",
        "type": int,
    },
    "id_end": {
        "help": "The Data Generator will create `(id_end + 1) - id_start` edges. Must be bigger or equal to id_start.",
        "type": int,
    },
    "ingest_mode": {
        "help": "The ingest_mode argument turns on fast insert when set to True or switches to consecutive inserts "
        "when set to False. For more information, please refer to the documentation."
        f"{TSDG_README_URL}#ingest_mode)",
        "choices": [0, 1],
        "type": int,
    },
    "ingest_size": {
        "help": "Number of values per edge to create (positive integer). "
        "If set to 0, an infinite amount of values will be created.",
        "type": int,
    },
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
    "model_path": {
        "help": "A relative or absolute path to a model in the json format (see the data generator documentation for "
        "more details: "
        f"{TSDG_README_URL}#data-generator-models)",
        "type": str,
    },
    "batch_size": {
        "help": "The batch size used when `ingest_mode = True` (positive integer). A value smaller or equal to 0 in "
        "combination with `ingest_mode` turns on auto batch mode using the batch size automator library",
        "type": int,
    },
    "stat_delta": {
        "help": "Interval in seconds to emit statistic outputs to the log",
        "type": float,
    },
    "num_threads": {
        "help": "The number of python-threads used for inserting values (positive integer). Recommendation: 1-4",
        "type": int,
    },
    "prometheus_enabled": {
        "help": "Whether to start the Prometheus HTTP server for exposing metrics",
        "action": "store_true",
    },
    "prometheus_port": {
        "help": "Port for publishing Prometheus metrics (1 to 65535)",
        "type": int,
    },
    "host": {
        "help": "Hostname according to the database client requirements. See documentation for further details:"
        f"{TSDG_README_URL}#host",
        "type": str,
    },
    "username": {
        "help": "User name of user used for authentication against the database. Used with CrateDB, TimescaleDB, "
        "MongoDB, Postgresql, MSSQL",
        "type": str,
    },
    "password": {
        "help": "Password of user used for authentication against the database. used with CrateDB, TimescaleDB, "
        "MongoDB, Postgresql, MSSQL.",
        "type": str,
    },
    "db_name": {
        "help": "Name of the database where table will be created. Used with InfluxDB, TimescaleDB, MongoDB, "
        "AWS Timestream, Postgresql, MSSQL. See the documentation for more details: "
        f"{TSDG_README_URL}#db-name",
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
    "shards": {
        "help": "Set the sharding of the CrateDB table (positive integer). See also: "
        "https://crate.io/docs/crate/reference/en/latest/general/ddl/sharding.html",
        "type": int,
    },
    "replicas": {
        "help": "Set the number of replicas for CrateDB (positive integer). See also: "
        "https://crate.io/docs/crate/reference/en/latest/general/ddl/replication.html",
        "type": int,
    },
    "port": {
        "help": "Defines the port number of the host where the DB is reachable (1 to 65535)",
        "type": int,
    },
    "copy": {
        "help": "Used to toggle between pgcopy and psycopg2 library with TimescaleDB. When set to True pgcopy is used "
        "for inserts",
        "choices": [True, False],
        "type": bool,
    },
    "distributed": {
        "help": "Defines if Timescale is used with distributed hypertables or not. Must only be set to True when "
        "Timescale > v2.0 in distributed mode is run.",
        "choices": [True, False],
        "type": bool,
    },
    "token": {
        "help": "Authentication token for InfluxDB V2: https://v2.docs.influxdata.com/v2.0/security/tokens/view-tokens/",
        "type": str,
    },
    "organization": {
        "help": "Organization ID for InfluxDB V2: https://v2.docs.influxdata.com/v2.0/organizations/",
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
}


def parse_arguments(
    config: DataGeneratorConfig,
) -> DataGeneratorConfig:  # pragma: no cover
    return read_configuration(
        config=config,
        args_info=args_info,
        description="Timeseries Database Data Generator - A program to benchmark TSDBs.",
    )