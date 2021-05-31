##############
tsperf backlog
##############


*******
Backlog
*******

Prio 1
======
- [o] Consolidate names: sensor, device, machine, edge, factory, plant
- [o] Migrate all remaining command line parameters
- [o] Add "humidity" to "environment.json" schema
- [o] CrateDB over PostgreSQL protocol
- [o] List schemas: ``tsperf schema list``
- [o] Probe connectivity on Amazon Timestream before running job

Prio 2
======
- [o] Automatically derive read query from schema
- [o] MongoDB adapter needs some love
- [o] Add database service to Docker Compose files?
- [o] Parallelize using Dask
- [o] Add more databases like CitusDB, PolarDB, CockroachDB, QuestDB, Yugabyte, Clickhouse, MontyDB


****
Done
****
- [x] Rename "model" to "schema".
- [x] Rename "metrics" to "fields".
- [x] Rename "edge" to "channel". A "channel" is comprised of multiple "measurements".
      A "channel" might map to a physical item like a "machine" or "device".
- [x] Make it possible to use built-in schemas.
