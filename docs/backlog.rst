##############
tsperf backlog
##############


*******
Backlog
*******


Prio 1
======
- [o] Adjust documentation
- [o] Python PyPI & Docker image release recipes for GHA
- [o] Implement fixed set of queries per use case
- [o] Improve report output
- [o] Implement parameter validation with Pydantic
- [o] Clarify how database / table / collection would be dropped in order to
      recreate it with different shards/partitions/replicas parameters.


Prio 2
======
- [o] Probe connectivity on Amazon Timestream before running job
- [o] Automatically derive read query from schema, like it already works for MongoDB
- [o] Add database service to Docker Compose files?
- [o] Parallelize using Dask
- [o] Add more databases like CitusDB, PolarDB, CockroachDB, QuestDB(+PostgreSQL,InfluxDB), Yugabyte, Clickhouse, MontyDB
- [o] Emit data to message brokers like MQTT, RabbitMQ, Azure IoTHub
- [o] Consolidate names: sensor, device, machine, edge, factory, plant


****
Done
****
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
