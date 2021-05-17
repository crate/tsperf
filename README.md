![Tests](https://github.com/crate/tsdg/workflows/Tests/badge.svg)

# Data Generator

The Data Generator has its own in-depth [documentation](DATA_GENERATOR.md).
For the purpose of capacity testing it simulates the generation of timeseries
data, without the need to set up an ingestion chain (which could be Azure IoTHub, RabbitMQ, etc.)

## Maximizing Performance

To maximize performance multiple instances of the Data Generator must be run in parallel. One way to achieve this is using kubernetes how to do this is documented [here](KUBERNETES.md).

## Setup sandbox
```shell
python3 -m venv .venv
source .venv/bin/activate
pip install --editable=.[testing]
pytest -vvv tests
```
