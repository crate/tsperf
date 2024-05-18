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

from datetime import datetime
from typing import Dict, Optional, Union

import psycopg2
import psycopg2.extras
from datetime_truncate import truncate

from tsperf.adapter import AdapterManager, DatabaseInterfaceMixin
from tsperf.model.interface import AbstractDatabaseInterface, DatabaseInterfaceType
from tsperf.read.config import QueryTimerConfig
from tsperf.util.tictrack import timed_function
from tsperf.write.config import DataGeneratorConfig


class PostgreSQLAdapter(AbstractDatabaseInterface, DatabaseInterfaceMixin):
    default_address = "localhost:5432"
    default_username = "postgres"
    default_query = "SELECT 1;"

    def __init__(
        self,
        config: Union[DataGeneratorConfig, QueryTimerConfig],
        schema: Optional[Dict] = None,
    ):
        DatabaseInterfaceMixin.__init__(self, config=config)
        super().__init__()

        self.conn = psycopg2.connect(
            dbname=config.database,
            user=self.username,
            password=config.password,
            host=self.host,
            port=self.port,
        )
        self.cursor = self.conn.cursor()
        self.schema = schema
        self.table_name = (config.table, self._get_schema_table_name())[config.table is None or config.table == ""]
        self.partition = config.partition

    def close_connection(self):
        self.cursor.close()
        self.conn.close()

    def prepare_database(self):
        # Drop table.
        stmt = f"DROP TABLE IF EXISTS {self.table_name}"
        self.cursor.execute(stmt)
        self.conn.commit()

        # Create table.
        stmt = f"""CREATE TABLE {self.table_name} (
ts TIMESTAMP NOT NULL,
ts_{self.partition} TIMESTAMP NOT NULL,
"""

        columns = self._get_tags_and_fields()
        for key, value in columns.items():
            stmt += f"""{key} {value},"""
        stmt = stmt.rstrip(",") + ");"

        self.cursor.execute(stmt)
        self.conn.commit()

    @timed_function()
    def insert_stmt(self, timestamps: list, batch: list):
        stmt = self._prepare_postgres_stmt(timestamps, batch)
        self.cursor.execute(stmt)
        self.conn.commit()

    @timed_function()
    def _prepare_postgres_stmt(self, timestamps: list, batch: list) -> str:
        columns = self._get_tags_and_fields().keys()
        stmt = f"""INSERT INTO {self.table_name} (ts, ts_{self.partition},"""
        for column in columns:
            stmt += f"""{column}, """

        stmt = stmt.rstrip(", ") + ") VALUES"
        for i in range(0, len(batch)):
            t = datetime.fromtimestamp(timestamps[i] / 1000)
            trunc = truncate(t, self.partition)
            stmt = f"""{stmt} ('{t}', '{trunc}', """
            for column in columns:
                stmt += f"""'{batch[i][column]}',"""
            stmt = stmt.rstrip(",") + "),"
        stmt = stmt.rstrip(",")
        return stmt

    @timed_function()
    def execute_query(self, query: str) -> list:
        return self.run_query(query)

    def run_query(self, query: str) -> list:
        self.cursor.execute(query)
        # self.conn.commit()  # noqa: ERA001
        return self.cursor.fetchall()

    def _get_schema_table_name(self) -> str:
        for key in self.schema.keys():
            if key != "description":
                return key
        raise ValueError("Unable to determine table name")


AdapterManager.register(interface=DatabaseInterfaceType.PostgreSQL, factory=PostgreSQLAdapter)
