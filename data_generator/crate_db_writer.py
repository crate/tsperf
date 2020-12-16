from data_generator.db_writer import DbWriter
from crate import client
from tictrack import timed_function


class CrateDbWriter(DbWriter):
    def __init__(self, host, username, password, model, table_name=None, shards=None, replicas=None, partition="week"):
        super().__init__()
        self.conn = client.connect(host, username=username, password=password)
        self.cursor = self.conn.cursor()
        self.model = model
        self.table_name = (table_name, self._get_model_table_name())[table_name is None or table_name == ""]
        self.shards = (shards, 21)[shards is None]
        self.replicas = (replicas, 1)[replicas is None]
        self.partition = partition

    def close_connection(self):
        self.cursor.close()
        self.conn.close()

    def prepare_database(self):
        stmt = f"""CREATE TABLE IF NOT EXISTS {self.table_name} ("ts" TIMESTAMP WITH TIME ZONE,
"g_ts_{self.partition}" TIMESTAMP WITH TIME ZONE GENERATED ALWAYS AS date_trunc('{self.partition}', "ts"), 
"payload" OBJECT(DYNAMIC))
CLUSTERED INTO {self.shards} SHARDS
PARTITIONED BY ("g_ts_{self.partition}")
WITH (number_of_replicas = {self.replicas})"""
        self.cursor.execute(stmt)

    @timed_function()
    def insert_stmt(self, timestamps, batch):
        stmt = f"""INSERT INTO {self.table_name} (ts, payload) (SELECT col1, col2 FROM UNNEST(?,?))"""
        self.cursor.execute(stmt, (timestamps, batch))

    @timed_function()
    def execute_query(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def _get_model_table_name(self):
        for key in self.model.keys():
            if key != "description":
                return key
