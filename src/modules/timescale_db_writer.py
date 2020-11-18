import psycopg2
import psycopg2.extras
from pgcopy import CopyManager
from modules.db_writer import DbWriter
from modules import helper
from datetime import datetime
from datetime_truncate import truncate


class TimescaleDbWriter(DbWriter):
    def __init__(self, host, port, username, password,
                 ts_db_name, model, table_name=None,
                 partition="week", copy=False):
        super().__init__()
        self.conn = psycopg2.connect(dbname=ts_db_name, user=username, password=password, host=host, port=port)
        self.cursor = self.conn.cursor()
        self.model = model
        self.table_name = (table_name, self._get_model_table_name())[table_name is None or table_name == ""]
        self.partition = partition
        self.copy = copy

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
        stmt = f"""SELECT create_hypertable('{self.table_name}', 'ts', 'ts_{self.partition}', 10, if_not_exists => true); """
        self.cursor.execute(stmt)
        self.conn.commit()

    def insert_stmt(self, timestamps, batch):
        if self.copy:
            helper.execute_timed_function(self._prepare_copy, timestamps, batch)
        else:
            stmt = helper.execute_timed_function(self._prepare_timescale_stmt, timestamps, batch)
            self.cursor.execute(stmt)
        self.conn.commit()

    def _prepare_copy(self, timestamps, batch):
        columns = self._get_tags_and_metrics().keys()
        values = []

        for i in range(0, len(timestamps)):
            t = datetime.fromtimestamp(timestamps[i] / 1000)
            trunc = truncate(t, self.partition)
            data = [t, trunc]
            for column in columns:
                data.append(batch[i][column])
            values.append(data)

        cols = ["ts", f"ts_{self.partition}"]
        for column in columns:
            cols.append(column)
        copy_manager = CopyManager(self.conn, self.table_name, cols)
        copy_manager.copy(values)

    def _prepare_timescale_stmt(self, timestamps, batch):
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

    def execute_query(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def _get_tags_and_metrics(self):
        key = self._get_model_table_name()
        tags = self.model[key]["tags"]
        metrics = self.model[key]["metrics"]
        columns = {}
        for key, value in tags.items():
            if key != "description":
                if type(value) == "list":
                    columns[key] = "TEXT"
                else:
                    columns[key] = "INTEGER"
        for key, value in metrics.items():
            if key != "description":
                columns[value["key"]["value"]] = value["type"]["value"]
        return columns

    def _get_model_table_name(self):
        for key in self.model.keys():
            if key != "description":
                return key
