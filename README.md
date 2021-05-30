![Tests](https://github.com/crate/tsperf/workflows/Tests/badge.svg)

# Data Generator

The Data Generator has a dedicated [documentation page](tsperf/write/README.md).
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

- Data generator: Generate time series data and feed it into database.
- Query Timer: Probe responsiveness of database on the read path.


### CrateDB
```shell
# Run CrateDB
docker run -it --rm --publish=4200:4200 --publish=5432:5432 crate/crate:4.5.1

# Feed data into CrateDB table.
tsperf write --schema=tsperf.schema.basic:environment.json --adapter=cratedb

# Query data from CrateDB table.
tsperf read --adapter=cratedb --query="SELECT * FROM environment LIMIT 10;"
```

```shell
# Increase concurrency
tsperf write --schema=tsperf.schema.basic:environment.json --adapter=cratedb --concurrency=8

# Feed data into CrateDB running on a remote address
tsperf write --schema=tsperf.schema.basic:environment.json --adapter=cratedb --address=cratedb.example.org:4200

# Feed data and expose metrics in Prometheus format
tsperf write --schema=tsperf.schema.basic:environment.json --adapter=cratedb --prometheus-enable=true
tsperf write --schema=tsperf.schema.basic:environment.json --adapter=cratedb --prometheus-enable=true --prometheus-listen=0.0.0.0:8000

# Increase concurrency and number of iterations when querying.
tsperf read --adapter=cratedb --concurrency=10 --iterations=2000
```


### InfluxDB
```shell
# Run and configure InfluxDB
docker run -it --rm --publish=8086:8086 influxdb:2.0
influx setup --name=default --username=root --password=12345678 --org=acme --bucket=environment --retention=0 --force
cat /Users/amo/.influxdbv2/configs

# Configure tsperf
export ADAPTER=influxdb
export ADDRESS=http://localhost:8086/
export INFLUXDB_ORGANIZATION=acme
export INFLUXDB_TOKEN="X1kHPaXvS...p1IAQ=="
 
# Feed data into InfluxDB bucket.
tsperf write --schema=tsperf.schema.basic:environment.json

# Query data from InfluxDB bucket.
tsperf read --query='from(bucket:"environment") |> range(start:-2h, stop:2h) |> limit(n: 10)'
```
