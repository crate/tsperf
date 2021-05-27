![Tests](https://github.com/crate/tsperf/workflows/Tests/badge.svg)

# Data Generator

The Data Generator has a dedicated [documentation page](tsdg/README.md).
For the purpose of capacity testing it simulates the generation of time-series
data, without the need to set up an ingestion chain (which could be Azure IoTHub, RabbitMQ, etc.).

## Maximizing Performance

To maximize performance, multiple instances of the Data Generator must be run in parallel.
How to achieve this using Kubernetes is documented within [KUBERNETES.md](KUBERNETES.md).

## Setup sandbox
```shell
git clone https://github.com/crate/tsperf
cd tsperf
python3 -m venv .venv
source .venv/bin/activate
pip install --editable=.[testing] --upgrade
pytest -vvv tests
```

## Usage

### Generate time series data and feed into database
```shell
# Run CrateDB
docker run -it --rm --publish=4200:4200 --publish=5432:5432 crate/crate:4.5.1

# Feed data into CrateDB
tsdg --model_path=examples/temperature.json --database=0 --host=localhost:4200

# Feed data and expose metrics in Prometheus format
tsdg --model_path=examples/temperature.json --database=0 --host=localhost:4200 --prometheus_enabled
```
