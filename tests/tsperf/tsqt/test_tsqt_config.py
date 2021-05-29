import os
import os.path
from unittest import mock

import pytest

import tsperf
from tsperf.adapter.cratedb import CrateDbAdapter
from tsperf.model.interface import DatabaseInterfaceType
from tsperf.tsqt.config import QueryTimerConfig


def test_config_vanilla():
    config = QueryTimerConfig(adapter=DatabaseInterfaceType.CrateDB)
    assert config.adapter == DatabaseInterfaceType.CrateDB
    assert config.concurrency == 10
    assert config.iterations == 100
    assert config.quantiles == ["50", "60", "75", "90", "99"]
    assert config.refresh_rate == 0.1

    assert config.host == "localhost"
    assert config.username is None
    assert config.password is None
    assert config.db_name == ""

    assert config.token == ""
    assert config.organization == ""

    assert config.query is None


def mkconfig(*more_args):
    ctx = tsperf.cli.read.make_context(
        info_name=None, args=["--adapter=cratedb"] + list(more_args)
    )
    config = QueryTimerConfig.create(**ctx.params)
    return config


def test_config_adapter_environ():
    test_adapter = DatabaseInterfaceType.InfluxDB2
    os.environ["ADAPTER"] = test_adapter.name.lower()

    ctx = tsperf.cli.read.make_context(info_name=None, args=[])
    config = QueryTimerConfig.create(**ctx.params)

    assert config.adapter == test_adapter
    del os.environ["ADAPTER"]


def test_config_concurrency_environ():
    test_concurrency = 3
    os.environ["CONCURRENCY"] = str(test_concurrency)
    config = mkconfig()
    assert config.concurrency == test_concurrency
    del os.environ["CONCURRENCY"]


def test_config_iterations_environ():
    test_iterations = 3
    os.environ["ITERATIONS"] = str(test_iterations)
    config = mkconfig()
    assert config.iterations == test_iterations
    del os.environ["ITERATIONS"]


def test_config_env_quantiles_set():
    test_quantiles = "1,2,3,4,5"
    os.environ["QUANTILES"] = test_quantiles
    config = mkconfig()
    assert config.quantiles == ["1", "2", "3", "4", "5"]
    del os.environ["QUANTILES"]


def test_config_env_refresh_rate_set():
    test_refresh_rate = 3
    os.environ["REFRESH_RATE"] = str(test_refresh_rate)
    config = mkconfig()
    assert config.refresh_rate == test_refresh_rate
    del os.environ["REFRESH_RATE"]


def test_config_query_environ():
    test_query = "SELECT * FROM test"
    os.environ["QUERY"] = test_query
    config = mkconfig()
    assert config.query == test_query
    del os.environ["QUERY"]


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


def test_validate_default_valid():
    config = QueryTimerConfig(adapter=DatabaseInterfaceType.CrateDB)
    assert config.validate_config()


@mock.patch("os.path.isfile")
def test_validate_adapter_invalid(mock_isfile):
    mock_isfile.return_value = True
    test_adapter = -1
    config = QueryTimerConfig(adapter=test_adapter)
    config.adapter = test_adapter

    with pytest.raises(ValueError) as ex:
        config.validate_config()
    ex.match("-1 is not a valid DatabaseInterfaceType")


def test_validate_port_invalid():
    test_port = "0"
    config = mkconfig()
    config.port = test_port
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "PORT" in config.invalid_configs[0]


def test_not_enough_results():
    config = mkconfig()
    config.iterations = 10
    config.concurrency = 1
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "CONCURRENCY" in config.invalid_configs[0]
    assert "ITERATIONS" in config.invalid_configs[0]


@mock.patch("shutil.get_terminal_size", autospec=True)
def test_terminal_to_small(mock_terminal_size):
    mock_size = mock.MagicMock()
    mock_terminal_size.return_value = mock_size
    mock_size.lines = 15
    config = mkconfig()
    config.quantiles = ["1", "2"]
    assert config.validate_config()
    config.quantiles = ["1", "2", "3", "4", "5"]
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "QUANTILES" in config.invalid_configs[0]


def test_load_args():
    test_concurrency = 1
    config = mkconfig()
    config.concurrency = test_concurrency
    args = {"concurrency": 4}
    config.load_args(args)
    assert config.concurrency == 4


@mock.patch("os.path.isfile")
def test_config_default_select_query(mock_isfile):
    mock_isfile.return_value = True
    config = mkconfig()
    assert config.validate_config(adapter=CrateDbAdapter)
    assert config.query == "SELECT 1;"


@mock.patch("os.path.isfile")
def test_config_default_port_cratedb(mock_isfile):
    mock_isfile.return_value = True
    config = mkconfig()
    assert config.validate_config(adapter=CrateDbAdapter)
    assert config.port == 4200
