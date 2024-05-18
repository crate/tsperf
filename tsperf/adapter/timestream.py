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
import math
from typing import Dict, Optional, Tuple, Union

import boto3
import numpy
from botocore.config import Config

from tsperf.adapter import AdapterManager, DatabaseInterfaceMixin
from tsperf.model.interface import AbstractDatabaseInterface, DatabaseInterfaceType
from tsperf.read.config import QueryTimerConfig
from tsperf.util.tictrack import timed_function
from tsperf.write.config import DataGeneratorConfig

logger = logging.getLogger(__name__)


class AmazonTimestreamAdapter(AbstractDatabaseInterface, DatabaseInterfaceMixin):
    default_database = "tsperf"

    def __init__(
        self,
        config: Union[DataGeneratorConfig, QueryTimerConfig],
        schema: Optional[Dict] = None,
    ):
        DatabaseInterfaceMixin.__init__(self, config=config)
        super().__init__()

        self.schema = schema
        self.database_name = self.database
        self.table_name = self._get_schema_collection_name()

        logger.info(f"Connecting to AWS region »{config.aws_region_name}« with key id »{config.aws_access_key_id}«")
        self.session = boto3.session.Session(
            config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
            region_name=config.aws_region_name,
        )

        logger.info("Creating database session objects")
        self.write_client = self.session.client(
            "timestream-write",
            config=Config(read_timeout=20, max_pool_connections=5000, retries={"max_attempts": 10}),
        )
        self.query_client = self.session.client("timestream-query")

        logger.info(
            f"Connecting to Amazon Timestream at »{config.address}« "
            f"with database »{self.database_name}« and table »{self.table_name}«"
        )

    @timed_function()
    def insert_stmt(self, timestamps: list, batch: list):
        data = self._prepare_timestream_stmt(timestamps, batch)
        for values in data.values():
            common_attributes = values["common_attributes"]
            records = numpy.array_split(values["records"], math.ceil(len(values["records"]) / 100))
            for record in records:
                record_list = list(record)
                try:
                    self.write_client.write_records(
                        DatabaseName=self.database_name,
                        TableName=self.table_name,
                        Records=record_list,
                        CommonAttributes=common_attributes,
                    )
                except Exception as e:
                    logging.warning(e)

    @timed_function()
    def _prepare_timestream_stmt(self, timestamps: list, batch: list) -> dict:
        data = {}
        tags, fields = self._get_tags_and_fields()
        for i in range(0, len(batch)):
            record = {"Time": str(timestamps[i])}
            common_attributes = {"Dimensions": []}
            for tag in tags:
                common_attributes["Dimensions"].append({"Name": tag, "Value": str(batch[i][tag])})
            if str(common_attributes) not in data:
                data[str(common_attributes)] = {
                    "common_attributes": common_attributes,
                    "records": [],
                }
            for field in fields:
                record = dict(record)
                record.update(
                    {
                        "MeasureName": field["name"],
                        "MeasureValue": str(batch[i][field["name"]]),
                        "MeasureValueType": field["type"],
                    }
                )
                data[str(common_attributes)]["records"].append(record)
        return data

    @timed_function()
    def execute_query(self, query: str, retry: bool = True) -> list:
        return self.run_query(query)

    def run_query(self, query: str, retry: bool = True) -> list:
        result = []
        try:
            paginator = self.query_client.get_paginator("query")
            page_iterator = paginator.paginate(QueryString=query)
            for page in page_iterator:
                result.append(page)
        except Exception as ex:
            if retry:
                result = self.execute_query(query, False)
            else:
                raise RuntimeError(ex) from ex
        return result

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
                fields.append(
                    {
                        "name": value["key"]["value"],
                        "type": self._convert_to_timestream_type(value["type"]["value"]),
                    }
                )
        return tags, fields

    @staticmethod
    def _convert_to_timestream_type(field_type: str) -> str:
        field_type = field_type.lower()
        if field_type in ["float", "double"]:
            return "DOUBLE"
        elif field_type in ["bool", "boolean"]:
            return "BOOLEAN"
        elif field_type in ["int", "long", "uint"]:
            return "BIGINT"
        else:
            return "VARCHAR"

    def _get_schema_collection_name(self) -> str:
        for key in self.schema.keys():
            if key != "description":
                return key
        raise ValueError("Unable to determine collection name")

    def prepare_database(self):
        try:
            self.write_client.create_database(DatabaseName=self.database_name)
            logger.info("Database [%s] created successfully." % self.database_name)
        except Exception as ex:
            logger.error(f"Creating database failed: {ex}")

        retention_properties = {
            "MemoryStoreRetentionPeriodInHours": 24,
            "MagneticStoreRetentionPeriodInDays": 7,
        }
        try:
            self.write_client.create_table(
                DatabaseName=self.database_name,
                TableName=self.table_name,
                RetentionProperties=retention_properties,
            )
            logger.info("Table [%s] successfully created." % self.table_name)
        except Exception as ex:
            logger.error(f"Creating table failed: {ex}")

    def close_connection(self):
        pass


AdapterManager.register(interface=DatabaseInterfaceType.Timestream, factory=AmazonTimestreamAdapter)
