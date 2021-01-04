import psycopg2
import psycopg2.extras
from tictrack import timed_function
from data_generator.db_writer import DbWriter
from datetime import datetime
from datetime_truncate import truncate


class PostgresDbWriter(DbWriter):
    def __init__(self, host: str, port: int, username: str, password: str, db_name: str, model: dict,
                 table_name: str = None, partition: str = "week"):
        super().__init__()
        self.conn = psycopg2.connect(dbname=db_name, user=username, password=password, host=host, port=port)
        self.cursor = self.conn.cursor()
        self.model = model
        self.table_name = (table_name, self._get_model_table_name())[table_name is None or table_name == ""]
        self.partition = partition

    def close_connection(self):
        self.cursor.close()
        self.conn.close()

    def prepare_database(self):
        columns = self._get_tags_and_metrics()
        stmt = f"""CREATE TABLE IF NOT EXISTS {self.table_name} (
ts TIMESTAMP NOT NULL,
ts_{self.partition} TIMESTAMP NOT NULL,
"""
        for key, value in columns.items():
            stmt += f"""{key} {value},"""
        stmt = stmt.rstrip(",") + ");"

        self.cursor.execute(stmt)
        self.conn.commit()

    @timed_function()
    def insert_stmt(self, timestamps: list, batch: list):
        stmt = self._prepare_postgres_stmt(timestamps, batch)
        self.cursor.execute(stmt)
        self.conn.commit()

    @timed_function()
    def _prepare_postgres_stmt(self, timestamps: list, batch: list) -> str:
        columns = self._get_tags_and_metrics().keys()
        stmt = f"""INSERT INTO {self.table_name} (ts, ts_{self.partition},"""
        for column in columns:
            stmt += f"""{column}, """

        stmt = stmt.rstrip(", ") + ") VALUES"
        for i in range(0, len(batch)):
            t = datetime.fromtimestamp(timestamps[i] / 1000)
            trunc = truncate(t, self.partition)
            stmt = f"""{stmt} ('{t}', '{trunc}', """
            for column in columns:
                stmt += f"""'{batch[i][column]}',"""
            stmt = stmt.rstrip(",") + "),"
        stmt = stmt.rstrip(",")
        return stmt

    @timed_function()
    def execute_query(self, query: str) -> list:
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def _get_model_table_name(self) -> str:
        for key in self.model.keys():
            if key != "description":
                return key
