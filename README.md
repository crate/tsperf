# TSPERF Time Series Database Benchmark Suite

TSPERF is a tool for evaluating and comparing the performance of time series databases,
in the spirit of TimescaleDB's Time Series Benchmark Suite (TSBS). 

» [Documentation]
| [Changelog]
| [PyPI]
| [Issues]
| [Source code]
| [License]


[![CI][badge-tests]][project-tests]
[![Coverage Status][badge-coverage]][project-codecov]
[![License][badge-license]][project-license]
[![Downloads per month][badge-downloads-per-month]][project-downloads]

[![Supported Python versions][badge-python-versions]][project-pypi]
[![Status][badge-status]][project-pypi]
[![Package version][badge-package-version]][project-pypi]


## About

The `tsperf` program includes both a database workload generator, and a query
timer. That effectively spans two domains, one for writing data, and another
one for reading.

- [Data Generator]: Generate time series data and feed it into database.
  Use `tsperf write --help` to explore its options.
- [Query Timer]: Probe responsiveness of database on the read path.
  Use `tsperf read --help` to explore its options.

For the purpose of capacity testing, both domains try to simulate the generation and querying of
time-series data. As the program is easy to use, it provides instant reward without the need to
set up a whole data ingestion chain.


## Features

### General
* Generate random data which follows a statistical model to better reflect real world scenarios,
  real world data is almost never truly random.
* The "steady load"-mode can simulate a constant load of a defined number of messages per second.
* Ready-made to deploy and scale data generators with Docker containers. In order to maximize
  performance, multiple instances of the data generator can be run in parallel.
  This can be achieved by [parallelizing using Kubernetes].
* Metrics are exposed for consumption by Prometheus.

### Data Generator
* Capability to [define your own schema].
* Full control on how many values will be inserted.
* Scale out to multiple clients is a core concept.
* Huge sets of data can be inserted without creating files as intermediate storage.

### Database Coverage
* CrateDB
* InfluxDB
* Microsoft SQL Server
* MongoDB
* PostgreSQL
* TimescaleDB
* Timestream


## Install

### Python package
```shell
pip install --user tsperf
```

### Docker image
```shell
alias tsperf="docker run -it --rm --network=host tsperf tsperf"
tsperf --help
```

## Usage

Please refer to the [usage] documentation.


## Prior Art

### cr8 + mkjson
`mkjson` combined with `cr8 insert-json` makes it easy to generate random entries into a table.
See [generate data sets using mkjson] for an example how to use `cr8` together with `mkjson`.

### TSBS
The [Time Series Benchmark Suite (TSBS)] is a collection of Go programs that are used to generate
datasets and then benchmark read and write performance of various databases.


## Project Information

### Contributing
We are always happy to receive code contributions, ideas, suggestions and
problem reports from the community.

So, if you’d like to contribute you’re most welcome. Spend some time taking
a look around, locate a bug, design issue or spelling mistake and then send
us a pull request or open an issue on GitHub.

Thanks in advance for your efforts, we really appreciate any help or feedback.

### Acknowledgements
Thanks to all the contributors who helped to co-create and conceive `tsperf`
in one way or another and kudos to all authors of the foundational libraries.

### License
This project is licensed under the terms of the Apache 2.0 license.


[Data Generator]: https://tsperf.readthedocs.io/data-generator.html
[define your own schema]: https://tsperf.readthedocs.io/data-generator.html#data-generator-schemas
[generate data sets using mkjson]: https://zignar.net/2020/05/01/generating-data-sets-using-mkjson/
[parallelizing using Kubernetes]: https://tsperf.readthedocs.io/performance.html
[Query Timer]: https://tsperf.readthedocs.io/query-timer.html
[Time Series Benchmark Suite (TSBS)]: https://github.com/timescale/tsbs
[Usage]: https://tsperf.readthedocs.io/usage.html

[Changelog]: https://github.com/crate/tsperf/blob/main/CHANGES.md
[Documentation]: https://tsperf.readthedocs.io/
[Issues]: https://github.com/crate/tsperf/issues
[License]: https://github.com/crate/tsperf/blob/main/LICENSE
[PyPI]: https://pypi.org/project/tsperf/
[Source code]: https://github.com/crate/tsperf

[badge-coverage]: https://codecov.io/gh/crate/tsperf/branch/main/graph/badge.svg
[badge-downloads-per-month]: https://pepy.tech/badge/tsperf/month
[badge-license]: https://img.shields.io/github/license/crate/tsperf.svg
[badge-package-version]: https://img.shields.io/pypi/v/tsperf.svg
[badge-python-versions]: https://img.shields.io/pypi/pyversions/tsperf.svg
[badge-status]: https://img.shields.io/pypi/status/tsperf.svg
[badge-tests]: https://github.com/crate/tsperf/actions/workflows/tests.yml/badge.svg
[project-codecov]: https://codecov.io/gh/crate/tsperf
[project-downloads]: https://pepy.tech/project/tsperf/
[project-license]: https://github.com/crate/tsperf/blob/main/LICENSE
[project-pypi]: https://pypi.org/project/tsperf
[project-tests]: https://github.com/crate/tsperf/actions/workflows/tests.yml
