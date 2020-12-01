import pyodbc
from tictrack import timed_function
from modules.db_writer import DbWriter
from datetime import datetime
from datetime_truncate import truncate


class MsSQLDbWriter(DbWriter):
    def __init__(self, host, username, password, db_name, model, port=1433, table_name=None):
        super().__init__()
        driver = '{ODBC Driver 17 for SQL Server}'
        self.conn = pyodbc.connect(f"DRIVER={driver};SERVER={host};PORT={port};DATABASE={db_name};UID={username};PWD={password}")
        self.cursor = self.conn.cursor()
        self.model = model
        self.table_name = (table_name, self._get_model_table_name())[table_name is None or table_name == ""]

    def prepare_database(self):
        columns = self._get_tags_and_metrics()
        stmt = f"""
IF NOT EXISTS (SELECT * FROM sysobjects WHERE id = object_id(N'{self.table_name}')
AND OBJECTPROPERTY(id, N'IsUserTable') = 1) CREATE TABLE {self.table_name} (
ts DATETIME NOT NULL,
"""
        for key, value in columns.items():
            stmt += f"""{key} {value},"""
        stmt = stmt.rstrip(",") + ");"

        self.cursor.execute(stmt)
        self.conn.commit()

    @timed_function()
    def insert_stmt(self, timestamps, batch):
        stmt, params = self._prepare_mssql_stmt(timestamps, batch)
        self.cursor.executemany(stmt, params)
        self.conn.commit()

    @timed_function()
    def _prepare_mssql_stmt(self, timestamps, batch):
        columns = self._get_tags_and_metrics().keys()
        stmt = f"""INSERT INTO {self.table_name} (ts ,"""
        for column in columns:
            stmt += f"""{column}, """

        stmt = stmt.rstrip(", ") + ") VALUES (?, "

        for column in columns:
            stmt += "?, "

        stmt = stmt.rstrip(", ") + ")"

        params = []
        for i in range(0, len(batch)):
            t = datetime.fromtimestamp(timestamps[i] / 1000)
            row = [t]
            for column in columns:
                row.append(batch[i][column])
            params.append(row)
        return stmt, params

    @timed_function()
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
                columns[key] = "INTEGER"
        for key, value in metrics.items():
            if key != "description":
                if value["type"]["value"] == "BOOL":
                    columns[value["key"]["value"]] = "BIT"
                else:
                    columns[value["key"]["value"]] = value["type"]["value"]
        return columns

    def _get_model_table_name(self):
        for key in self.model.keys():
            if key != "description":
                return key
