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
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple, Union

from pymongo import MongoClient

from tsperf.adapter import AdapterManager, DatabaseInterfaceMixin
from tsperf.model.interface import AbstractDatabaseInterface, DatabaseInterfaceType
from tsperf.read.config import QueryTimerConfig
from tsperf.util.tictrack import timed_function
from tsperf.write.config import DataGeneratorConfig

logger = logging.getLogger(__name__)


class MongoDbAdapter(AbstractDatabaseInterface, DatabaseInterfaceMixin):
    default_address = "localhost:27017"
    default_database = "tsperf"

    def __init__(
        self,
        config: Union[DataGeneratorConfig, QueryTimerConfig],
        schema: Optional[Dict] = None,
    ):
        DatabaseInterfaceMixin.__init__(self, config=config)
        super().__init__()
        self.schema = schema

        if "://" in self.config.address:
            connection_string = self.config.address

        else:
            # Compute credentials.
            credentials = ""
            if self.username:
                credentials += self.username
                if config.password:
                    credentials += ":" + config.password
                credentials += "@"

            if self.host == "localhost":
                connection_string = f"""mongodb://{credentials}{self.host}"""
            else:
                connection_string = f"""mongodb+srv://{credentials}{self.host}"""

        self.collection_name = self._get_schema_collection_name()

        logger.info(
            f"Connecting to MongoDB at »{connection_string}« "
            f"with database »{self.database}« and collection »{self.collection_name}«"
        )
        self.client = MongoClient(connection_string)
        self.db = self.client[self.database]
        self.collection = self.db[self.collection_name]

    def close_connection(self):
        self.client.close()

    def prepare_database(self):
        """
        Communicate with database server.

        https://stackoverflow.com/a/12014215
        """
        logger.info("dbstats:   %s", self.db.command("dbstats"))
        # TODO: logger.info("collstats: %s", self.db.command("collstats", self.collection_name))

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
    def execute_query(self, query: Dict) -> list:
        return self.run_query(query)

    def run_query(self, query: Dict) -> list:
        if query is None:
            query = {}
        elif isinstance(query, Dict):
            pass
        else:
            query = json.loads(query)
        cursor = self.collection.find(query).limit(10)
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
        raise ValueError("Unable to determine collection name")


AdapterManager.register(interface=DatabaseInterfaceType.MongoDB, factory=MongoDbAdapter)
