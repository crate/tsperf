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

from data_generator.db_writer import DbWriter
from crate import client
from tictrack import timed_function


class CrateDbWriter(DbWriter):
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        model: dict,
        table_name: str = None,
        shards: int = None,
        replicas: int = None,
        partition: str = "week",
    ):
        super().__init__()
        self.conn = client.connect(host, username=username, password=password)
        self.cursor = self.conn.cursor()
        self.model = model
        self.table_name = (table_name, self._get_model_table_name())[
            table_name is None or table_name == ""
        ]
        self.shards = (shards, 21)[shards is None]
        self.replicas = (replicas, 1)[replicas is None]
        self.partition = partition

    def close_connection(self):
        self.cursor.close()
        self.conn.close()

    def prepare_database(self):
        stmt = f"""CREATE TABLE IF NOT EXISTS {self.table_name} ("ts" TIMESTAMP WITH TIME ZONE,
 "g_ts_{self.partition}" TIMESTAMP WITH TIME ZONE GENERATED ALWAYS AS date_trunc('{self.partition}', "ts"),
 "payload" OBJECT(DYNAMIC))
 CLUSTERED INTO {self.shards} SHARDS
 PARTITIONED BY ("g_ts_{self.partition}")
 WITH (number_of_replicas = {self.replicas})"""
        self.cursor.execute(stmt)

    @timed_function()
    def insert_stmt(self, timestamps: list, batch: list):
        stmt = f"""INSERT INTO {self.table_name} (ts, payload) (SELECT col1, col2 FROM UNNEST(?,?))"""
        self.cursor.execute(stmt, (timestamps, batch))

    @timed_function()
    def execute_query(self, query: str) -> list:
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def _get_model_table_name(self) -> str:
        for key in self.model.keys():
            if key != "description":
                return key
