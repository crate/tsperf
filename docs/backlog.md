# Backlog

## Iteration +1
- [o] Documentation: Convert documents to Markdown, and publish to RTD
- [o] Improve OCI image building, using modern recipe
- [o] Bring version numbers up to speed (in docs, for OCI images)
- [o] Query Timer's documentation says MongoDB adapter needs a patch!?

## Iteration +1.5
- [o] Fix typo `stdev`?
- [o] Active voice

## Iteration +2
- [o] Verify functionality on all cloud offerings
- [o] Python PyPI & Docker image release recipes for GHA
- [o] Reflect Docker updates within documentation
- [o] Implement fixed set of queries per use case
- [o] Improve report output

## Iteration +3
- [o] Probe connectivity on Amazon Timestream before invoking workload
- [o] Automatically derive read query from schema, like it already works for MongoDB
- [o] Parallelize using Dask instead of Kubernetes
- [o] Add more databases like CitusDB, PolarDB, CockroachDB, QuestDB(+PostgreSQL,InfluxDB), Yugabyte, Clickhouse, MontyDB
- [o] Emit data to message brokers like MQTT, RabbitMQ, Azure IoTHub, AWS Aurora, ScyllaDB.
- [o] Consolidate names: sensor, device, machine, edge, factory, plant
- [o] Implement parameter validation with Pydantic


## Done
- [x] Rename "model" to "schema".
- [x] Rename "metrics" to "fields".
- [x] Rename "edge" to "channel". A "channel" is comprised of multiple "measurements".
      A "channel" might map to a physical item like a "machine" or "device".
- [x] Make it possible to use built-in schemas.
- [x] MongoDB adapter needs some love
- [x] Add "humidity" to "environment.json" schema
- [x] Rename "db_name" to "database" and "table_name" to "table"
- [x] Migrate all remaining command line parameters
- [x] CrateDB over PostgreSQL protocol
- [x] List schemas: ``tsperf schema --list``
- [x] Fix Docker-related stuff
- [x] Clarify how database / table / collection would be dropped in order to
      recreate it with different shards/partitions/replicas parameters.
- [x] Adjust documentation
- [x] Re-add pyodbc dependency
