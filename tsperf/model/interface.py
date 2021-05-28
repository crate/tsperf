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


class DatabaseInterfaceBase:

    default_port = None
    default_select_query = None

    @abstractmethod
    def __init__(self):
        pass

    def connect_to_database(self):  # pragma: no cover
        pass

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

    def _get_tags_and_metrics(self):
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
                columns[value["key"]["value"]] = value["type"]["value"]
        return columns


class DatabaseInterfaceType(Enum):
    CrateDB = "cratedb"
    TimescaleDB = "timescaledb"
    InfluxDB1 = "influxdb1"
    InfluxDB2 = "influxdb2"
    MongoDB = "mongodb"
    PostgreSQL = "postgresql"
    TimeStream = "timestream"
    MsSQL = "mssql"
