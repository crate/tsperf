import os
import os.path
import time
from unittest import mock

import pytest

import tsperf.cli
from tsperf.adapter.cratedb import CrateDbAdapter
from tsperf.model.interface import DatabaseInterfaceType
from tsperf.tsdg.config import DataGeneratorConfig
from tsperf.tsdg.model import IngestMode


def test_config_default():
    config = DataGeneratorConfig(adapter=DatabaseInterfaceType.CrateDB)
    assert config.adapter == DatabaseInterfaceType.CrateDB
    assert config.id_start == 1
    assert config.id_end == 500
    assert config.ingest_mode == IngestMode.FAST
    assert config.ingest_size == 1000
    assert config.ingest_ts == pytest.approx(time.time(), abs=0.3)
    assert config.ingest_delta == 0.5
    assert config.model is None
    assert config.batch_size == -1
    assert config.stat_delta == 30

    assert config.host == "localhost"
    assert config.username is None
    assert config.password is None
    assert config.db_name == ""
    assert config.table_name == ""
    assert config.partition == "week"

    assert config.shards == 4
    assert config.replicas == 1

    assert config.token == ""
    assert config.organization == ""


def mkconfig(*more_args):
    ctx = tsperf.cli.write.make_context(
        info_name=None,
        args=["--model=examples/temperature.json", "--adapter=cratedb"]
        + list(more_args),
    )
    config = DataGeneratorConfig.create(**ctx.params)
    return config


def test_config_id_start_environ():
    os.environ["ID_START"] = str(10)
    config = mkconfig()
    assert config.id_start == 10
    del os.environ["ID_START"]


def test_config_id_start_cmdline():
    config = mkconfig("--id-start=10")
    assert config.id_start == 10


def test_config_id_end_environ():
    test_id_end = 50
    os.environ["ID_END"] = str(test_id_end)
    config = mkconfig()
    assert config.id_end == test_id_end
    del os.environ["ID_END"]


def test_config_ingest_mode_environ():
    test_ingest_mode = IngestMode.CONSECUTIVE
    os.environ["INGEST_MODE"] = test_ingest_mode.name.lower()
    config = mkconfig()
    assert config.ingest_mode == test_ingest_mode
    del os.environ["INGEST_MODE"]


def test_config_env_ingest_size_set():
    test_ingest_size = 1000
    os.environ["INGEST_SIZE"] = str(test_ingest_size)
    config = mkconfig()
    assert config.ingest_size == test_ingest_size
    del os.environ["INGEST_SIZE"]


def test_config_env_ingest_ts_set():
    ts = time.time()
    os.environ["INGEST_TS"] = str(ts)
    config = mkconfig()
    assert config.ingest_ts == ts
    del os.environ["INGEST_TS"]


def test_config_env_ingest_delta_set():
    test_ingest_delta = 10
    os.environ["INGEST_DELTA"] = str(test_ingest_delta)
    config = mkconfig()
    assert config.ingest_delta == test_ingest_delta
    del os.environ["INGEST_DELTA"]


def test_config_model_environ():
    test_path = "test/path"
    os.environ["MODEL"] = test_path

    ctx = tsperf.cli.write.make_context(info_name=None, args=["--adapter=cratedb"])
    config = DataGeneratorConfig.create(**ctx.params)

    assert config.model == test_path
    del os.environ["MODEL"]


def test_config_batch_size_environ():
    test_batch_size = 100
    os.environ["BATCH_SIZE"] = str(test_batch_size)
    config = mkconfig()
    assert config.batch_size == test_batch_size
    del os.environ["BATCH_SIZE"]


def test_config_adapter_environ():
    test_adapter = DatabaseInterfaceType.InfluxDB2
    os.environ["ADAPTER"] = test_adapter.name.lower()

    ctx = tsperf.cli.write.make_context(info_name=None, args=["--model=foobar"])
    config = DataGeneratorConfig.create(**ctx.params)

    assert config.adapter == test_adapter
    del os.environ["ADAPTER"]


def test_config_env_stat_delta_set():
    test_stat_delta = 60
    os.environ["STAT_DELTA"] = str(test_stat_delta)
    config = mkconfig()
    assert config.stat_delta == test_stat_delta
    del os.environ["STAT_DELTA"]


def test_config_env_host_set():
    test_host = "test/host"
    os.environ["HOST"] = test_host
    config = mkconfig()
    assert config.host == test_host
    del os.environ["HOST"]


def test_config_env_username_set():
    test_username = "testUsername"
    os.environ["USERNAME"] = test_username
    config = mkconfig()
    assert config.username == test_username
    del os.environ["USERNAME"]


def test_config_env_password_set():
    test_password = "password"
    os.environ["PASSWORD"] = test_password
    config = mkconfig()
    assert config.password == test_password
    del os.environ["PASSWORD"]


def test_config_env_db_name_set():
    test_db_name = "dbName"
    os.environ["DB_NAME"] = test_db_name
    config = mkconfig()
    assert config.db_name == test_db_name
    del os.environ["DB_NAME"]


def test_config_env_table_name_set():
    test_table_name = "testTableName"
    os.environ["TABLE_NAME"] = test_table_name
    config = mkconfig()
    assert config.table_name == test_table_name
    del os.environ["TABLE_NAME"]


def test_config_env_partition_set():
    test_partition = "day"
    os.environ["PARTITION"] = test_partition
    config = mkconfig()
    assert config.partition == test_partition
    del os.environ["PARTITION"]


def test_config_shards_environ():
    test_shards = 6
    os.environ["SHARDS"] = str(test_shards)
    config = mkconfig()
    assert config.shards == test_shards
    del os.environ["SHARDS"]


def test_config_replicas_environ():
    test_replicas = 2
    os.environ["REPLICAS"] = str(test_replicas)
    config = mkconfig()
    assert config.replicas == test_replicas
    del os.environ["REPLICAS"]


def test_config_env_port_set():
    test_port = "1234"
    os.environ["PORT"] = test_port
    config = mkconfig()
    assert config.port == test_port
    del os.environ["PORT"]


def test_config_env_token_set():
    test_token = "testToken"
    os.environ["TOKEN"] = test_token
    config = mkconfig()
    assert config.token == test_token
    del os.environ["TOKEN"]


def test_config_env_organization_set():
    test_organization = "testOrganization"
    os.environ["ORG"] = test_organization
    config = mkconfig()
    assert config.organization == test_organization
    del os.environ["ORG"]


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
def test_validate_model_path_invalid(mock_isfile):
    mock_isfile.return_value = False
    config = mkconfig()
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "MODEL" in config.invalid_configs[0]


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
def test_validate_port_invalid(mock_isfile):
    mock_isfile.return_value = True
    test_port = "0"
    config = mkconfig()
    config.port = test_port
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "PORT" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_prometheus_port_invalid(mock_isfile):
    mock_isfile.return_value = True
    config = DataGeneratorConfig(
        adapter=DatabaseInterfaceType.CrateDB,
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
def test_config_default_port_cratedb(mock_isfile):
    mock_isfile.return_value = True
    config = mkconfig()
    assert config.validate_config(adapter=CrateDbAdapter)
    assert config.port == 4200
