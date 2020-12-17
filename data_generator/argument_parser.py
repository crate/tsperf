import argparse
from data_generator.config import DataGeneratorConfig

args_info = {
    "database": {
        "help": "",
        "choices": [0, 1, 2, 3, 4, 5, 6],
        "type": int
    },
    "id_end": {
        "help": "",
        "choices": [],
        "type": int
    },
    "ingest_mode": {
        "help": "",
        "choices": [],
        "type": int
    },
    "ingest_size": {
        "help": "",
        "choices": [],
        "type": int
    },
    "ingest_ts": {
        "help": "",
        "choices": [],
        "type": int
    },
    "ingest_delta": {
        "help": "",
        "choices": [],
        "type": int
    },
    "model_path": {
        "help": "",
        "choices": [],
        "type": int
    },
    "batch_size": {
        "help": "",
        "choices": [],
        "type": int
    },
    "stat_delta": {
        "help": "",
        "choices": [],
        "type": int
    },
    "num_threads": {
        "help": "",
        "choices": [],
        "type": int
    },
    "prometheus_port": {
        "help": "",
        "choices": [],
        "type": int
    },
    "host": {
        "help": "",
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
