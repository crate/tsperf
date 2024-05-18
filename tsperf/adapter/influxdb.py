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

from influxdb_client import Bucket, InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS, Point

from tsperf.adapter import AdapterManager
from tsperf.model.interface import AbstractDatabaseInterface, DatabaseInterfaceType
from tsperf.read.config import QueryTimerConfig
from tsperf.util.tictrack import timed_function
from tsperf.write.config import DataGeneratorConfig

logger = logging.getLogger(__name__)


class InfluxDbAdapter(AbstractDatabaseInterface):
    default_address = "http://localhost:8086/"

    def __init__(
        self,
        config: Union[DataGeneratorConfig, QueryTimerConfig],
        schema: Optional[Dict] = None,
    ):
        super().__init__()

        logger.info(
            f"Connecting to InfluxDB at {config.address} with organization "
            f"{config.influxdb_organization} and token {config.influxdb_token}"
        )
        self.client = InfluxDBClient(
            url=config.address,
            token=config.influxdb_token,
            org=config.influxdb_organization,
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
        self.organization = config.influxdb_organization
        self.schema = schema or {}
        self.bucket = None

        database_name = config.database
        self.database_name = (database_name, self._get_schema_database_name())[
            database_name is None or database_name == ""
        ]
        logger.info(f"Using InfluxDB bucket »{self.database_name}«")

    def close_connection(self):
        self.client.close()

    def prepare_database(self):
        buckets = self.client.buckets_api().find_buckets()
        for bucket in buckets.buckets:
            if bucket.name == self.database_name:
                self.bucket = bucket

        if self.bucket is None:
            if self.client.__class__.__name__ == "Mock":
                org_id = "Mock12345"
            else:
                org = self._get_first_organization()
                org_id = org.id
            logger.info(f"Creating InfluxDB bucket {bucket.name} in organization {org_id}")
            bucket = Bucket(name=self.database_name, org_id=org_id, retention_rules=[])
            self.bucket = self.client.buckets_api().create_bucket(bucket)

    def _get_first_organization(self):
        org = list(
            filter(
                lambda it: it.name == self.organization,
                self.client.organizations_api().find_organizations(),
            )
        )[0]
        return org

    @timed_function()
    def insert_stmt(self, timestamps: list, batch: list):
        data = self._prepare_influx_stmt(timestamps, batch)
        self.write_api.write(bucket=self.database_name, org=self.organization, record=data)

    @timed_function()
    def _prepare_influx_stmt(self, timestamps: list, batch: list) -> list:
        data = []
        tags, fields = self._get_tags_and_fields()
        for i in range(0, len(batch)):
            t = datetime.fromtimestamp(timestamps[i] / 1000)
            point = Point(self.database_name).time(t)
            for tag in tags:
                point.tag(tag, batch[i][tag])
            for field in fields:
                point.field(field, batch[i][field])
            data.append(point)

        return data

    @timed_function()
    def execute_query(self, query: str) -> list:
        return self.run_query(query)

    def run_query(self, query: str) -> list:
        return self.query_api.query(query, org=self.organization)

    def _get_tags_and_fields(self) -> Tuple[dict, dict]:
        key = self._get_schema_database_name()
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

    def _get_schema_database_name(self) -> str:
        for key in self.schema.keys():
            if key != "description":
                return key
        raise ValueError("Unable to determine database name")


AdapterManager.register(interface=DatabaseInterfaceType.InfluxDB, factory=InfluxDbAdapter)
