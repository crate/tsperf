# Changelog

## Unreleased

## 2024/05/21 1.2.1
- Fix documentation flaw in README

## 2024/05/21 1.2.0
- Refactored modules
- Naming things
- Improved logging
- Improved exception handling
- Added progress bar for long-running operations
- Disabled Prometheus metrics export by default
- Provided default port per database
- Included schema files into Python package
- Improved database adapter subsystem
- Fixed database adapter lifecycle
- Adjusted default concurrency settings
- Unlocked database adapters MongoDB, MSSQL, PostgreSQL, TimescaleDB, and Timestream
- Added `humidity` to `environment.json` schema
- Fixed connection to MongoDB Atlas
- Improved data lifecycle: Drop table before recreating it with different parameters
- Relocated OCI image to `ghcr.io/crate/tsperf`
- Fixed InfluxDB adapter: Forward organization name to InfluxDB driver
- Updated dependencies
- Improved documentation
- Published documentation: https://tsperf.readthedocs.io/
- CI: Improved OCI image building by staging images to GHCR, using GHA

## 2021/05/17 1.1.0
- Refactoring
