import os
import os.path
import time
from unittest import mock

import pytest

import tsperf.cli
from tsperf.model.interface import DatabaseInterfaceType
from tsperf.util.common import to_list
from tsperf.write.config import DataGeneratorConfig
from tsperf.write.model import IngestMode


def mkconfig(cli_more_args=None):
    cli_more_args = cli_more_args or []
    ctx = tsperf.cli.write.make_context(
        info_name=None,
        args=["--schema=foobar.json", "--adapter=dummy"] + cli_more_args,
    )
    config = DataGeneratorConfig.create(**ctx.params)
    return config


@pytest.fixture(scope="function")
def config_cmdline(cli_args):
    cli_args = to_list(cli_args)
    return mkconfig(cli_args)


@pytest.fixture(scope="function")
def config_environ(env_vars):
    env_vars = to_list(env_vars)
    names = []
    for env_var in env_vars:
        name, value = env_var.split("=")
        names.append(name)
        os.environ[name] = value
    yield mkconfig()
    for name in names:
        del os.environ[name]


def test_config_default():
    config = DataGeneratorConfig(adapter=DatabaseInterfaceType.Dummy)
    assert config.adapter == DatabaseInterfaceType.Dummy
    assert config.id_start == 1
    assert config.id_end == 500
    assert config.ingest_mode == IngestMode.FAST
    assert config.ingest_size == 1000
    assert config.ingest_ts == pytest.approx(time.time(), abs=0.3)
    assert config.ingest_delta == 0.5
    assert config.schema is None
    assert config.batch_size == -1
    assert config.stat_delta == 30

    assert config.address is None
    assert config.username is None
    assert config.password is None
    assert config.database == ""
    assert config.table == ""
    assert config.partition == "week"

    assert config.shards == 4
    assert config.replicas == 1

    assert config.influxdb_organization is None
    assert config.influxdb_token is None


def test_config_schema_environ():
    test_path = "test/path"
    os.environ["SCHEMA"] = test_path

    ctx = tsperf.cli.write.make_context(info_name=None, args=["--adapter=dummy"])
    config = DataGeneratorConfig.create(**ctx.params)

    assert config.schema == test_path
    del os.environ["SCHEMA"]


def test_config_adapter_environ():
    test_adapter = DatabaseInterfaceType.InfluxDB
    os.environ["ADAPTER"] = test_adapter.name.lower()

    ctx = tsperf.cli.write.make_context(info_name=None, args=["--schema=foobar"])
    config = DataGeneratorConfig.create(**ctx.params)

    assert config.adapter == test_adapter
    del os.environ["ADAPTER"]


@pytest.mark.parametrize("cli_args", ["--id-start=10"])
def test_config_id_start_cmdline(config_cmdline):
    assert config_cmdline.id_start == 10


@pytest.mark.parametrize("env_vars", ["ID_START=11"])
def test_config_id_start_environ(config_environ):
    assert config_environ.id_start == 11


@pytest.mark.parametrize("env_vars", ["ID_END=50"])
def test_config_id_end_environ(config_environ):
    assert config_environ.id_start == 1
    assert config_environ.id_end == 50


@pytest.mark.parametrize("env_vars", ["INGEST_MODE=consecutive"])
def test_config_ingest_mode_consecutive_environ(config_environ):
    assert config_environ.ingest_mode == IngestMode.CONSECUTIVE


@pytest.mark.parametrize("env_vars", ["INGEST_MODE=fast"])
def test_config_ingest_mode_fast_environ(config_environ):
    assert config_environ.ingest_mode == IngestMode.FAST


@pytest.mark.parametrize("env_vars", ["INGEST_SIZE=1000"])
def test_config_ingest_size_environ(config_environ):
    assert config_environ.ingest_size == 1000


def test_config_ingest_ts_environ():
    ts = time.time()
    os.environ["INGEST_TS"] = str(ts)
    config = mkconfig()
    assert config.ingest_ts == ts
    del os.environ["INGEST_TS"]


@pytest.mark.parametrize("env_vars", ["INGEST_DELTA=10"])
def test_config_ingest_delta_environ(config_environ):
    assert config_environ.ingest_delta == 10


@pytest.mark.parametrize("env_vars", ["STAT_DELTA=60"])
def test_config_stat_delta_environ(config_environ):
    assert config_environ.stat_delta == 60


@pytest.mark.parametrize("env_vars", ["BATCH_SIZE=100"])
def test_config_batch_size_environ(config_environ):
    assert config_environ.batch_size == 100


@pytest.mark.parametrize("env_vars", ["ADDRESS=test/address"])
def test_config_address_environ(config_environ):
    assert config_environ.address == "test/address"


@pytest.mark.parametrize("env_vars", ["USERNAME=testUsername"])
def test_config_username_environ(config_environ):
    assert config_environ.username == "testUsername"


@pytest.mark.parametrize("env_vars", ["PASSWORD=password"])
def test_config_password_environ(config_environ):
    assert config_environ.password == "password"


@pytest.mark.parametrize("env_vars", ["DATABASE=dbName"])
def test_config_database_environ(config_environ):
    assert config_environ.database == "dbName"


@pytest.mark.parametrize("env_vars", ["TABLE=testTableName"])
def test_config_table_environ(config_environ):
    assert config_environ.table == "testTableName"


@pytest.mark.parametrize("env_vars", ["PARTITION=day"])
def test_config_partition_environ(config_environ):
    assert config_environ.partition == "day"


