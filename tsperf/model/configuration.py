import dataclasses
import os


@dataclasses.dataclass
class DatabaseConnectionConfiguration:

    # The database interface type.
    database: int = None

    # Configuration variables common to multiple databases.
    host: str = None
    port: str = None
    username: str = None
    password: str = None
    db_name: str = None
    table_name: str = None
    partition: str = None

    # Configuration variables for CrateDB.
    shards: int = None
    replicas: int = None

    def __post_init__(self):
        self.database = (
            self.database is not None
            and int(self.database)
            or int(os.getenv("DATABASE", 0))
        )
        self.host = self.host or os.getenv("HOST", "localhost")
        self.port = self.port or os.getenv("PORT", None)
        self.username = self.username or os.getenv("USERNAME", None)
        self.password = self.password or os.getenv("PASSWORD", None)
        self.db_name = self.db_name or os.getenv("DB_NAME", "")
        self.table_name = self.table_name or os.getenv("TABLE_NAME", "")
        self.partition = self.partition or os.getenv("PARTITION", "week")

        self.shards = (
            self.shards is not None and int(self.shards) or int(os.getenv("SHARDS", 4))
        )
        if self.replicas is None:
            self.replicas = int(os.getenv("REPLICAS", 1))
        else:
            self.replicas = int(self.replicas)
