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

import psycopg2
import psycopg2.extras
from pgcopy import CopyManager
from tictrack import timed_function
from data_generator.db_writer import DbWriter
from datetime import datetime
from datetime_truncate import truncate


class TimescaleDbWriter(DbWriter):
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        ts_db_name: str,
        model: dict,
        table_name: str = None,
        partition: str = "week",
        copy: bool = False,
        distributed: bool = False,
    ):
        super().__init__()
        self.conn = psycopg2.connect(
            dbname=ts_db_name, user=username, password=password, host=host, port=port
        )
        self.cursor = self.conn.cursor()
        self.model = model
        self.table_name = (table_name, self._get_model_table_name())[
            table_name is None or table_name == ""
        ]
        self.partition = partition
        self.copy = copy
        self.distributed = distributed

    def close_connection(self):
        self.cursor.close()
        self.conn.close()

    def prepare_database(self):
        columns = self._get_tags_and_metrics()
        stmt = f"""CREATE TABLE IF NOT EXISTS {self.table_name} (
ts TIMESTAMP NOT NULL,
ts_{self.partition} TIMESTAMP NOT NULL,
"""
        for key, value in columns.items():
            stmt += f"""{key} {value},"""
        stmt = stmt.rstrip(",") + ");"

        self.cursor.execute(stmt)
        self.conn.commit()
        if self.distributed:
            tag = self._get_partition_tag()
            stmt = f"SELECT create_distributed_hypertable('{self.table_name}', 'ts', '{tag}', if_not_exists => true);"
        else:
            stmt = (
                f"SELECT create_hypertable('{self.table_name}', 'ts', 'ts_{self.partition}', 10, "
                f"if_not_exists => true);"
            )
        self.cursor.execute(stmt)
        self.conn.commit()

    @timed_function()
    def insert_stmt(self, timestamps: list, batch: list):
        if self.copy:
            self._prepare_copy(timestamps, batch)
        else:
            stmt = self._prepare_timescale_stmt(timestamps, batch)
            self.cursor.execute(stmt)
        self.conn.commit()

    @timed_function()
    def _prepare_copy(self, timestamps: list, batch: list):
        columns = self._get_tags_and_metrics().keys()
        values = []

        for i in range(0, len(timestamps)):
            t = datetime.fromtimestamp(timestamps[i] / 1000)
            trunc = truncate(t, self.partition)
            data = [t, trunc]
            for column in columns:
                data.append(batch[i][column])
            values.append(data)

        cols = ["ts", f"ts_{self.partition}"]
        for column in columns:
            cols.append(column)
        copy_manager = CopyManager(self.conn, self.table_name, cols)
        copy_manager.copy(values)

    @timed_function()
    def _prepare_timescale_stmt(self, timestamps: list, batch: list) -> str:
        columns = self._get_tags_and_metrics().keys()
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
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def _get_model_table_name(self) -> str:
        for key in self.model.keys():
            if key != "description":
                return key

    def _get_partition_tag(self, top_level: bool = False) -> str:
        key = self._get_model_table_name()
        tags = list(self.model[key]["tags"].keys())
        if "description" in tags:
            tags.remove("description")
        return tags[0] if top_level else tags[-1]
