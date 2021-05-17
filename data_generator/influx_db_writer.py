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
from influxdb_client import InfluxDBClient, Bucket
from influxdb_client.client.write_api import SYNCHRONOUS, Point
from datetime import datetime


class InfluxDbWriter(DbWriter):
    def __init__(
        self, host: str, token: str, org: str, model: dict, database_name: str = None
    ):
        super().__init__()
        self.client = InfluxDBClient(url=host, token=token)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
        self.org = org
        self.model = model
        self.bucket = None
        self.database_name = (database_name, self._get_model_database_name())[
            database_name is None or database_name == ""
        ]

    def close_connection(self):
        self.client.close()

    def prepare_database(self):
        buckets = self.client.buckets_api().find_buckets()
        for bucket in buckets.buckets:
            if bucket.name == self.database_name:
                self.bucket = bucket

        if self.bucket is None:
            bucket = Bucket(
                name=self.database_name, org_id=self.org, retention_rules=[]
            )
            self.bucket = self.client.buckets_api().create_bucket(bucket)

    @timed_function()
    def insert_stmt(self, timestamps: list, batch: list):
        data = self._prepare_influx_stmt(timestamps, batch)
        self.write_api.write(bucket=self.database_name, org=self.org, record=data)

    @timed_function()
    def _prepare_influx_stmt(self, timestamps: list, batch: list) -> list:
        data = []
        tags, metrics = self._get_tags_and_metrics()
        for i in range(0, len(batch)):
            t = datetime.fromtimestamp(timestamps[i] / 1000)
            point = Point(self.database_name).time(t)
            for tag in tags:
                point.tag(tag, batch[i][tag])
            for metric in metrics:
                point.field(metric, batch[i][metric])
            data.append(point)

        return data

    @timed_function()
    def execute_query(self, query: str) -> list:
        return self.query_api.query(query)

    def _get_tags_and_metrics(self) -> Tuple[dict, dict]:
        key = self._get_model_database_name()
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

    def _get_model_database_name(self) -> str:
        for key in self.model.keys():
            if key != "description":
                return key
