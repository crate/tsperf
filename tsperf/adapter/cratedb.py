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

from crate import client

from tsperf.adapter import AdapterManager
from tsperf.model.interface import AbstractDatabaseInterface, DatabaseInterfaceType
from tsperf.read.config import QueryTimerConfig
from tsperf.util.tictrack import timed_function
from tsperf.write.config import DataGeneratorConfig

logger = logging.getLogger(__name__)


class CrateDbAdapter(AbstractDatabaseInterface):
    default_address = "localhost:4200"
    default_username = "crate"
    default_query = "SELECT 1;"

    def __init__(
        self,
        config: Union[DataGeneratorConfig, QueryTimerConfig],
        schema: Optional[Dict] = None,
    ):
        super().__init__()

        self.conn = client.connect(config.address, username=config.username, password=config.password)
        self.cursor = self.conn.cursor()
        self.schema = schema
        self.table_name = (config.table, self._get_schema_table_name())[config.table is None or config.table == ""]
        self.partition = config.partition

        logger.info(f"Configuring CrateDB with {config.shards} shards and {config.replicas} replicas")
        self.shards = config.shards
        self.replicas = config.replicas

    def close_connection(self):
        self.cursor.close()
        self.conn.close()

    def prepare_database(self):
        # Drop table.
        stmt = f"DROP TABLE IF EXISTS {self.table_name}"
        self.cursor.execute(stmt)

        # Create table.
        stmt = f"""CREATE TABLE {self.table_name} ("ts" TIMESTAMP WITH TIME ZONE,
 "g_ts_{self.partition}" TIMESTAMP WITH TIME ZONE GENERATED ALWAYS AS date_trunc('{self.partition}', "ts"),
 "payload" OBJECT(DYNAMIC))
 CLUSTERED INTO {self.shards} SHARDS
 PARTITIONED BY ("g_ts_{self.partition}")
 WITH (number_of_replicas = {self.replicas})"""
        logger.info(f"Preparing database with statement:\n{stmt}")
        self.cursor.execute(stmt)

    @timed_function()
    def insert_stmt(self, timestamps: list, batch: list):
        stmt = f"""INSERT INTO {self.table_name} (ts, payload) (SELECT col1, col2 FROM UNNEST(?,?))"""  # noqa: S608
        self.cursor.execute(stmt, (timestamps, batch))

    @timed_function()
    def execute_query(self, query: str) -> list:
        return self.run_query(query)

    def run_query(self, query: str) -> list:
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def _get_schema_table_name(self) -> str:
        for key in self.schema.keys():
            if key != "description":
                return key
        raise ValueError("Unable to determine table name")


AdapterManager.register(interface=DatabaseInterfaceType.CrateDB, factory=CrateDbAdapter)
