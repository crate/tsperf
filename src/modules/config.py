import os
import time
import os.path


class DataGeneratorConfig:
    def __init__(self):
        # environment variables describing how the data_generator behaves
        self.id_start = int(os.getenv("ID_START", 1))
        self.id_end = int(os.getenv("ID_END", 500))
        self.ingest_mode = int(os.getenv("INGEST_MODE", 1))
        self.ingest_size = int(os.getenv("INGEST_SIZE", 1000))
        self.ingest_ts = float(os.getenv("INGEST_TS", time.time()))
        self.ingest_delta = float(os.getenv("INGEST_DELTA", 0.5))
        self.model_path = os.getenv("MODEL_PATH", "")
        self.batch_size = int(os.getenv("BATCH_SIZE", -1))
        self.database = int(os.getenv("DATABASE", 0))  # 0:crate, 1:timescale, 2:influx, 3:mongo
        self.stat_delta = int(os.getenv("STAT_DELTA", 30))

        # environment variables used by multiple database clients
        self.host = os.getenv("HOST", "localhost")
        self.username = os.getenv("USERNAME", None)
        self.password = os.getenv("PASSWORD", None)
        self.db_name = os.getenv("DB_NAME", "")
        self.table_name = os.getenv("TABLE_NAME", "")
        self.partition = os.getenv("PARTITION", "week")

        # environment variables to configure cratedb
        self.shards = int(os.getenv("SHARDS", 4))
        self.replicas = int(os.getenv("REPLICAS", 0))

        # environment variables to configure timescaledb
        self.port = os.getenv("PORT", "5432")

        # environment variables to connect to influxdb
        self.token = os.getenv("TOKEN", "")
        self.organization = os.getenv("ORG", "")
        self.invalid_configs = []

        # environment variable to connect to aws timestream
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.aws_region_name = os.getenv("AWS_REGION_NAME", "")

    def validate_config(self) -> bool:
        if self.id_start < 0:
            self.invalid_configs.append(f"ID_START: {self.id_start} < 0")
        if self.id_end < 0:
            self.invalid_configs.append(f"ID_END: {self.id_end} < 0")
        if self.id_end < self.id_start:
            self.invalid_configs.append(f"ID_START: {self.id_start} > ID_END: {self.id_end}")
        if self.ingest_mode not in [0, 1]:
            self.invalid_configs.append(f"INGEST_MODE: {self.ingest_mode} not 0 or 1")
        if self.ingest_size < 0:
            self.invalid_configs.append(f"INGEST_SIZE: {self.ingest_size} < 0")
        if self.ingest_ts < 0:
            self.invalid_configs.append(f"INGEST_TS: {self.ingest_ts} < 0")
        if self.ingest_delta <= 0:
            self.invalid_configs.append(f"INGEST_DELTA: {self.ingest_delta} <= 0")
        if not os.path.isfile(self.model_path):
            self.invalid_configs.append(f"MODEL_PATH: {self.model_path} does not exist")
        if self.database not in [0, 1, 2, 3, 4, 5]:
            self.invalid_configs.append(f"DATABASE: {self.database} not 0, 1, 2, 3 or 4")
        if self.stat_delta <= 0:
            self.invalid_configs.append(f"STAT_DELTA: {self.stat_delta} <= 0")
        if self.partition.lower() not in ["second", "minute", "hour", "day", "week", "month", "quarter", "year"]:
            self.invalid_configs.append(f"PARTITION: {self.partition} not one of second, minute, hour, day, week, "
                                        f"month, quarter or year")
        if self.shards <= 0:
            self.invalid_configs.append(f"SHARDS: {self.shards} <= 0")
        if self.replicas < 0:
            self.invalid_configs.append(f"REPLICAS: {self.replicas} < 0")
        if int(self.port) <= 0:
            self.invalid_configs.append(f"PORT: {self.port} <= 0")

        return len(self.invalid_configs) == 0
