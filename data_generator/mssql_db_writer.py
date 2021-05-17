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

from typing import Tuple

import pyodbc
from tictrack import timed_function
from data_generator.db_writer import DbWriter
from datetime import datetime


class MsSQLDbWriter(DbWriter):
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        db_name: str,
        model: dict,
        port: int = 1433,
        table_name: str = None,
    ):
        super().__init__()
        driver = "{ODBC Driver 17 for SQL Server}"
        connection_string = (
            f"DRIVER={driver};SERVER={host},{port};DATABASE={db_name};"
            f"UID={username};PWD={password};CONNECTION TIMEOUT=170000;"
        )
        self.conn = pyodbc.connect(connection_string)
        self.cursor = self.conn.cursor()
        self.cursor.fast_executemany = True
        self.model = model
        self.table_name = (table_name, self._get_model_table_name())[
            table_name is None or table_name == ""
        ]

    def prepare_database(self):
        columns = self._get_tags_and_metrics()
        stmt = f"""
IF NOT EXISTS (SELECT * FROM sysobjects WHERE id = object_id(N'{self.table_name}')
AND OBJECTPROPERTY(id, N'IsUserTable') = 1) CREATE TABLE {self.table_name} (
ts DATETIME NOT NULL,
"""
        for key, value in columns.items():
            stmt += f"""{key} {value},"""

        stmt += f" CONSTRAINT PK_{self.table_name} PRIMARY KEY (ts, "
        tags = list(self.model[self._get_model_table_name()]["tags"].keys())
        for tag in tags:
            if tag != "description":
                stmt += f"{tag}, "
        stmt = stmt.rstrip(", ") + "));"

        self.cursor.execute(stmt)
        self.conn.commit()

    @timed_function()
    def insert_stmt(self, timestamps: list, batch: list):
        stmt, params = self._prepare_mssql_stmt(timestamps, batch)
        self.cursor.executemany(stmt, params)
        self.conn.commit()

    @timed_function()
    def _prepare_mssql_stmt(self, timestamps: list, batch: list) -> Tuple[str, list]:
        columns = self._get_tags_and_metrics().keys()
        stmt = f"""INSERT INTO {self.table_name} (ts ,"""
        for column in columns:
            stmt += f"""{column}, """

        stmt = stmt.rstrip(", ") + ") VALUES (?, "

        for column in columns:
            stmt += "?, "

        stmt = stmt.rstrip(", ") + ")"

        params = []
        for i in range(0, len(batch)):
            t = datetime.fromtimestamp(timestamps[i] / 1000)
            row = [t]
            for column in columns:
                row.append(batch[i][column])
            params.append(row)
        return stmt, params

    @timed_function()
    def execute_query(self, query: str) -> list:
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def _get_tags_and_metrics(self) -> dict:
        key = self._get_model_table_name()
        tags = self.model[key]["tags"]
        metrics = self.model[key]["metrics"]
        columns = {}
        for key, value in tags.items():
            if key != "description":
                if type(value).__name__ == "list":
                    columns[key] = "TEXT"
                else:
                    columns[key] = "INTEGER"
        for key, value in metrics.items():
            if key != "description":
                if value["type"]["value"] == "BOOL":
                    columns[value["key"]["value"]] = "BIT"
                else:
                    columns[value["key"]["value"]] = value["type"]["value"]
        return columns

    def _get_model_table_name(self) -> str:
        for key in self.model.keys():
            if key != "description":
                return key
