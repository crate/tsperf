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
import time
from argparse import Namespace

from tsperf.model.configuration import DatabaseConnectionConfiguration
from tsperf.write.model import IngestMode


@dataclasses.dataclass
class DataGeneratorConfig(DatabaseConnectionConfiguration):
    # The concurrency level.
    concurrency: int = 2

    # Describing how the Timeseries Datagenerator (TSDG) behaves
    id_start: int = 1
    id_end: int = 500
    timestamp_start: int = None
    timestamp_delta: int = 0.5

    ingest_mode: IngestMode = IngestMode.FAST
    ingest_size: int = 1000
    batch_size: int = -1

    # Whether to expose metrics in Prometheus format.
    prometheus_enable: bool = False
    prometheus_listen: str = "localhost:8000"
    prometheus_host: str = None
    prometheus_port: int = None

    statistics_interval: int = 30

    def __post_init__(self):
        super().__post_init__()

        # How the write behaves.
        if self.timestamp_start is None:
            self.timestamp_start = time.time()

        self.invalid_configs = []

    def validate_config(self) -> bool:  # noqa
        super().validate()

        if self.concurrency < 1:
            self.invalid_configs.append(f"CONCURRENCY: {self.concurrency} < 1")
        if self.id_start < 0:
            self.invalid_configs.append(f"ID_START: {self.id_start} < 0")
        if self.id_end < 0:
            self.invalid_configs.append(f"ID_END: {self.id_end} < 0")
        if self.id_end < self.id_start:
            self.invalid_configs.append(f"ID_START: {self.id_start} > ID_END: {self.id_end}")
        if self.timestamp_start < 0:
            self.invalid_configs.append(f"TIMESTAMP_START: {self.timestamp_start} < 0")
        if self.timestamp_delta <= 0:
            self.invalid_configs.append(f"TIMESTAMP_DELTA: {self.timestamp_delta} <= 0")

        if not IngestMode(self.ingest_mode):
            self.invalid_configs.append(f"INGEST_MODE: {self.ingest_mode} not in {IngestMode}")
        if self.ingest_size < 0:
            self.invalid_configs.append(f"INGEST_SIZE: {self.ingest_size} < 0")

        if self.statistics_interval <= 0:
            self.invalid_configs.append(f"STATISTICS_INTERVAL: {self.statistics_interval} <= 0")
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
                f"PARTITION: {self.partition} not one of second, minute, hour, day, week, " f"month, quarter or year"
            )
        if self.shards <= 0:
            self.invalid_configs.append(f"SHARDS: {self.shards} <= 0")
        if self.replicas < 0:
            self.invalid_configs.append(f"REPLICAS: {self.replicas} < 0")

        if self.prometheus_enable:
            if ":" in self.prometheus_listen:
                host, port = self.prometheus_listen.split(":")
            else:
                host = "localhost"
                port = self.prometheus_listen
            port = int(port)
            if port < 1 or port > 65535:
                self.invalid_configs.append(f"PROMETHEUS_PORT: {port} not in valid port range")
            else:
                self.prometheus_host = host
                self.prometheus_port = port

        return len(self.invalid_configs) == 0

    def load_args(self, args: Namespace):
        for element in vars(self):
            if element in args:
                setattr(self, element, args[element])
