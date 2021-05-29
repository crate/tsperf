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
import dataclasses
import os
import os.path
import time
from argparse import Namespace
from distutils.util import strtobool

from tsperf.model.configuration import DatabaseConnectionConfiguration
from tsperf.write.model import IngestMode


@dataclasses.dataclass
class DataGeneratorConfig(DatabaseConnectionConfiguration):

    # Describing how the Timeseries Datagenerator (TSDG) behaves
    model: str = None
    id_start: int = 1
    id_end: int = 500
    ingest_mode: IngestMode = IngestMode.FAST
    ingest_size: int = 1000
    batch_size: int = -1

    # Whether to expose metrics in Prometheus format.
    prometheus_enable: bool = False
    prometheus_listen: str = "localhost:8000"
    prometheus_host: str = None
    prometheus_port: int = None

    def __post_init__(self):

        super().__post_init__()

        # environment variables describing how the write behaves
        self.ingest_ts = float(os.getenv("INGEST_TS", time.time()))
        self.ingest_delta = float(os.getenv("INGEST_DELTA", 0.5))
        # self.batch_size = int(os.getenv("BATCH_SIZE", -1))
        self.stat_delta = int(os.getenv("STAT_DELTA", 30))

        # environment variables to configure timescaledb
        self.copy = strtobool(os.getenv("TIMESCALE_COPY", "True"))
        self.distributed = strtobool(os.getenv("TIMESCALE_DISTRIBUTED", "False"))

        # environment variables to connect to influxdb
        self.token = os.getenv("TOKEN", "")
        self.organization = os.getenv("ORG", "")

        # environment variable to connect to aws timestream
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.aws_region_name = os.getenv("AWS_REGION_NAME", "")

        self.invalid_configs = []

    def validate_config(self, adapter=None) -> bool:  # noqa

        super().validate()

        if self.concurrency < 1:
            self.invalid_configs.append(f"CONCURRENCY: {self.concurrency} < 1")
        if self.id_start < 0:
            self.invalid_configs.append(f"ID_START: {self.id_start} < 0")
        if self.id_end < 0:
            self.invalid_configs.append(f"ID_END: {self.id_end} < 0")
        if self.id_end < self.id_start:
            self.invalid_configs.append(
                f"ID_START: {self.id_start} > ID_END: {self.id_end}"
            )
        if not IngestMode(self.ingest_mode):
            self.invalid_configs.append(
                f"INGEST_MODE: {self.ingest_mode} not in {IngestMode}"
            )
        if self.ingest_size < 0:
            self.invalid_configs.append(f"INGEST_SIZE: {self.ingest_size} < 0")
        if self.ingest_ts < 0:
            self.invalid_configs.append(f"INGEST_TS: {self.ingest_ts} < 0")
        if self.ingest_delta <= 0:
            self.invalid_configs.append(f"INGEST_DELTA: {self.ingest_delta} <= 0")
        if not os.path.isfile(self.model):
            self.invalid_configs.append(f"MODEL: {self.model} does not exist")

        if self.stat_delta <= 0:
            self.invalid_configs.append(f"STAT_DELTA: {self.stat_delta} <= 0")
        if self.partition.lower() not in [
            "second",
            "minute",
            "hour",
            "day",
            "week",
            "month",
            "quarter",
            "year",
        ]:
            self.invalid_configs.append(
                f"PARTITION: {self.partition} not one of second, minute, hour, day, week, "
                f"month, quarter or year"
            )
        if self.shards <= 0:
            self.invalid_configs.append(f"SHARDS: {self.shards} <= 0")
        if self.replicas < 0:
            self.invalid_configs.append(f"REPLICAS: {self.replicas} < 0")

        if self.port is None and adapter is not None:
            self.port = adapter.default_port
        if self.port is not None and int(self.port) <= 0:
            self.invalid_configs.append(f"PORT: {self.port} <= 0")

        if self.prometheus_enable:
            if ":" in self.prometheus_listen:
                host, port = self.prometheus_listen.split(":")
            else:
                host = "localhost"
                port = self.prometheus_listen
            port = int(port)
            if port < 1 or port > 65535:
                self.invalid_configs.append(
                    f"PROMETHEUS_PORT: {port} not in valid port range"
                )
            else:
                self.prometheus_host = host
                self.prometheus_port = port

        return len(self.invalid_configs) == 0

    def load_args(self, args: Namespace):
        for element in vars(self):
            if element in args:
                setattr(self, element, args[element])
