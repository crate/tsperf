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
from abc import abstractmethod
from enum import Enum


class DatabaseInterfaceType(Enum):
    CrateDB = "cratedb"
    CrateDBpg = "cratedbpg"
    Dummy = "dummy"
    InfluxDB = "influxdb"
    MicrosoftSQL = "mssql"
    MongoDB = "mongodb"
    PostgreSQL = "postgresql"
    TimescaleDB = "timescaledb"
    Timestream = "timestream"


class AbstractDatabaseInterface:
    default_address = None
    default_username = None
    default_database = None
    default_query = None

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def connect_to_database(self):  # pragma: no cover
        pass

    @abstractmethod
    def prepare_database(self):  # pragma: no cover
        pass

    @abstractmethod
    def close_connection(self):  # pragma: no cover
        pass

    @abstractmethod
    def insert_stmt(self, timestamps: list, batch: list):  # pragma: no cover
        pass

    @abstractmethod
    def execute_query(self, query: str):  # pragma: no cover
        pass

    def _get_schema_table_name(self) -> str:
        pass

    def _get_tags_and_fields(self):
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
                columns[value["key"]["value"]] = value["type"]["value"]
        return columns
