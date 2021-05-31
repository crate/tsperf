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
make test
source .venv/bin/activate
```

## Usage

- Data generator: Generate time series data and feed it into database.
  Use `tsperf write --help` to explore its options.
- Query Timer: Probe responsiveness of database on the read path.
  Use `tsperf read --help` to explore its options.


### CrateDB
```shell
# Run CrateDB
docker run -it --rm --publish=4200:4200 --publish=5432:5432 crate:4.5.1

# Feed data into CrateDB table.
tsperf write --adapter=cratedb --schema=tsperf.schema.basic:environment.json

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


### Microsoft SQL Server
```shell
# Run Microsoft SQL Server
docker run -it --rm --publish=1433:1433 --env="ACCEPT_EULA=Y" --env="SA_PASSWORD=yayRirr3" mcr.microsoft.com/mssql/server:2019-latest
docker exec -it aeba7fdd4d73 /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P yayRirr3 -Q "select @@Version"

# Install the Microsoft ODBC driver for SQL Server
- Visit: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

# Configure tsperf
export ADAPTER=mssql

# Feed data into MSSQL table.
tsperf write --schema=tsperf.schema.basic:environment.json

# Query data from MSSQL table.
tsperf read --iterations=3000 --query="SELECT TOP 10 * FROM environment;"
```


### MongoDB
```shell
# Run and configure MongoDB
docker run -it --rm --publish=27017:27017 mongo:4.4

# Feed data into MongoDB collection.
tsperf write --adapter=mongodb --schema=tsperf.schema.basic:environment.json

# Query data from MongoDB collection.
tsperf read --adapter=mongodb --schema=tsperf.schema.basic:environment.json
```


### PostgreSQL
```shell
# Run PostgreSQL
docker run -it --rm --env="POSTGRES_HOST_AUTH_METHOD=trust" --publish=5432:5432 postgres:13.3

# Configure tsperf
export ADAPTER=postgresql

# Feed data into PostgreSQL table.
tsperf write --schema=tsperf.schema.basic:environment.json

# Query data from PostgreSQL table.
tsperf read --iterations=3000 --query="SELECT * FROM environment LIMIT 10;"
```


### TimescaleDB
```shell
# Run PostgreSQL
docker run -it --rm --env="POSTGRES_HOST_AUTH_METHOD=trust" --publish=5432:5432 timescale/timescaledb:2.3.0-pg13

# Configure tsperf
export ADAPTER=timescaledb

# Feed data into TimescaleDB hypertable.
tsperf write --schema=tsperf.schema.basic:environment.json
tsperf write --schema=tsperf.schema.basic:environment.json --timescaledb-distributed
tsperf write --schema=tsperf.schema.basic:environment.json --timescaledb-pgcopy

# Query data from TimescaleDB hypertable.
tsperf read --iterations=3000 --query="SELECT * FROM environment LIMIT 10;"
```


### Timestream
```shell
# Run Timestream

# There is no way to run Amazon Timestream on premises.
# - https://aws.amazon.com/timestream/
# - https://docs.aws.amazon.com/timestream/

# Configure tsperf
export ADAPTER=timestream
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export AWS_REGION_NAME=us-west-2

# Feed data into Timestream table.
tsperf write --schema=tsperf.schema.basic:environment.json

# Query data from Timestream table.
tsperf read --iterations=3000 --query="SELECT * FROM environment LIMIT 10;"
```