@pytest.mark.parametrize("env_vars", ["SHARDS=6"])
def test_config_shards_environ(config_environ):
    assert config_environ.shards == 6


@pytest.mark.parametrize("env_vars", ["REPLICAS=2"])
def test_config_replicas_environ(config_environ):
    assert config_environ.replicas == 2


@pytest.mark.parametrize("env_vars", ["INFLUXDB_ORGANIZATION=testOrganization"])
def test_config_influxdb_organization_environ(config_environ):
    assert config_environ.influxdb_organization == "testOrganization"


@pytest.mark.parametrize("env_vars", ["INFLUXDB_TOKEN=testToken"])
def test_config_influxdb_token_environ(config_environ):
    assert config_environ.influxdb_token == "testToken"


@mock.patch("os.path.isfile")
def test_validate_default(mock_isfile):
    mock_isfile.return_value = True
    config = mkconfig()
    assert config.validate_config()


@mock.patch("os.path.isfile")
def test_validate_id_end_invalid(mock_isfile):
    mock_isfile.return_value = True
    test_id_end = -1
    config = mkconfig()
    config.id_end = test_id_end
    assert not config.validate_config()
    assert len(config.invalid_configs) == 2  # id_end is also smaller than id_start
    assert "ID_END" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_id_start_id_end_invalid(mock_isfile):
    mock_isfile.return_value = True
    test_id_start = 100
    test_id_end = 50
    config = mkconfig()
    config.id_start = test_id_start
    config.id_end = test_id_end
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "ID_START" in config.invalid_configs[0]
    assert "ID_END" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_ingest_mode_invalid(mock_isfile):
    mock_isfile.return_value = True
    test_ingest_mode = -1
    config = mkconfig()
    config.ingest_mode = test_ingest_mode
    with pytest.raises(ValueError) as ex:
        config.validate_config()
    ex.match("-1 is not a valid IngestMode")


@mock.patch("os.path.isfile")
def test_validate_ingest_size_invalid(mock_isfile):
    mock_isfile.return_value = True
    test_ingest_size = -1
    config = mkconfig()
    config.ingest_size = test_ingest_size
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "INGEST_SIZE" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_ingest_ts_invalid(mock_isfile):
    mock_isfile.return_value = True
    test_ingest_ts = -1
    config = mkconfig()
    config.ingest_ts = test_ingest_ts
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "INGEST_TS" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_ingest_delta_invalid(mock_isfile):
    mock_isfile.return_value = True
    test_ingest_delta = -1
    config = mkconfig()
    config.ingest_delta = test_ingest_delta
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "INGEST_DELTA" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_adapter_invalid(mock_isfile):
    mock_isfile.return_value = True
    test_adapter = -1
    config = DataGeneratorConfig(adapter=test_adapter)
    config.adapter = test_adapter

    with pytest.raises(ValueError) as ex:
        config.validate_config()
    ex.match("-1 is not a valid DatabaseInterfaceType")


@mock.patch("os.path.isfile")
def test_validate_stat_delta_invalid(mock_isfile):
    mock_isfile.return_value = True
    test_stat_delta = -1
    config = mkconfig()
    config.stat_delta = test_stat_delta
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "STAT_DELTA" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_partition_invalid(mock_isfile):
    mock_isfile.return_value = True
    test_partition = "invalid_partition"
    config = mkconfig()
    config.partition = test_partition
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "PARTITION" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_id_start_invalid(mock_isfile):
    mock_isfile.return_value = True
    test_id_start = -1
    config = mkconfig()
    config.id_start = test_id_start
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "ID_START" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_shards_invalid(mock_isfile):
    mock_isfile.return_value = True
    test_shards = 0
    config = mkconfig()
    config.shards = test_shards
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "SHARDS" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_replicas_invalid(mock_isfile):
    mock_isfile.return_value = True
    test_replicas = -1
    config = mkconfig()
    config.replicas = test_replicas
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "REPLICAS" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_prometheus_port_invalid(mock_isfile):
    mock_isfile.return_value = True
    config = DataGeneratorConfig(
        adapter=DatabaseInterfaceType.Dummy,
        prometheus_enable=True,
        prometheus_listen=":0",
    )
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "PROMETHEUS_PORT" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_concurrency_invalid(mock_isfile):
    mock_isfile.return_value = True
    test_concurrency = 0
    config = mkconfig()
    config.concurrency = test_concurrency
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "CONCURRENCY" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_load_args(mock_isfile):
    mock_isfile.return_value = True

    config = mkconfig()
    assert config.concurrency == 2

    args = {"concurrency": 4}
    config.load_args(args)
    assert config.concurrency == 4


@mock.patch("os.path.isfile")
def test_config_default_concurrency(mock_isfile):
    mock_isfile.return_value = True
    config = mkconfig()
    assert config.concurrency == 2


@mock.patch("os.path.isfile")
def test_config_defaults_cratedb(mock_isfile):
    mock_isfile.return_value = True
    config = mkconfig()
    config.adapter = DatabaseInterfaceType.CrateDB
    assert config.validate_config()
    assert config.address == "localhost:4200"


@mock.patch("os.path.isfile")
def test_config_defaults_influxdb(mock_isfile):
    mock_isfile.return_value = True
    config = mkconfig()
    config.adapter = DatabaseInterfaceType.InfluxDB
    assert config.validate_config()
    assert config.address == "http://localhost:8086/"
