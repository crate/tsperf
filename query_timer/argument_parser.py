import argparse
from query_timer.config import QueryTimerConfig

args_info = {
    "database": {
        "help": "Value which defines what database will be used: 0-CrateDB, 1-TimescaleDB, 2-InfluxDB, 3-MongoDB, "
        "4-PostgreSQL, 5-Timestream, 6-MSSQL",
        "choices": range(0, 7),
        "type": int,
    },
    "host": {
        "help": "hostname according to the database client requirements. See documentation for further details:"
        "https://github.com/crate/tsdg/blob/main/DATA_GENERATOR.md#host",
        "choices": [],
        "type": str,
    },
    "username": {
        "help": "username of user used for authentication against the database. Used with CrateDB, TimescaleDB, "
        "MongoDB, Postgresql, MSSQL",
        "choices": [],
        "type": str,
    },
    "password": {
        "help": "password of user used for authentication against the database. used with CrateDB, TimescaleDB, "
        "MongoDB, Postgresql, MSSQL.",
        "choices": [],
        "type": str,
    },
    "db_name": {
        "help": "Name of the database where query will be executed. Used with InfluxDB, TimescaleDB, MongoDB, "
        "AWS Timestream, Postgresql, MSSQL. See the documentation for more details: "
        "https://github.com/crate/tsdg/blob/main/DATA_GENERATOR.md#db-name",
        "choices": [],
        "type": str,
    },
    "port": {
        "help": "Defines the port number of the host where the DB is reachable.",
        "choices": ["1 to 65535"],
        "type": int,
    },
    "token": {
        "help": "token gotten from InfluxDB V2: https://v2.docs.influxdata.com/v2.0/security/tokens/view-tokens/",
        "choices": [],
        "type": str,
    },
    "organization": {
        "help": "org_id gotten from InfluxDB V2: https://v2.docs.influxdata.com/v2.0/organizations/",
        "choices": [],
        "type": str,
    },
    "aws_access_key_id": {"help": "AWS Access Key ID", "choices": [], "type": str},
    "aws_secret_access_key": {
        "help": "AWS Secret Access Key",
        "choices": [],
        "type": str,
    },
    "aws_region_name": {"help": "AWS region name", "choices": [], "type": str},
    "concurrency": {
        "help": "Defines how many threads run in parallel executing queries.",
        "choices": ["1, 2, 3,..."],
        "type": int,
    },
    "iterations": {
        "help": "Defines how many times each thread executes the query.",
        "choices": ["1, 2, 3,..."],
        "type": int,
    },
    "quantiles": {
        "help": "A string which defines which quantiles will be outputted at the end of the run. Values "
        "are separated by ','",
        "choices": ["string in the same format as the default value"],
        "type": str,
    },
    "refresh_rate": {
        "help": "Defines how often the output is refreshed in seconds.",
        "choices": ["x > 0"],
        "type": float,
    },
    "query": {
        "help": "The query that will be timed.",
        "choices": ["A valid query in string format for the chosen database"],
        "type": str,
    },
}


def parse_arguments(config: QueryTimerConfig) -> QueryTimerConfig:  # pragma: no cover
    parser = argparse.ArgumentParser(
        description="Timeseries Database Query Timer - A program to benchmark TSDBs.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    for element in vars(config):
        if element in args_info:
            parser.add_argument(
                f"--{element}",
                type=args_info[element]["type"],
                default=getattr(config, element),
                help=args_info[element]["help"],
                choices=args_info[element]["choices"],
            )

    arguments = parser.parse_args()
    config.load_args(vars(arguments))
    return config
