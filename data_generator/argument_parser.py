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

import argparse
from data_generator.config import DataGeneratorConfig

args_info = {
    "database": {
        "help": "Value which defines what database will be used: 0-CrateDB, 1-TimescaleDB, 2-InfluxDB, 3-MongoDB, "
        "4-PostgreSQL, 5-Timestream, 6-MSSQL",
        "choices": range(0, 7),
        "type": int,
    },
    "id_start": {
        "help": "The Data Generator will create `(id_end + 1) - id_start` edges. Must be smaller or equal to id_end.",
        "choices": ["1, 2, 3, ..."],
        "type": int,
    },
    "id_end": {
        "help": "The Data Generator will create `(id_end + 1) - id_start` edges. Must be bigger or equal to id_start.",
        "choices": ["1, 2, 3, ..."],
        "type": int,
    },
    "ingest_mode": {
        "help": "The ingest_mode argument turns on fast insert when set to True or switches to consecutive inserts "
        "when set to False. For more information, please refer to the documentation."
        "https://github.com/crate/tsdg/blob/main/DATA_GENERATOR.md#ingest_mode)",
        "choices": [True, False],
        "type": bool,
    },
    "ingest_size": {
        "help": "This argument defines how many values per edge will be created. If set to 0 an endless amount of "
        "values will be created.",
        "choices": ["0, 1, 2, 3, ..."],
        "type": int,
    },
    "ingest_ts": {
        "help": "The starting timestamp of the generated data. If not provided will be the timestamp when the Data "
        "Generator has been started.",
        "choices": ["A valid UNIX timestamp"],
        "type": int,
    },
    "ingest_delta": {
        "help": "This values defines the interval between timestamps of generated values. With `ingest_mode = False` "
        "This is the actual time between inserts.",
        "choices": ["Any positive number"],
        "type": float,
    },
    "model_path": {
        "help": "A relative or absolute path to a model in the json format (see the data generator documentation for "
        "more details: "
        "https://github.com/crate/tsdg/blob/main/DATA_GENERATOR.md#data-generator-models)",
        "choices": ["Absolute or relative file path"],
        "type": str,
    },
    "batch_size": {
        "help": "The batch size used when ingest_mode is set to True. A value smaller or equal to 0 in combination "
        "with ingest_mode turns on auto batch mode using the batch-size-automator library: "
        "https://pypi.org/project/batch-size-automator/",
        "choices": ["Any integer number"],
        "type": int,
    },
    "stat_delta": {
        "help": "Time in seconds that is waited between statistic outputs to the log",
        "choices": ["number > 0"],
        "type": float,
    },
    "num_threads": {
        "help": "The number of python-threads used for inserting values",
        "choices": ["integer > 0 but 1-4 advised"],
        "type": int,
    },
    "prometheus_port": {
        "help": "The port that is used to publish prometheus metrics",
        "choices": ["1 to 65535"],
        "type": int,
    },
    "host": {
        "help": "hostname according to the database client requirements. See documentation for further details:"
        "https://github.com/crate/tsdg/blob/main/DATA_GENERATOR.md#host",
        "choices": [],
        "type": str,
    },
    "username": {
        "help": "username of user used for authentication against the database. Used with CrateDB, TimescaleDB, "
        "MongoDB, Postgresql, MSSQL",
        "choices": [],
        "type": str,
    },
    "password": {
        "help": "password of user used for authentication against the database. used with CrateDB, TimescaleDB, "
        "MongoDB, Postgresql, MSSQL.",
        "choices": [],
        "type": str,
    },
    "db_name": {
        "help": "Name of the database where table will be created. Used with InfluxDB, TimescaleDB, MongoDB, "
        "AWS Timestream, Postgresql, MSSQL. See the documentation for more details: "
        "https://github.com/crate/tsdg/blob/main/DATA_GENERATOR.md#db-name",
        "choices": [],
        "type": str,
    },
    "table_name": {
        "help": "Name of the table where values are stored. Used with CrateDB, Postgresql, MSSQL and TimescaleDB.",
        "choices": [],
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
        "help": "Is used to set the sharding of the CrateDB table: "
        "https://crate.io/docs/crate/reference/en/latest/general/ddl/sharding.html",
        "choices": ["x > 0"],
        "type": int,
    },
    "replicas": {
        "help": "Is used to set the number of replicas for CrateDB: "
        "https://crate.io/docs/crate/reference/en/latest/general/ddl/replication.html",
        "choices": ["x >= 0"],
        "type": int,
    },
    "port": {
        "help": "Defines the port number of the host where the DB is reachable.",
        "choices": ["1 to 65535"],
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
        "help": "token gotten from InfluxDB V2: https://v2.docs.influxdata.com/v2.0/security/tokens/view-tokens/",
        "choices": [],
        "type": str,
    },
    "organization": {
        "help": "org_id gotten from InfluxDB V2: https://v2.docs.influxdata.com/v2.0/organizations/",
        "choices": [],
        "type": str,
    },
    "aws_access_key_id": {"help": "AWS Access Key ID", "choices": [], "type": str},
    "aws_secret_access_key": {
        "help": "AWS Secret Access Key",
        "choices": [],
        "type": str,
    },
    "aws_region_name": {"help": "AWS region name", "choices": [], "type": str},
}


def parse_arguments(
    config: DataGeneratorConfig,
) -> DataGeneratorConfig:  # pragma: no cover
    parser = argparse.ArgumentParser(
        description="Timeseries Database Data Generator - A program to benchmark TSDBs.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    for element in vars(config):
        if element in args_info:
            parser.add_argument(
                f"--{element}",
                type=args_info[element]["type"],
                default=getattr(config, element),
                help=args_info[element]["help"],
                choices=args_info[element]["choices"],
            )

    arguments = parser.parse_args()
    config.load_args(vars(arguments))
    return config
