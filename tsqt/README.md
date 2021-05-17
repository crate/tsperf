# Query Timer

## General Information

This chapter cover general information about the Query Timer, e.g. supported databases and the basic workflow.

### About

The Query Timer is a tool to run queries against different databases and determine how fast the query is.

### How To

#### Pip install

The Query Timer is part of the tsdb-data-generator package and can be installed using `pip install tsperf`.

By calling `tsqt -h` the possible configurations are listed. For further details see
[Query Timer Configuration](#query-timer-configuration). All configurations can be done with either command line
arguments or environment variables but when both are set then command line arguments will be used.

When calling `tsqt` with the desired arguments the Query Timer outputs live updated statistics on the query execution.
This includes:

+ concurrency: how many threads are running, defined by [CONCURRENCY](#concurrency)
+ iterations: how many queries will be done in each thread, defined by [ITERATIONS](#iterations)
+ Progress: Percent of queries done and duration in seconds
+ time left: how much time is approximately left
+ rate: how many queries are executed each second on average
+ mean: the average query duration
+ stdev: the standard deviation of query execution time from the mean
+ min: the minimal query duration
+ max: the maximum query duration
+ success: how many queries were executed successfully
+ failure: how many queries were not executed successfully
+ percentiles: prints all chosen percentiles from the query execution times, defined by [QUANTILES](#quantiles)

**NOTE: the QueryTimer measures roundtrip times so the actual time spent in the database could be less.**

### Supported Databases

Currently 7 Databases are
+ [CrateDB](https://crate.io/)
+ [InfluxDB V2](https://www.influxdata.com/)
+ [TimescaleDB](https://www.timescale.com/)
+ [MongoDB](https://www.mongodb.com/) with limitations see [Using MongoDB](#using-mongodb)
+ [PostgreSQL](https://www.postgresql.org/)
+ [AWS Timestream](https://aws.amazon.com/timestream/)
+ [Microsoft SQL Server](https://www.microsoft.com/de-de/sql-server)

#### CrateDB

##### Client Library

For CrateDB the [crate](https://pypi.org/project/crate/) library is used. To connect to CrateDB the following
environment variables must be set:

+ [HOST](#host): hostname including port e.g. `localhost:4200`
+ [USERNAME](#username): CrateDB username.
+ [PASSWORD](#password): password for CrateDB user.

#### InfluxDB

##### Client Library

For InfluxDB the [influx-client](https://pypi.org/project/influxdb-client/) library is used as the Data Generator only
supports InfluxDB V2. To connect to InfluxDB the following environment variables must be set:

+ [HOST](#host): hostname
+ [TOKEN](#token): InfluxDB Read/Write token
+ [ORG](#org): InfluxDB organization

##### Specifics

+ As only InfluxDB V2 is currently supported queries have to be written in the Flux Query Language.

#### TimescaleDB

##### Client Library

For TimescaleDB the [psycopg2](https://pypi.org/project/psycopg2/) library is used.

To connect with TimescaleDB the following environment variables must be set:

+ [HOST](#host): hostname
+ [PORT](#port): port
+ [USERNAME](#username): username of TimescaleDB user
+ [PASSWORD](#password): password of TimescaleDB user
+ [DB_NAME](#db_name): the database name with which to connect

#### MongoDB

##### Client Library

For MongoDB the [MongoClient](https://mongodb.github.io/node-mongodb-native/api-generated/mongoclient.html) library is
used.

To connect with MongoDB the following environment variables must be set:

+ [HOST](#host): hostname (can include port if not standard MongoDB port is used)
+ [USERNAME](#username): username of TimescaleDB user
+ [PASSWORD](#password): password of TimescaleDB user
+ [DB_NAME](#db_name): The name of the MongoDB database that will be used

##### Specifics

Because `pymongo` does not support queries as string, Support for MongoDB is turned of in the binary. To still use the
Query Timer with Mongo DB have a look at the [Using MongoDB](#using-mongodb) section of this documentation. 

#### PostgreSQL

##### Client Library

For PostgreSQL the [psycopg2](https://pypi.org/project/psycopg2/) library is used.

To connect with PostgreSQL the following environment variables must be set:

+ [HOST](#host): hostname
+ [PORT](#port): port
+ [USERNAME](#username): username of TimescaleDB user
+ [PASSWORD](#password): password of TimescaleDB user
+ [DB_NAME](#db_name): the database name with which to connect

#### AWS Timestream

##### Client Library

For AWS Timestream the [boto3](https://github.com/boto/boto3) library is used.

To connect with AWS Timestream the following environment variables must be set:

+ [AWS_ACCESS_KEY_ID](#aws_access_key_id): AWS Access Key ID
+ [AWS_SECRET_ACCESS_KEY](#aws_secret_access_key): AWS Secret Access Key
+ [AWS_REGION_NAME](#aws_region_name): AWS Region
+ [DB_NAME](#db_name): the database name to connect to or create

##### Specifics

+ Tests have shown that queries often fail due to server errors. To accommodate this an automatic retry is implemented
  that tries to execute the query a second time. If it fails again the query is marked as failure.
  
#### Microsoft SQL Server

##### Client Library

For Microsoft SQL Server the [pyodcb](https://github.com/mkleehammer/pyodbc) library is used.
If the Data Generator is run via `pip install` please ensure that pyodbc is properly installed on your system.

To connect with Microsoft SQL Server the following environment variables must be set:

+ [HOST](#host): the host where Microsoft SQL Server is running in this [format](https://www.connectionstrings.com/azure-sql-database/)
+ [USERNAME](#username): Database user
+ [PASSWORD](#password): Password of the database user
+ [DB_NAME](#db_name): the database name to connect to or create

### Using MongoDB

To use the Query Timer with MongoDB the code of the Query Timer needs to be changed. Therefore checkout the
[repository](https://www.github.com/crate/tsperf). 

+ In the file [tsqt/core.py](tsqt/core.py), uncomment the import statement of the `MongoDBAdapter` 
+ Also uncomment the instantiation of the `adapter` in the `get_database_adapter` function 
+ Comment the `ValueError` in the line above

This should let you start the Query Timer using `DATABASE` set to MongoDB.

To add the query you want to measure add a variable containing your query to the script and pass this variable to
`adapter.execute_query()` in the `start_query_run` function, instead of `config.query`.

Now the Query Timer is able to measure query execution times for MongoDB.

## Query Timer Configuration

The Query Timer is mostly configured by setting Environment Variables (or command line arguments start with `-h` for
more information). This chapter lists all available Environment Variables and explains their use in the Query Time.

### Environment variables configuring the behaviour of the Query Time

The environment variables in this chapter are used to configure the behaviour of the Query Timer

#### DATABASE

Type: Integer

Values: 0..6

Default: 0

The value will define which database is used:
+ 0: CrateDB
+ 1: TimescaleDB
+ 2: InfluxDB
+ 3: MongoDB
+ 4: PostgreSQL
+ 5: Timestream
+ 6: Microsoft SQL Server

#### CONCURRENCY

How many threads are used in parallel to execute queries

Type: Integer

Values: Integer bigger 0

Default: 10

#### ITERATIONS

How many iterations each thread is doing. 

Type: Integer

Values: Integer bigger 0

Default: 100

#### QUANTILES

List of quantiles that will be written to the ouput after the Query Timer finishes

Type: String

Values: list of Floats between 0 and 100 split by `,`

Default: "50,60,75,90,99"

#### REFRESH_RATE

The time in seconds between updates of the output

Type: Float

Values: Any positive float

Default: 0.1

#### QUERY

Type: String

Values: A valid Query as string

Default: ""

#### HOST

Type: String

Values: hostname according to database client requirements

Default: localhost

used with CrateDB, TimescaleDB, InfluxDB, MongoDB, Postgresql, MSSQL.

**CrateDB:**

host must include port, e.g.: `"localhost:4200"`

**TimescaleDB, Postgresql and InfluxDB:**

host must be hostname excluding port, e.g.: `"localhost"`

**MongoDB:**

host can be either without port (e.g. `"localhost"`) or with port (e.g. `"localhost:27017"`)

**MSSQL:**

host must start with `tcp:`

#### USERNAME

Type: String

Values: username of user used for authentication against the database

Default: None

used with CrateDB, TimescaleDB, MongoDB, Postgresql, MSSQL.

#### PASSWORD

Type: String

Values: password of user used for authentication against the database

Default: None

used with CrateDB, TimescaleDB, MongoDB, Postgresql, MSSQL.

#### DB_NAME

Type: String

Values: Name of the database where table will be created

Default: empty string

used with TimescaleDB, MongoDB, AWS Timestream, Postgresql, MSSQL.

**TimescaleDB, Postgresql, MSSQL:**
The value of `DB_NAME` is used when connecting to TimescaleDB. This database must already exist in your TimescaleDB
instance and must have already been initialized with `CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;`.

**MongoDB:**
The value of `DB_NAME` is used as the database parameter of MongoDB.

**AWS Timestream:**
The value of `DB_NAME` is used as the database parameter of AWS Timestream.

#### PORT

Type: Integer

Values: positive number

Default: 5432

Defines the port number of the host where the DB is reachable.

used with TimescaleDB, Postgresql and MSSQL

### Environment variables used to configure InfluxDB

The environment variables in this chapter are only used to configure InfluxDB

#### TOKEN

Type: String

Values: token gotten from InfluxDB V2

Default: empty string

Influx V2 uses [token](https://v2.docs.influxdata.com/v2.0/security/tokens/view-tokens/) based authentication.

#### ORG

Type: String

Values: org_id gotten from InfluxDB V2

Default: empty string

Influx V2 uses [organizations](https://v2.docs.influxdata.com/v2.0/organizations/) to manage buckets.

### Environment variables used to configure AWS Timestream

The environment variables in this chapter are only used to configure AWS Timestream

#### AWS_ACCESS_KEY_ID

Type: String

Values: AWS Access Key ID

Default: empty string

#### AWS_SECRET_ACCESS_KEY

Type: String

Values: AWS Secret Access Key

Default: empty string

#### AWS_REGION_NAME

Type: String

Values: AWS region name

Default: empty string

## Alternative Query Timers

As the Query Timer is just a by-product of the Data Generator there are other alternatives that offer more features and
ways to time queries. The main advantage of the Query Timer is that it supports all Databases that are also supported by
the Data Generator and is easy and fast to use.

### cr8

[cr8](https://github.com/mfussenegger/cr8) is a highly sophisticated tool that offers the possibility to measure query
execution times for CrateDB and other databases using the PostgreSQL protocol.

Pros:

+ Offers support for .toml files to configure more complex scenarios.
+ Offers saving results to CrateDB directly
+ For CrateDB only the real DB-time is measured (when not using the postgres port)

Cons:

+ No support for databases not using PostgreSQL protocol

### JMeter

[Jmeter](https://jmeter.apache.org/) is a well known and great tool that offers the possibility to measure query
execution times for Databases using JDBC.

Pros: 

+ Industry standard for these kinds of tests
+ Offers Prometheus export of results
+ Offers more sophisticated settings and configurations to support more complicated use cases

Cons:

+ More complex to setup for simple use cases
