import os
import shutil
from argparse import Namespace


class QueryTimerConfig:
    def __init__(self):
        # environment variables describing how the query_timer behaves
        self.database = int(os.getenv("DATABASE", 0))
        self.concurrency = int(os.getenv("CONCURRENCY", 10))
        self.iterations = int(os.getenv("ITERATIONS", 100))
        self.quantiles = os.getenv("QUANTILES", "50,60,75,90,99").split(",")
        self.refresh_rate = float(os.getenv("REFRESH_RATE", 0.1))
        self.query = os.getenv("QUERY", "")

        # environment variables used by multiple database clients
        self.host = os.getenv("HOST", "localhost")
        self.username = os.getenv("USERNAME", None)
        self.password = os.getenv("PASSWORD", None)
        self.db_name = os.getenv("DB_NAME", "")
        self.port = os.getenv("PORT", "5432")

        # environment variables to connect to influxdb
        self.token = os.getenv("TOKEN", "")
        self.organization = os.getenv("ORG", "")

        # environment variable to connect to aws timestream
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.aws_region_name = os.getenv("AWS_REGION_NAME", "")

        self.invalid_configs = []

    def validate_config(self) -> bool:  # noqa
        if self.database not in [0, 1, 2, 3, 4, 5, 6]:
            self.invalid_configs.append(
                f"DATABASE: {self.database} not 0, 1, 2, 3, 4, 5 or 6"
            )
        if int(self.port) <= 0:
            self.invalid_configs.append(f"PORT: {self.port} <= 0")
        if self.concurrency * self.iterations < 100:
            self.invalid_configs.append(
                f"CONCURRENCY: {self.concurrency}; ITERATIONS: {self.iterations}. At least "
                f"100 queries must be run. The current configuration results "
                f"in {self.concurrency * self.iterations} queries (concurrency * iterations)"
            )
        terminal_size = shutil.get_terminal_size()
        if len(self.quantiles) > terminal_size.lines - 12:
            self.invalid_configs.append(
                f"QUANTILES: {self.quantiles}; TERMINAL_LINES: {terminal_size.lines}. "
                f"QueryTimer needs a bigger terminal (at least {len(self.quantiles) + 12}) "
                f"to display all results. Please increase "
                f"terminal size or reduce number of quantiles."
            )

        return len(self.invalid_configs) == 0

    def load_args(self, args: Namespace):
        for element in vars(self):
            if element in args:
                setattr(self, element, args[element])
