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
from typing import List

from tsperf.adapter import AdapterManager
from tsperf.model.configuration import DatabaseConnectionConfiguration


@dataclasses.dataclass
class QueryTimerConfig(DatabaseConnectionConfiguration):
    # The query to invoke against the database.
    query: str = None

    # The concurrency level.
    concurrency: int = 4

    # How many times each thread executes the query.
    iterations: int = 1000

    refresh_interval: float = 0.1
    quantiles: List[str] = "50,60,75,90,99"

    invalid_configs: dataclasses.InitVar[List] = None

    def __post_init__(self, invalid_configs):
        super().__post_init__()

        if isinstance(self.quantiles, str):
            self.quantiles = self.quantiles.split(",")

        self.invalid_configs = []

    def validate_config(self) -> bool:  # noqa
        super().validate()

        if self.query is None:
            adapter = AdapterManager.get(self.adapter)
            self.query = adapter.default_query

        if isinstance(self.query, str):
            self.query = self.query.format(**self.__dict__)

        if "PYTEST_CURRENT_TEST" not in os.environ:
            if self.address is None or self.address.strip() == "":
                self.invalid_configs.append("--address parameter or ADDRESS environment variable required")

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
