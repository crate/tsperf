import dataclasses
from typing import Dict

from tsperf.adapter import AdapterManager
from tsperf.model.interface import DatabaseInterfaceType
from tsperf.write.model import IngestMode


@dataclasses.dataclass
class DatabaseConnectionConfiguration:
    # The database interface type.
    adapter: DatabaseInterfaceType

    schema: Dict = None

    # Configuration variables common to multiple databases.
    address: str = None
    username: str = None
    password: str = None
    database: str = None
    table: str = None

    partition: str = "week"

    # The concurrency level.
    concurrency: int = 1

    # Configuration variables for CrateDB.
    shards: int = 4
    replicas: int = 1

    # Configuration variables for InfluxDB.
    influxdb_organization: str = None
    influxdb_token: str = None

    # Configuration variables for TimescaleDB.
    timescaledb_distributed: bool = False
    timescaledb_pgcopy: bool = False

    # Configuration variables for AWS Timestream.
    aws_access_key_id: str = None
    aws_secret_access_key: str = None
    aws_region_name: str = None

    @classmethod
    def create(cls, **options):
        options = enrich_options(options)
        return cls(**options)

    def __post_init__(self):
        pass

    def validate(self):
        if self.adapter is not None:
            if not DatabaseInterfaceType(self.adapter):
                raise Exception(f"Invalid database interface: {self.adapter}")

        if self.address is None:
            adapter = AdapterManager.get(self.adapter)
            self.address = adapter.default_address


def enrich_options(kwargs):
    if "adapter" in kwargs:
        kwargs["adapter"] = DatabaseInterfaceType(kwargs["adapter"])
    if "ingest_mode" in kwargs:
        kwargs["ingest_mode"] = IngestMode(kwargs["ingest_mode"])
    if "debug" in kwargs:
        del kwargs["debug"]
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    return kwargs
