![tag_build_and_push](https://github.com/crate/ts-data-generator/workflows/tag_build_and_push/badge.svg?branch=master) ![code_quality](https://github.com/crate/ts-data-generator/workflows/code_quality/badge.svg)

# Data Generator

The Data Generator has its own in-depth [documentation](DATA_GENERATOR.md).
For the purpose of capacity testing it simulates the generation of timeseries
data, without the need to set up an ingestion chain (which could be Azure IoTHub, RabbitMQ, etc.)

## Maximizing Performance

To maximize performance multiple instances of the Data Generator must be run in parallel. One way to achieve this is using kubernetes how to do this is documented [here](KUBERNETES.md).
