# Query Timer

The Query Timer is a tool to invoke queries against databases and measure
its responsiveness.

## Installation

:::{rubric} PyPI package
:::
The *Time Series Query Timer* is part of the `tsperf` package and can be
installed using `pip`.
```shell
pip install tsperf
```

## Usage

By calling `tsperf read --help`, the possible configurations are listed. For
further details, see [Query Timer Configuration](#configuration).
All configurations can be done with either command line arguments or environment
variables, the former are taking precedence.

When calling `tsperf read` with the desired arguments, the Query Timer outputs
live updated statistics on the query execution. This includes:

:::{csv-table} Query Timer Statistics Arguments
"Argument", "Description", "Setting"

concurrency, How many threads are running, [CONCURRENCY](#setting-qt-concurrency)
iterations, How many queries will be done in each thread, [ITERATIONS](#setting-qt-iterations)
progress, Percent of queries done and duration in seconds
time left, How much time is approximately left
rate, How many queries are executed each second on average
mean, The average query duration
stdev, The standard deviation of query execution time from the mean
min, The minimal query duration
max, The maximum query duration
success, How many queries were executed successfully
failure, How many queries were not executed successfully
percentiles, Chosen percentiles from the query execution times, [QUANTILES](#setting-qt-quantiles)
:::

:::{note}
The QueryTimer measures roundtrip times, so the actual
query execution time spent within the database could be less.
:::

### Supported Databases

Currently, 7 databases are supported.

+ [CrateDB](https://crate.io/)
+ [InfluxDB V2](https://www.influxdata.com/)
+ [TimescaleDB](https://www.timescale.com/)
+ [MongoDB](https://www.mongodb.com/)
+ [PostgreSQL](https://www.postgresql.org/)
+ [AWS Timestream](https://aws.amazon.com/timestream/)
+ [Microsoft SQL Server](https://www.microsoft.com/de-de/sql-server)


#### CrateDB

For CrateDB the [crate](https://pypi.org/project/crate/) library is used.
To connect to CrateDB, the following environment variables must be set:

+ [ADDRESS](#setting-qt-address): hostname including port e.g. `localhost:4200`
+ [USERNAME](#setting-qt-username): CrateDB username.
+ [PASSWORD](#setting-qt-password): password for CrateDB user.


#### InfluxDB

For InfluxDB, the [influx-client](https://pypi.org/project/influxdb-client/) library is used.
To connect to InfluxDB, the following environment variables must be set:

+ [ADDRESS](#setting-qt-address): hostname
+ [TOKEN](#setting-qt-token): InfluxDB Read/Write token
+ [ORG](#setting-qt-org): InfluxDB organization

:::{note}
As only InfluxDB V2 is currently supported, queries have to be written in the Flux Query Language.
:::


#### Microsoft SQL Server

For Microsoft SQL Server the [pyodcb](https://github.com/mkleehammer/pyodbc) library is used.
If the Data Generator is run via `pip install` please ensure that `pyodbc` is properly installed on your system.

To connect with Microsoft SQL Server the following environment variables must be set:

+ [ADDRESS](#setting-qt-address): the host where Microsoft SQL Server is running in this [format](https://www.connectionstrings.com/azure-sql-database/)
+ [USERNAME](#setting-qt-username): Database user
+ [PASSWORD](#setting-qt-password): Password of the database user
+ [DATABASE](#setting-qt-database): the database name to connect to or create


#### MongoDB

For MongoDB, the [MongoClient](https://mongodb.github.io/node-mongodb-native/api-generated/mongoclient.html) library is
used.

To connect with MongoDB the following environment variables must be set:

+ [ADDRESS](#setting-qt-address): hostname (can include port if not standard MongoDB port is used)
+ [USERNAME](#setting-qt-username): username of TimescaleDB user
+ [PASSWORD](#setting-qt-password): password of TimescaleDB user
+ [DATABASE](#setting-qt-database): The name of the MongoDB database that will be used

:::{note}
Because `pymongo` does not support queries as string, support for MongoDB is
turned off in the binary. To still use the Query Timer with MongoDB, have a
look at the next documentation section. 
:::

:::{attention}
To use the Query Timer with MongoDB, the code needs to be changed. Therefore,
check out the [repository](https://www.github.com/crate/tsperf).

+ In the file `core.py`, uncomment the import statement of the `MongoDBAdapter`.
+ Also uncomment the instantiation of the `adapter` in the `get_database_adapter` function. 
+ Comment the `ValueError` in the line above.

This should let you start the Query Timer using `ADAPTER` set to MongoDB.

To add the query you want to measure add a variable containing your query to the script and pass this variable to
`adapter.execute_query()` in the `start_query_run` function, instead of `config.query`.

Now, the Query Timer is able to measure query execution times for MongoDB.
:::

:::{todo}
Why make the user need to change the code? Why not just implement the facts above?
:::


#### PostgreSQL

For PostgreSQL the [psycopg2](https://pypi.org/project/psycopg2/) library is used.

To connect with PostgreSQL the following environment variables must be set:

+ [ADDRESS](#setting-qt-address): hostname
+ [USERNAME](#setting-qt-username): username of TimescaleDB user
+ [PASSWORD](#setting-qt-password): password of TimescaleDB user
+ [DATABASE](#setting-qt-database): the database name with which to connect


#### TimescaleDB

For TimescaleDB the [psycopg2](https://pypi.org/project/psycopg2/) library is used.

To connect with TimescaleDB the following environment variables must be set:

+ [ADDRESS](#setting-qt-address): hostname
+ [USERNAME](#setting-qt-username): username of TimescaleDB user
+ [PASSWORD](#setting-qt-password): password of TimescaleDB user
+ [DATABASE](#setting-qt-database): the database name with which to connect


#### Timestream

For AWS Timestream the [boto3](https://github.com/boto/boto3) library is used.

To connect with AWS Timestream the following environment variables must be set:

+ [AWS_ACCESS_KEY_ID](#setting-qt-aws_access_key_id): AWS Access Key ID
+ [AWS_SECRET_ACCESS_KEY](#setting-qt-aws_secret_access_key): AWS Secret Access Key
+ [AWS_REGION_NAME](#setting-qt-aws_region_name): AWS Region
+ [DATABASE](#setting-qt-database): the database name to connect to or create

:::{note}
Tests have shown that queries often fail due to server errors. To accommodate this,
an automatic retry is implemented, that tries to execute the query a second time.
If it fails again the query is marked as failure.
:::
  

(configuration)=
## Configuration

The Query Timer is mostly configured by setting Environment Variables (or command line arguments start with `-h` for
more information). This chapter lists all available Environment Variables and explains their use in the Query Time.

### Database Settings

The environment variables in this chapter are used to configure the behaviour of the Query Timer.

(setting-qt-adapter)=
#### ADAPTER

:Type: String
:Value: `cratedb|timescaledb|influxdb1|influxdb2|mongodb|postgresql|timestream|mssql`

The value will define which database adapter to use:
+ CrateDB
+ TimescaleDB
+ InfluxDB
+ MongoDB
+ PostgreSQL
+ Timestream
+ Microsoft SQL Server

(setting-qt-concurrency)=
#### CONCURRENCY

How many threads are used in parallel to execute queries

:Type: Integer
:Values: Integer bigger 0
:Default: 10

(setting-qt-iterations)=
#### ITERATIONS

How many iterations each thread is doing. 

:Type: Integer
:Value: Integer bigger 0
:Default: 100

(setting-qt-quantiles)=
#### QUANTILES

List of quantiles that will be written to the ouput after the Query Timer finishes

:Type: String
:Value: list of Floats between 0 and 100 split by `,`
:Default: "50,60,75,90,99"

(setting-qt-refresh-interval)=
#### REFRESH_INTERVAL

The time in seconds between updates of the output

:Type: Float
:Value: Any positive float
:Default: 0.1

(setting-qt-query)=
#### QUERY

:Type: String
:Value: A valid Query as string
:Default: ""

(setting-qt-address)=
#### ADDRESS

Type: String

Values: Database address (DSN URI, hostname:port) according to the database client requirements

**CrateDB:**

Host must include port, e.g.: `"localhost:4200"`

**TimescaleDB, Postgresql and InfluxDB:**

Host must be hostname excluding port, e.g.: `"localhost"`

**MongoDB:**

Host can be either without port (e.g. `"localhost"`) or with port (e.g. `"localhost:27017"`)

**MSSQL:**

host must start with `tcp:`

(setting-qt-username)=
#### USERNAME

:Type: String
:Value: username of user used for authentication against the database
:Default: None

used with CrateDB, TimescaleDB, MongoDB, Postgresql, MSSQL.

(setting-qt-password)=
#### PASSWORD

:Type: String
:Value: password of user used for authentication against the database
:Default: None

used with CrateDB, TimescaleDB, MongoDB, Postgresql, MSSQL.

(setting-qt-database)=
#### DATABASE

:Type: String
:Value: Name of the database where table will be created
:Default: empty string

used with TimescaleDB, MongoDB, AWS Timestream, Postgresql, MSSQL.

**TimescaleDB, Postgresql, MSSQL:**
The value of `DATABASE` is used when connecting to TimescaleDB. This database must already exist in your TimescaleDB
instance and must have already been initialized with `CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;`.

**MongoDB:**
The value of `DATABASE` is used as the database parameter of MongoDB.

**AWS Timestream:**
The value of `DATABASE` is used as the database parameter of AWS Timestream.

### InfluxDB Settings

The environment variables in this chapter are only used to configure InfluxDB

(setting-qt-token)=
#### TOKEN

:Type: String
:Value: token gotten from InfluxDB V2
:Default: empty string

Influx V2 uses [token](https://v2.docs.influxdata.com/v2.0/security/tokens/view-tokens/) based authentication.

(setting-qt-org)=
#### ORG

:Type: String
:Value: org_id gotten from InfluxDB V2
:Default: empty string

Influx V2 uses [organizations](https://v2.docs.influxdata.com/v2.0/organizations/) to manage buckets.

### Timestream Settings

The environment variables in this chapter are only used to configure AWS Timestream

(setting-qt-aws_access_key_id)=
#### AWS_ACCESS_KEY_ID

:Type: String
:Value: AWS Access Key ID
:Default: empty string

(setting-qt-aws_secret_access_key)=
#### AWS_SECRET_ACCESS_KEY

:Type: String
:Value: AWS Secret Access Key
:Default: empty string

(setting-qt-aws_region_name)=
#### AWS_REGION_NAME

:Type: String
:Value: AWS region name
:Default: empty string

## Alternative Query Timers

The Query Timer is just a by-product of the Data Generator. There are other
alternatives that offer more features and ways to measure the timing of queries.
The main advantage of the Query Timer is that it supports all Databases that are
also supported by the Data Generator and that it is easy and quick to use.

### cr8

[cr8] is a highly sophisticated tool that offers the possibility to measure query
execution times for CrateDB and other databases using the PostgreSQL protocol.

:::{rubric} Pros
:::
+ **Tracks:** Supports configuring more complex scenarios using .toml files.
+ **Persistence:** Supports saving results to CrateDB directly.
+ **Effective:** With the CrateDB HTTP protocol, the real timings spent within
  the database are measured, not only round-trip times.

:::{rubric} Cons
:::
+ No support for databases not using PostgreSQL protocol.

### JMeter

[JMeter] is a well known and great tool that offers the possibility to measure query
execution times for Databases using JDBC.

:::{rubric} Pros
:::
+ Industry standard for these kinds of tests.
+ Supports export of results to Prometheus.
+ Provides sophisticated settings and configurations to support more complex use cases.

:::{rubric} Cons
:::
+ More complex to set up for simple use cases.


[cr8]: https://github.com/mfussenegger/cr8
[JMeter]: https://jmeter.apache.org/
