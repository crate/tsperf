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
from datetime import datetime
from typing import Dict, Optional, Tuple, Union

from tsperf.adapter import AdapterManager, DatabaseInterfaceMixin
from tsperf.model.interface import AbstractDatabaseInterface, DatabaseInterfaceType
from tsperf.read.config import QueryTimerConfig
from tsperf.util.tictrack import timed_function
from tsperf.write.config import DataGeneratorConfig

logger = logging.getLogger(__name__)


class MsSQLDbAdapter(AbstractDatabaseInterface, DatabaseInterfaceMixin):
    default_address = "127.0.0.1:1433"  # "localhost" does not work here
    default_username = "sa"
    default_password = "yayRirr3"  # noqa: S105
    default_query = "SELECT 1;"

    def __init__(
        self,
        config: Union[DataGeneratorConfig, QueryTimerConfig],
        schema: Optional[Dict] = None,
    ):
        import pyodbc

        DatabaseInterfaceMixin.__init__(self, config=config)
        super().__init__()

        driver = "{ODBC Driver 17 for SQL Server}"
        connection_string = (
            f"DRIVER={driver};SERVER={self.host},{self.port};DATABASE={config.database};"
            f"UID={self.username};PWD={self.password};CONNECTION TIMEOUT=10;"
        )
        logger.info(f"Connecting with »{connection_string}«")
        self.conn = pyodbc.connect(connection_string, timeout=15)
        self.cursor = self.conn.cursor()
        self.cursor.fast_executemany = True
        self.schema = schema
        self.table_name = (config.table, self._get_schema_table_name())[config.table is None or config.table == ""]

    def prepare_database(self):
        # Drop table.
        stmt = (
            f"IF EXISTS "  # noqa: S608
            f"   (SELECT * FROM sysobjects "
            f"   WHERE id = object_id(N'{self.table_name}') AND OBJECTPROPERTY(id, N'IsUserTable') = 1) "
            f"DROP TABLE {self.table_name}"
        )
        self.cursor.execute(stmt)
        self.conn.commit()

        # Create table.
        stmt = f"CREATE TABLE {self.table_name} (ts DATETIME NOT NULL,"

        columns = self._get_tags_and_fields()
        for key, value in columns.items():
            stmt += f"""{key} {value},"""

        stmt += f" CONSTRAINT PK_{self.table_name} PRIMARY KEY (ts, "
        tags = list(self.schema[self._get_schema_table_name()]["tags"].keys())
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
        columns = self._get_tags_and_fields().keys()
        stmt = f"""INSERT INTO {self.table_name} (ts ,"""
        for column in columns:
            stmt += f"""{column}, """

        stmt = stmt.rstrip(", ") + ") VALUES (?, "

        for _ in columns:
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
        return self.run_query(query)

    def run_query(self, query: str) -> list:
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def _get_tags_and_fields(self) -> dict:
        key = self._get_schema_table_name()
        tags = self.schema[key]["tags"]
        fields = self.schema[key]["fields"]
        columns = {}
        for key, value in tags.items():
            if key != "description":
                if type(value).__name__ == "list":
                    columns[key] = "TEXT"
                else:
                    columns[key] = "INTEGER"
        for key, value in fields.items():
            if key != "description":
                if value["type"]["value"] == "BOOL":
                    columns[value["key"]["value"]] = "BIT"
                else:
                    columns[value["key"]["value"]] = value["type"]["value"]
        return columns

    def _get_schema_table_name(self) -> str:
        for key in self.schema.keys():
            if key != "description":
                return key
        raise ValueError("Unable to determine table name")

    def close_connection(self):
        self.conn.close()


AdapterManager.register(interface=DatabaseInterfaceType.MicrosoftSQL, factory=MsSQLDbAdapter)
