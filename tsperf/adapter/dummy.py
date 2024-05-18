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
from typing import Dict, Optional, Union

from tsperf.adapter import AdapterManager
from tsperf.model.interface import AbstractDatabaseInterface, DatabaseInterfaceType
from tsperf.read.config import QueryTimerConfig
from tsperf.util.tictrack import timed_function
from tsperf.write.config import DataGeneratorConfig

logger = logging.getLogger(__name__)


class DummyDbAdapter(AbstractDatabaseInterface):
    default_address = "localhost:12345"
    default_query = "SELECT 42;"

    def __init__(
        self,
        config: Union[DataGeneratorConfig, QueryTimerConfig],
        schema: Optional[Dict] = None,
    ):
        super().__init__()

    def close_connection(self):
        pass

    def prepare_database(self):
        pass

    @timed_function()
    def insert_stmt(self, timestamps: list, batch: list):
        pass

    @timed_function()
    def execute_query(self, query: str) -> list:
        pass

    def run_query(self, query: str) -> list:
        pass

    def _get_schema_table_name(self) -> str:
        pass


AdapterManager.register(interface=DatabaseInterfaceType.Dummy, factory=DummyDbAdapter)
