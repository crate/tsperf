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
import sys

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
            list(map(lambda p: p.name.lower(), DatabaseInterfaceType)),
            case_sensitive=False,
        ),
        required=True,
        help="Which database adapter to use",
    ),
    click.option(
        "--address",
        envvar="ADDRESS",
        type=click.STRING,
        help="Database address (DSN URI, hostname:port) according to the database client requirements",
    ),
    click.option(
        "--influxdb-organization",
        envvar="INFLUXDB_ORGANIZATION",
        type=click.STRING,
        help="Organization name for InfluxDB V2. "
        "See also: https://v2.docs.influxdata.com/v2.0/organizations/.",
    ),
    click.option(
        "--influxdb-token",
        envvar="INFLUXDB_TOKEN",
        type=click.STRING,
        help="Authentication token for InfluxDB V2. "
        "See also https://v2.docs.influxdata.com/v2.0/security/tokens/view-tokens/.",
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
)

performance_options = cloup.option_group(
    "Performance options",
    click.option(
        "--concurrency",
        envvar="CONCURRENCY",
        type=click.INT,
        help="Number of worker threads for executing queries in parallel. Recommended: 1-4",
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
        "--ingest-mode",
        envvar="INGEST_MODE",
        type=click.Choice(
            list(map(lambda p: p.name.lower(), IngestMode)),
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
        default=100,
        help="How many times each thread executes the query",
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


@cloup.group(
    "tsperf", help=f"See documentation for further details: {TSPERF_README_URL}"
)
def main():
    setup_logging()


@main.command("write")
@general_options
@adapter_options
@performance_options
@write_options
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
@performance_options
@read_options
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
