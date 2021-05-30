import dataclasses
import os
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
    db_name: str = None
    table_name: str = None
    partition: str = None

    # The concurrency level.
    concurrency: int = 2

    # Configuration variables for CrateDB.
    shards: int = 4
    replicas: int = 1

    @classmethod
    def create(cls, **options):
        options = enrich_options(options)
        return cls(**options)

    def __post_init__(self):
        self.username = self.username or os.getenv("USERNAME", None)
        self.password = self.password or os.getenv("PASSWORD", None)
        self.db_name = self.db_name or os.getenv("DB_NAME", "")
        self.table_name = self.table_name or os.getenv("TABLE_NAME", "")
        self.partition = self.partition or os.getenv("PARTITION", "week")

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
