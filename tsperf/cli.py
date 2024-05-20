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
import glob
import json
import logging
import sys
from pathlib import Path

import click
import cloup
from blessed import Terminal

import tsperf.read.core
import tsperf.write.core
from tsperf.model.interface import DatabaseInterfaceType
from tsperf.read.config import QueryTimerConfig
from tsperf.util.common import setup_logging
from tsperf.write.config import DataGeneratorConfig
from tsperf.write.model import IngestMode

logger = logging.getLogger(__name__)

TSPERF_README_URL = "https://github.com/crate/tsperf"


general_options = cloup.option_group(
    "General options",
    cloup.option(
        "--schema",
        envvar="SCHEMA",
        type=str,
        help="A reference to a schema in JSON format. It can either be the name of a Python resource in "
        "full-qualified dotted `pkg_resources`-compatible notation, or an absolute or relative path.",
    ),
)


adapter_options = cloup.option_group(
    "Adapter",
    click.option(
        "--adapter",
        envvar="ADAPTER",
        type=click.Choice(
            [item.name.lower() for item in DatabaseInterfaceType],
            case_sensitive=False,
        ),
        required=True,
        help="Which database adapter to use",
    ),
    click.option(
        "--address",
        envvar="ADDRESS",
        type=click.STRING,
        help="Database address (DSN URI, hostname:port) according to the database client requirements. "
        "When left empty, the default will be to connect to the respective database on localhost.",
    ),
    click.option(
        "--database",
        envvar="DATABASE",
        type=click.STRING,
        help="Name of the database. Applies to specific databases only.",
    ),
    click.option(
        "--table",
        envvar="TABLE",
        type=click.STRING,
        help="Name of the table. Applies to specific databases only.",
    ),
)

authentication_options = cloup.option_group(
    "Authentication options",
    click.option(
        "--username",
        envvar="USERNAME",
        type=click.STRING,
        help="User name for authentication against the database",
    ),
    click.option(
        "--password",
        envvar="PASSWORD",
        type=click.STRING,
        help="Password for authentication against the database",
    ),
    click.option(
        "--influxdb-organization",
        envvar="INFLUXDB_ORGANIZATION",
        type=click.STRING,
        help="Organization name for InfluxDB V2. " "See also: https://v2.docs.influxdata.com/v2.0/organizations/.",
    ),
    click.option(
        "--influxdb-token",
        envvar="INFLUXDB_TOKEN",
        type=click.STRING,
        help="Authentication token for InfluxDB V2. "
        "See also https://v2.docs.influxdata.com/v2.0/security/tokens/view-tokens/.",
    ),
    click.option(
        "--aws-access-key-id",
        envvar="AWS_ACCESS_KEY_ID",
        type=click.STRING,
        help="AWS Access Key ID",
    ),
    click.option(
        "--aws-secret-access-key",
        envvar="AWS_SECRET_ACCESS_KEY",
        type=click.STRING,
        help="AWS Secret Access Key",
    ),
    click.option(
        "--aws-region-name",
        envvar="AWS_REGION_NAME",
        type=click.STRING,
        help="AWS region name",
    ),
)


performance_options = cloup.option_group(
    "Performance options",
    click.option(
        "--concurrency",
        envvar="CONCURRENCY",
        type=click.INT,
        help="Number of worker threads for executing queries in parallel. Recommended: 1-4",
    ),
    click.option(
        "--partition",
        envvar="PARTITION",
        type=click.Choice(
            [
                "second",
                "minute",
                "hour",
                "day",
                "week",
                "month",
                "quarter",
                "year",
            ],
            case_sensitive=False,
        ),
        default="week",
        help="Is used to partition table by a specified value. Used with CrateDB, PostgreSQL and TimescaleDB.",
    ),
    click.option(
        "--shards",
        envvar="SHARDS",
        type=click.INT,
        default=4,
        help="Sharding of the CrateDB table",
    ),
    click.option(
        "--replicas",
        envvar="REPLICAS",
        type=click.INT,
        default=1,
        help="Number of replicas for the CrateDB table",
    ),
    cloup.option(
        "--timescaledb-distributed",
        envvar="TIMESCALEDB_DISTRIBUTED",
        type=click.BOOL,
        is_flag=True,
        default=False,
        help="Use distributed hypertables with TimescaleDB",
    ),
    cloup.option(
        "--timescaledb-pgcopy",
        envvar="TIMESCALEDB_PGCOPY",
        type=click.BOOL,
        is_flag=True,
        default=False,
        help="Use pgcopy with TimescaleDB",
    ),
)


