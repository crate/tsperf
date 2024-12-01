from modules import helper
from modules.db_writer import DbWriter
from pymongo import MongoClient
from pymongo import CursorType
from datetime import datetime


class MongoDbWriter(DbWriter):
    def __init__(self, host, username, password, database_name, model):
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

    def insert_stmt(self, timestamps, batch):
        data = helper.execute_timed_function(self._prepare_mongo_stmt, timestamps, batch)
        self.collection.insert_many(data)

    def _prepare_mongo_stmt(self, timestamps, batch):
        data = []
        tags, metrics = self._get_tags_and_metrics()
        for i in range(0, len(batch)):
            t = datetime.fromtimestamp(timestamps[i] / 1000)
            document = {"measurement": self._get_model_collection_name(),
                        "date": t,
                        "tags": {},
                        "metrics": {}}
            for tag in tags:
                document["tags"][tag] = batch[i][tag]
            for metric in metrics:
                document["metrics"][metric] = batch[i][metric]
            data.append(document)
        return data

    def execute_query(self, query):
        cursor = self.collection.find(query, cursor_type=CursorType.EXHAUST)
        return list(cursor)

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
                metrics.append(value["key"]["value"])
        return tags, metrics

    def _get_model_collection_name(self):
        for key in self.model.keys():
            if key != "description":
                return key
