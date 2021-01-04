class DbWriter:
    def __init__(self):
        pass

    def connect_to_database(self):  # pragma: no cover
        pass

    def close_connection(self):  # pragma: no cover
        pass

    def prepare_database(self):  # pragma: no cover
        pass

    def insert_stmt(self, timestamps: list, batch: list):  # pragma: no cover
        pass

    def execute_query(self, query: str):  # pragma: no cover
        pass

    def _get_tags_and_metrics(self):
        key = self._get_model_table_name()
        tags = self.model[key]["tags"]
        metrics = self.model[key]["metrics"]
        columns = {}
        for key, value in tags.items():
            if key != "description":
                if type(value).__name__ == "list":
                    columns[key] = "TEXT"
                else:
                    columns[key] = "INTEGER"
        for key, value in metrics.items():
            if key != "description":
                columns[value["key"]["value"]] = value["type"]["value"]
        return columns