write_options = cloup.option_group(
    "Write options",
    cloup.option(
        "--schema",
        envvar="SCHEMA",
        type=str,
        required=True,
        help="A reference to a schema in JSON format. It can either be the name of a Python resource in "
        "full-qualified dotted `pkg_resources`-compatible notation, or an absolute or relative path.",
    ),
    cloup.option(
        "--id-start",
        envvar="ID_START",
        type=click.INT,
        default=1,
        help="The Data Generator will create `(id_end + 1) - id_start` channels. Must be smaller or equal to id_end.",
    ),
    cloup.option(
        "--id-end",
        envvar="ID_END",
        type=click.INT,
        default=500,
        help="The Data Generator will create `(id_end + 1) - id_start` channels. Must be bigger or equal to id_start.",
    ),
    cloup.option(
        "--timestamp-start",
        envvar="TIMESTAMP_START",
        type=click.FLOAT,
        help="The start Unix timestamp of the generated data. If not provided, it will use the current time.",
    ),
    cloup.option(
        "--timestamp-delta",
        envvar="TIMESTAMP_DELTA",
        type=click.FLOAT,
        default=0.5,
        help="A positive number to define the interval between timestamps of generated values. "
        "With `ingest_mode = False`, this is the actual time between inserts.",
    ),
    cloup.option(
        "--ingest-mode",
        envvar="INGEST_MODE",
        type=click.Choice(
            [item.name.lower() for item in IngestMode],
            case_sensitive=False,
        ),
        default="fast",
        help="Which ingest mode to use. "
        "consecutive: For each record, an individual SQL statement will be submitted. "
        "fast: Many records will be submitted in batches using a single SQL statement. "
        "Default: fast",
    ),
    cloup.option(
        "--ingest-size",
        envvar="INGEST_SIZE",
        type=click.INT,
        default=1000,
        help="Number of values per object to create. If set to 0, an infinite amount of values will be created.",
    ),
    cloup.option(
        "--batch-size",
        envvar="BATCH_SIZE",
        type=click.INT,
        default=-1,
        help="The batch size used when `ingest_mode = True`. A value smaller or equal to 0 in combination with "
        "`ingest_mode` turns on auto batch mode using the batch size automator library.",
    ),
    cloup.option(
        "--prometheus-enable",
        envvar="PROMETHEUS_ENABLE",
        type=click.BOOL,
        is_flag=True,
        default=False,
        help="Whether to start the Prometheus HTTP server for exposing metrics",
    ),
    cloup.option(
        "--prometheus-listen",
        envvar="PROMETHEUS_LISTEN",
        type=click.STRING,
        default="localhost:8000",
        help="Prometheus HTTP server listen address. Use 0.0.0.0:8000 to listen on all interfaces.",
    ),
)

read_options = cloup.option_group(
    "Read options",
    cloup.option(
        "--query",
        envvar="QUERY",
        type=click.STRING,
        default=None,
        help="The query that will be timed. It must be a valid query in string format for the chosen database",
    ),
    cloup.option(
        "--iterations",
        envvar="ITERATIONS",
        type=click.INT,
        default=None,
        help="How many times each thread executes the query",
    ),
    click.option(
        "--quantiles",
        envvar="QUANTILES",
        type=click.STRING,
        default="50,60,75,90,99",
        help="Which quantiles should be displayed at the end of the run. Values are separated by ','",
    ),
)


misc_options = cloup.option_group(
    "Miscellaneous options",
    click.option(
        "--debug",
        envvar="DEBUG",
        is_flag=True,
    ),
)


@cloup.group("tsperf", help=f"See documentation for further details: {TSPERF_README_URL}")
@click.version_option()
def main():
    setup_logging()


@main.command("write")
@general_options
@adapter_options
@authentication_options
@performance_options
@write_options
@click.option(
    "--statistics-interval",
    envvar="STATISTICS_INTERVAL",
    type=click.FLOAT,
    default=30,
    help="Interval in seconds to emit statistic outputs to the log",
)
@misc_options
def write(**kwargs):
    # Run workload.
    adapter = kwargs["adapter"]
    logger.info(f"Invoking write workload on time-series database »{adapter}«")
    config = DataGeneratorConfig.create(**kwargs)
    tsperf.write.core.start(config)


@main.command("read")
@general_options
@adapter_options
@authentication_options
@performance_options
@read_options
@click.option(
    "--refresh-interval",
    envvar="REFRESH_INTERVAL",
    type=click.FLOAT,
    default=0.1,
    help="Output refresh interval in seconds",
)
@misc_options
def read(**kwargs):
    # Clear screen.
    terminal = Terminal()
    sys.stdout.write(terminal.home + terminal.clear + "\n")

    # Run workload.
    adapter = kwargs["adapter"]
    logger.info(f"Invoking read workload on time-series database »{adapter}«")
    config = QueryTimerConfig.create(**kwargs)
    tsperf.read.core.start(config)


@main.command("schema")
@click.option(
    "--list",
    "as_list",
    is_flag=True,
    default=False,
    help="List all built-in schemas",
)
def schema(as_list: bool):
    if as_list:
        module_path = Path(__file__).parent / "schema"
        pattern = str(module_path / "**" / "*.json")
        json_files = glob.glob(pattern, recursive=True)
        print(json.dumps(json_files, indent=4))  # noqa: T201
    else:
        raise ValueError("Currently only implements --list")
