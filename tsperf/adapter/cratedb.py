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
from typing import Dict, Union

from crate import client

from tsperf.adapter import AdapterManager
from tsperf.model.interface import DatabaseInterfaceBase, DatabaseInterfaceType
from tsperf.read.config import QueryTimerConfig
from tsperf.util.tictrack import timed_function
from tsperf.write.config import DataGeneratorConfig

logger = logging.getLogger(__name__)


class CrateDbAdapter(DatabaseInterfaceBase):

    default_port = 4200
    default_select_query = "SELECT 1;"

    def __init__(
        self,
        config: Union[DataGeneratorConfig, QueryTimerConfig],
        schema: Dict,
    ):
        super().__init__()
        if ":" not in config.host:
            config.host = f"{config.host}:{self.default_port}"
        self.conn = client.connect(
            config.host, username=config.username, password=config.password
        )
        self.cursor = self.conn.cursor()
        self.schema = schema
        self.table_name = (config.table_name, self._get_schema_table_name())[
            config.table_name is None or config.table_name == ""
        ]
        self.partition = config.partition

        logger.info(
            f"Configuring CrateDB with {config.shards} shards and {config.replicas} replicas"
        )
        self.shards = config.shards
        self.replicas = config.replicas

    def close_connection(self):
        self.cursor.close()
        self.conn.close()

    def prepare_database(self):
        stmt = f"""CREATE TABLE IF NOT EXISTS {self.table_name} ("ts" TIMESTAMP WITH TIME ZONE,
 "g_ts_{self.partition}" TIMESTAMP WITH TIME ZONE GENERATED ALWAYS AS date_trunc('{self.partition}', "ts"),
 "payload" OBJECT(DYNAMIC))
 CLUSTERED INTO {self.shards} SHARDS
 PARTITIONED BY ("g_ts_{self.partition}")
 WITH (number_of_replicas = {self.replicas})"""  # noqa:S608
        self.cursor.execute(stmt)

    @timed_function()
    def insert_stmt(self, timestamps: list, batch: list):
        stmt = f"""INSERT INTO {self.table_name} (ts, payload) (SELECT col1, col2 FROM UNNEST(?,?))"""  # noqa:S608
        self.cursor.execute(stmt, (timestamps, batch))

    @timed_function()
    def execute_query(self, query: str) -> list:
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def _get_schema_table_name(self) -> str:
        for key in self.schema.keys():
            if key != "description":
                return key


AdapterManager.register(interface=DatabaseInterfaceType.CrateDB, factory=CrateDbAdapter)
