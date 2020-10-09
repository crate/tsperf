import boto3
import math
import numpy
from botocore.config import Config
from modules import helper
from modules.db_writer import DbWriter


class TimeStreamWriter(DbWriter):
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name, database_name, model):
        super().__init__()
        self.model = model
        self.database_name = database_name
        self.table_name = self._get_model_collection_name()
        self.session = boto3.session.Session(aws_access_key_id, aws_secret_access_key=aws_secret_access_key,
                                             region_name=region_name)
        self.write_client = self.session.client('timestream-write',
                                                config=Config(read_timeout=20, max_pool_connections=5000,
                                                              retries={'max_attempts': 10}))
        self.query_client = self.session.client('timestream-query')

    def insert_stmt(self, timestamps, batch):
        data = helper.execute_timed_function(self._prepare_timestream_stmt, timestamps, batch)
        records = numpy.array_split(data, math.ceil(len(data)/100))
        for record in records:
            values = list(record)
            self.write_client.write_records(DatabaseName=self.database_name, TableName=self.table_name,
                                            Records=values, CommonAttributes={})

    def _prepare_timestream_stmt(self, timestamps, batch):
        data = []
        tags, metrics = self._get_tags_and_metrics()
        for i in range(0, len(batch)):
            record = {"Time": str(timestamps[i]),
                      "Dimensions": []}
            for tag in tags:
                record["Dimensions"].append({"Name": tag, "Value": str(batch[i][tag])})
            for metric in metrics:
                record_metric = dict(record)
                record_metric.update({"MeasureName": metric["name"],
                                      "MeasureValue": str(batch[i][metric["name"]]),
                                      "MeasureValueType": metric["type"]})
                data.append(record_metric)
        return data

    def execute_query(self, query):
        result = []
        paginator = self.query_client.get_paginator('query')
        page_iterator = paginator.paginate(QueryString=query)
        for page in page_iterator:
            result.append(page)
        return result

    def _get_tags_and_metrics(self):
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
                metrics.append({"name": value["key"]["value"],
                                "type": self._conver_to_timestream_type(value["type"]["value"])})
        return tags, metrics

    @staticmethod
    def _conver_to_timestream_type(metric_type: str) -> str:
        metric_type = metric_type.lower()
        if metric_type in ["float", "double"]:
            return "DOUBLE"
        elif metric_type in ["bool", "boolean"]:
            return "BOOLEAN"
        elif metric_type in ["int", "long", "uint"]:
            return "BIGINT"
        else:
            return "VARCHAR"

    def _get_model_collection_name(self):
        for key in self.model.keys():
            if key != "description":
                return key

    def prepare_database(self):
        try:
            self.write_client.create_database(DatabaseName=self.database_name)
            print("Database [%s] created successfully." % self.database_name)
        except Exception as err:
            print("Create database failed:", err)

        retention_properties = {
            'MemoryStoreRetentionPeriodInHours': 24,
            'MagneticStoreRetentionPeriodInDays': 7
        }
        try:
            self.write_client.create_table(DatabaseName=self.database_name, TableName=self.table_name,
                                     RetentionProperties=retention_properties)
            print("Table [%s] successfully created." % self.table_name)
        except Exception as err:
            print("Create table failed:", err)