import argparse
from data_generator.config import DataGeneratorConfig

args_info = {
    "database": {
        "help": "Value which defines what database will be used: 0-CrateDB, 1-TimescaleDB, 2-InfluxDB, 3-MongoDB, "
                "4-PostgreSQL, 5-Timestream, 6-MSSQL",
        "choices": range(0, 7),
        "type": int
    },
    "id_start": {
        "help": "The Data Generator will create `(id_end + 1) - id_start` edges. Must be smaller or equal to id_end.",
        "choices": ["1, 2, 3, ..."],
        "type": int
    },
    "id_end": {
        "help": "The Data Generator will create `(id_end + 1) - id_start` edges. Must be bigger or equal to id_start.",
        "choices": ["1, 2, 3, ..."],
        "type": int
    },
    "ingest_mode": {
        "help": "The ingest_mode argument turns on fast insert when set to True or switches to consecutive inserts "
                "when set to False. For more information read the documentation ("
                "https://github.com/crate/ts-data-generator/blob/master/DATA_GENERATOR.md#ingest_mode)",
        "choices": [True, False],
        "type": bool
    },
    "ingest_size": {
        "help": "This argument defines how many values per edge will be created. If set to 0 an endless amount of "
                "values will be created.",
        "choices": ["0, 1, 2, 3, ..."],
        "type": int
    },
    "ingest_ts": {
        "help": "The starting timestamp of the generated data. If not provided will be the timestamp when the Data "
                "Generator has been started.",
        "choices": ["A valid UNIX timestamp"],
        "type": int
    },
    "ingest_delta": {
        "help": "This values defines the interval between timestamps of generated values. With `ingest_mode = False` "
                "This is the actual time between inserts.",
        "choices": ["Any positive number"],
        "type": float
    },
    "model_path": {
        "help": "A relative or absolute path to a model in the json format (see the data generator documentation for "
                "more details: https://github.com/crate/ts-data-generator/blob/master/DATA_GENERATOR.md#data"
                "-generator-models)",
        "choices": ["Absolute or relative file path"],
        "type": str
    },
    "batch_size": {
        "help": "The batch size used when ingest_mode is set to True. A value smaller or equal to 0 in combination "
                "with ingest_mode turns on auto batch mode using the batch-size-automator library: "
                "https://pypi.org/project/batch-size-automator/",
        "choices": ["Any integer number"],
        "type": int
    },
    "stat_delta": {
        "help": "Time in seconds that is waited between statistic outputs to the log",
        "choices": ["number > 0"],
        "type": float
    },
    "num_threads": {
        "help": "The number of python-threads used for inserting values",
        "choices": ["integer > 0 but 1-4 advised"],
        "type": int
    },
    "prometheus_port": {
        "help": "The port that is used to publish prometheus metrics",
        "choices": ["1 to 65535"],
        "type": int
    },
    "host": {
        "help": "hostname according to the database client requirements",
        "choices": [],
        "type": int
    },
    "username": {
        "help": "",
        "choices": [],
        "type": int
    },
    "password": {
        "help": "",
        "choices": [],
        "type": int
    },
    "db_name": {
        "help": "",
        "choices": [],
        "type": int
    },
    "table_name": {
        "help": "",
        "choices": [],
        "type": int
    },
    "partition": {
        "help": "",
        "choices": [],
        "type": int
    },
    "shards": {
        "help": "",
        "choices": [],
        "type": int
    },
    "replicas": {
        "help": "",
        "choices": [],
        "type": int
    },
    "port": {
        "help": "",
        "choices": [],
        "type": int
    },
    "copy": {
        "help": "",
        "choices": [],
        "type": int
    },
    "distributed": {
        "help": "",
        "choices": [],
        "type": int
    },
    "token": {
        "help": "",
        "choices": [],
        "type": int
    },
    "organization": {
        "help": "",
        "choices": [],
        "type": int
    },
    "aws_access_key_id": {
        "help": "",
        "choices": [],
        "type": int
    },
    "aws_secret_access_key": {
        "help": "",
        "choices": [],
        "type": int
    },
    "aws_region_name": {
        "help": "",
        "choices": [],
        "type": int
    },

}


def parse_arguments(config: DataGeneratorConfig):
    parser = argparse.ArgumentParser(description="Timeseries Database Data Generator - A program to benchmark TSDBs.")

    for element in vars(config):
        if element in args_info:
            parser.add_argument(f"--{element}",
                                type=args_info[element]["type"],
                                default=getattr(config, element),
                                help=args_info[element]["help"],
                                choices=args_info[element]["choices"])

    arguments = parser.parse_args()
    config.load_args(vars(arguments))
