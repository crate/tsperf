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
from typing import Tuple

from pymongo import CursorType, MongoClient

from tsperf.model.interface import DatabaseInterfaceBase
from tsperf.util.tictrack import timed_function


class MongoDbAdapter(DatabaseInterfaceBase):
    def __init__(
        self, host: str, username: str, password: str, database_name: str, schema: dict
    ):
        super().__init__()
        self.schema = schema
        if host == "localhost":
            connection_string = f"""mongodb://{username}:{password}@{host}"""
        else:
            connection_string = f"""mongodb+srv://{username}:{password}@{host}"""

        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        self.collection = self.db[self._get_schema_collection_name()]

    def close_connection(self):
        self.client.close()

    @timed_function()
    def insert_stmt(self, timestamps: list, batch: list):
        data = self._prepare_mongo_stmt(timestamps, batch)
        self.collection.insert_many(data)

    @timed_function()
    def _prepare_mongo_stmt(self, timestamps: list, batch: list) -> list:
        data = []
        tags, fields = self._get_tags_and_fields()
        for i in range(0, len(batch)):
            t = datetime.fromtimestamp(timestamps[i] / 1000)
            document = {
                "measurement": self._get_schema_collection_name(),
                "date": t,
                "tags": {},
                "fields": {},
            }
            for tag in tags:
                document["tags"][tag] = batch[i][tag]
            for field in fields:
                document["fields"][field] = batch[i][field]
            data.append(document)
        return data

    @timed_function()
    def execute_query(self, query: str) -> list:
        return self.run_query(query)

    def run_query(self, query: str) -> list:
        cursor = self.collection.find(query, cursor_type=CursorType.EXHAUST)
        return list(cursor)

    def _get_tags_and_fields(self) -> Tuple[dict, dict]:
        key = self._get_schema_collection_name()
        tags_ = self.schema[key]["tags"]
        fields_ = self.schema[key]["fields"]
        tags = []
        fields = []
        for key in tags_.keys():
            if key != "description":
                tags.append(key)
        for key, value in fields_.items():
            if key != "description":
                fields.append(value["key"]["value"])
        return tags, fields

    def _get_schema_collection_name(self) -> str:
        for key in self.schema.keys():
            if key != "description":
                return key
