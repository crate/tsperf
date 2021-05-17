![Tests](https://github.com/crate/tsdg/workflows/Tests/badge.svg)

# Data Generator

The Data Generator has a dedicated [documentation page](tsdg/README.md).
For the purpose of capacity testing it simulates the generation of time-series
data, without the need to set up an ingestion chain (which could be Azure IoTHub, RabbitMQ, etc.).

## Maximizing Performance

To maximize performance, multiple instances of the Data Generator must be run in parallel.
How to achieve this using Kubernetes is documented within [KUBERNETES.md](KUBERNETES.md).

## Setup sandbox
```shell
python3 -m venv .venv
source .venv/bin/activate
pip install --editable=.[testing] --upgrade
pytest -vvv tests
```
