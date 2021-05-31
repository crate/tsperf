##############
tsperf backlog
##############


*******
Backlog
*******


Prio 1
======
- [o] Consolidate names: sensor, device, machine, edge, factory, plant
- [o] Rename "db_name" to "database" and "table_name" to "table"?
- [o] Migrate all remaining command line parameters
- [o] Add "humidity" to "environment.json" schema
- [o] CrateDB over PostgreSQL protocol
- [o] List schemas: ``tsperf schema list``
- [o] Probe connectivity on Amazon Timestream before running job
- [o] Fix Docker-related stuff
- [o] Adjust documentation
- [o] Python PyPI & Docker image release recipes for GHA
- [o] Implement fixed set of queries per use case
- [o] Improve report output


Prio 2
======
- [o] Automatically derive read query from schema, like it already works for MongoDB
- [o] Add database service to Docker Compose files?
- [o] Parallelize using Dask
- [o] Add more databases like CitusDB, PolarDB, CockroachDB, QuestDB(+PostgreSQL,InfluxDB), Yugabyte, Clickhouse, MontyDB
- [o] Emit data to message brokers like MQTT, RabbitMQ, Azure IoTHub


****
Done
****
- [x] Rename "model" to "schema".
- [x] Rename "metrics" to "fields".
- [x] Rename "edge" to "channel". A "channel" is comprised of multiple "measurements".
      A "channel" might map to a physical item like a "machine" or "device".
- [x] Make it possible to use built-in schemas.
- [x] MongoDB adapter needs some love
