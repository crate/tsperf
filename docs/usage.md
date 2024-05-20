# Usage

This section outlines the usage of `tsperf` on different databases. Please note
that using Docker here is just for demonstration purposes. In reality, you will
want to run the database workload against a dedicated database instance running
on a decently powered machine.

- For increasing concurrency, try `--concurrency=8`.
- For enabling Prometheus metrics export, try `--prometheus-enable=true`
  and maybe `--prometheus-listen=0.0.0.0:8000`.
- For increasing concurrency and number of iterations when querying,
  try `--concurrency=10 --iterations=2000`.
- For displaying the list of built-in schemas, run `tsperf schema --list`.


## CrateDB
```shell
# Run CrateDB
docker run -it --rm --publish=4200:4200 --publish=5432:5432 crate:4.5.1

# Feed data into CrateDB table.
# Adjust write parameters like `--partition=day --shards=6 --replicas=3`.
tsperf write --adapter=cratedb --schema=tsperf.schema.basic:environment.json
tsperf write --adapter=cratedb --schema=tsperf.schema.basic:environment.json --address=cratedb.example.org:4200

# Query data from CrateDB table.
tsperf read --adapter=cratedb --query="SELECT * FROM environment LIMIT 10;"
```

Alternatively, use Docker.
```shell
alias tsperf="docker run --rm -it --network=host ghcr.io/crate/tsperf tsperf"
tsperf write --adapter=cratedb --schema=tsperf.schema.basic:environment.json
tsperf read --adapter=cratedb --query="SELECT * FROM environment LIMIT 10;"
```

## CrateDB+PostgreSQL
```shell
# Run CrateDB workload via PostgreSQL protocol.
tsperf write --adapter=cratedbpg --schema=tsperf.schema.basic:environment.json
tsperf read --adapter=cratedbpg --iterations=3000 --query="SELECT * FROM environment LIMIT 10;"

# Run PostgreSQL workload on CrateDB.
tsperf write --adapter=postgresql --schema=tsperf.schema.basic:environment.json
tsperf read --adapter=postgresql --username=crate --iterations=3000 --query="SELECT * FROM environment LIMIT 10;"
```

## InfluxDB
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

On InfluxDB Cloud, after generating an "All Access Token", configure `tsperf` like:
```shell
export ADAPTER=influxdb
export ADDRESS="https://eu-central-1-1.aws.cloud2.influxdata.com/"
export INFLUXDB_ORGANIZATION=a05test6edtest2d
export INFLUXDB_TOKEN="wpNtestfeNUveYitDLk8Ld47vrSVUTKB_vEaEwWC7qXj_ZqvOwYCRhQTB4EDty3uLFMXWP2C195gtestt4XGFQ=="
```

## Microsoft SQL Server
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

## MongoDB
```shell
# Run and configure MongoDB
docker run -it --rm --publish=27017:27017 mongo:4.4

# Feed data into MongoDB collection.
tsperf write --adapter=mongodb --schema=tsperf.schema.basic:environment.json

# Query data from MongoDB collection.
tsperf read --adapter=mongodb --schema=tsperf.schema.basic:environment.json

# For connecting to MongoDB Atlas, use:
export ADDRESS="mongodb+srv://username:password@testdrive.fkpkw.mongodb.net/tsperf?retryWrites=true&w=majority"
```

## PostgreSQL
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

## TimescaleDB
```shell
# Run TimescaleDB
docker run -it --rm --env="POSTGRES_HOST_AUTH_METHOD=trust" --publish=5432:5432 timescale/timescaledb:2.3.0-pg13

# Configure tsperf
export ADAPTER=timescaledb

# Feed data into TimescaleDB hypertable.
# Adjust write parameters like `--timescaledb-distributed --timescaledb-pgcopy`.
tsperf write --schema=tsperf.schema.basic:environment.json

# Query data from TimescaleDB hypertable.
tsperf read --iterations=3000 --query="SELECT * FROM environment LIMIT 10;"
```

## Timestream
```shell
# Run Timestream

# There is no way to run Amazon Timestream on premises.
# - https://aws.amazon.com/timestream/
# - https://docs.aws.amazon.com/timestream/

# Configure tsperf
export ADAPTER=timestream
export ADDRESS=ingest-cell1.timestream.us-west-2.amazonaws.com
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export AWS_REGION_NAME=us-west-2

# Feed data into Timestream table.
tsperf write --schema=tsperf.schema.basic:environment.json

# Query data from Timestream table.
tsperf read --iterations=3000 --query="SELECT * FROM environment LIMIT 10;"
```
