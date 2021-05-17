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

from tictrack import timed_function
from data_generator.db_writer import DbWriter
from pymongo import MongoClient
from pymongo import CursorType
from datetime import datetime


class MongoDbWriter(DbWriter):
    def __init__(
        self, host: str, username: str, password: str, database_name: str, model: dict
    ):
        super().__init__()
        self.model = model
        if host == "localhost":
            connection_string = f"""mongodb://{username}:{password}@{host}"""
        else:
            connection_string = f"""mongodb+srv://{username}:{password}@{host}"""

        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        self.collection = self.db[self._get_model_collection_name()]

    def close_connection(self):
        self.client.close()

    @timed_function()
    def insert_stmt(self, timestamps: list, batch: list):
        data = self._prepare_mongo_stmt(timestamps, batch)
        self.collection.insert_many(data)

    @timed_function()
    def _prepare_mongo_stmt(self, timestamps: list, batch: list) -> list:
        data = []
        tags, metrics = self._get_tags_and_metrics()
        for i in range(0, len(batch)):
            t = datetime.fromtimestamp(timestamps[i] / 1000)
            document = {
                "measurement": self._get_model_collection_name(),
                "date": t,
                "tags": {},
                "metrics": {},
            }
            for tag in tags:
                document["tags"][tag] = batch[i][tag]
            for metric in metrics:
                document["metrics"][metric] = batch[i][metric]
            data.append(document)
        return data

    @timed_function()
    def execute_query(self, query: str) -> list:
        cursor = self.collection.find(query, cursor_type=CursorType.EXHAUST)
        return list(cursor)

    def _get_tags_and_metrics(self) -> Tuple[dict, dict]:
        key = self._get_model_collection_name()
        tags_ = self.model[key]["tags"]
        metrics_ = self.model[key]["metrics"]
        tags = []
        metrics = []
        for key, value in tags_.items():
            if key != "description":
                tags.append(key)
        for key, value in metrics_.items():
            if key != "description":
                metrics.append(value["key"]["value"])
        return tags, metrics

    def _get_model_collection_name(self) -> str:
        for key in self.model.keys():
            if key != "description":
                return key
