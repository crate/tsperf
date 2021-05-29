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
import shutil
from argparse import Namespace

from tsperf.model.configuration import DatabaseConnectionConfiguration


@dataclasses.dataclass
class QueryTimerConfig(DatabaseConnectionConfiguration):

    # The query to invoke against the database.
    query: str = None

    # The concurrency level.
    concurrency: int = 10

    # How many times each thread executes the query.
    iterations: int = 100

    def __post_init__(self):

        super().__post_init__()

        # environment variables describing how the tsqt behaves
        # self.concurrency = int(os.getenv("CONCURRENCY", 10))
        self.quantiles = os.getenv("QUANTILES", "50,60,75,90,99").split(",")
        self.refresh_rate = float(os.getenv("REFRESH_RATE", 0.1))

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

        if self.query is None and adapter is not None:
            self.query = adapter.default_select_query

        if "PYTEST_CURRENT_TEST" not in os.environ:
            if self.host is None or self.host.strip() == "":
                self.invalid_configs.append(
                    f"--host parameter or HOST environment variable required"
                )
            if self.query is None or self.query.strip() == "":
                self.invalid_configs.append(
                    f"--query parameter or QUERY environment variable required"
                )

        if self.port is None and adapter is not None:
            self.port = adapter.default_port
        if self.port is not None and int(self.port) <= 0:
            self.invalid_configs.append(f"PORT: {self.port} <= 0")

        if self.concurrency * self.iterations < 100:
            self.invalid_configs.append(
                f"CONCURRENCY: {self.concurrency}; ITERATIONS: {self.iterations}. At least "
                f"100 queries must be run. The current configuration results "
                f"in {self.concurrency * self.iterations} queries (concurrency * iterations)"
            )
        terminal_size = shutil.get_terminal_size()
        if len(self.quantiles) > terminal_size.lines - 12:
            self.invalid_configs.append(
                f"QUANTILES: {self.quantiles}; TERMINAL_LINES: {terminal_size.lines}. "
                f"QueryTimer needs a bigger terminal (at least {len(self.quantiles) + 12}) "
                f"to display all results. Please increase "
                f"terminal size or reduce number of quantiles."
            )

        return len(self.invalid_configs) == 0

    def load_args(self, args: Namespace):
        for element in vars(self):
            if element in args:
                setattr(self, element, args[element])
