from tictrack import timed_function
from data_generator.db_writer import DbWriter
from influxdb_client import InfluxDBClient, Bucket
from influxdb_client.client.write_api import SYNCHRONOUS, Point
from datetime import datetime


class InfluxDbWriter(DbWriter):
    def __init__(self, host, token, org, model, database_name=None):
        super().__init__()
        self.client = InfluxDBClient(url=host, token=token)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
        self.org = org
        self.model = model
        self.bucket = None
        self.database_name = (database_name, self._get_model_database_name())[database_name is None or database_name == ""]

    def close_connection(self):
        self.client.close()

    def prepare_database(self):
        buckets = self.client.buckets_api().find_buckets()
        for bucket in buckets.buckets:
            if bucket.name == self.database_name:
                self.bucket = bucket

        if self.bucket is None:
            bucket = Bucket(name=self.database_name,
                            org_id=self.org,
                            retention_rules=[])
            self.bucket = self.client.buckets_api().create_bucket(bucket)

    @timed_function()
    def insert_stmt(self, timestamps, batch):
        data = self._prepare_influx_stmt(timestamps, batch)
        self.write_api.write(bucket=self.database_name, org=self.org, record=data)

    @timed_function()
    def _prepare_influx_stmt(self, timestamps, batch):
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
    def execute_query(self, query):
        return self.query_api.query(query)

    def _get_tags_and_metrics(self):
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

    def _get_model_database_name(self):
        for key in self.model.keys():
            if key != "description":
                return key
