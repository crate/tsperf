import os
import os.path
from unittest import mock

import pytest

import tsperf
from tsperf.adapter import AdapterManager
from tsperf.model.interface import DatabaseInterfaceType
from tsperf.read.config import QueryTimerConfig
from tsperf.util.common import to_list


def mkconfig(cli_more_args=None):
    cli_more_args = cli_more_args or []
    ctx = tsperf.cli.read.make_context(
        info_name=None,
        args=["--adapter=dummy"] + cli_more_args,
    )
    config = QueryTimerConfig.create(**ctx.params)
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


def test_config_vanilla():
    config = QueryTimerConfig(adapter=DatabaseInterfaceType.Dummy)
    assert config.adapter == DatabaseInterfaceType.Dummy
    assert config.concurrency == 4
    assert config.iterations == 1000
    assert config.quantiles == ["50", "60", "75", "90", "99"]
    assert config.refresh_interval == 0.1

    assert config.address is None
    assert config.username is None
    assert config.password is None
    assert config.database is None

    assert config.influxdb_organization is None
    assert config.influxdb_token is None

    assert config.query is None


def test_config_real():
    config = mkconfig()
    _ = AdapterManager.create(interface=config.adapter, config=config)
    config.validate_config()

    assert config.address == "localhost:12345"


def test_config_adapter_environ():
    test_adapter = DatabaseInterfaceType.InfluxDB
    os.environ["ADAPTER"] = test_adapter.name.lower()

    ctx = tsperf.cli.read.make_context(info_name=None, args=[])
    config = QueryTimerConfig.create(**ctx.params)

    assert config.adapter == test_adapter
    del os.environ["ADAPTER"]


@pytest.mark.parametrize("env_vars", ["CONCURRENCY=7"])
def test_config_concurrency_environ(config_environ):
    assert config_environ.concurrency == 7


@pytest.mark.parametrize("env_vars", ["ITERATIONS=3"])
def test_config_iterations_environ(config_environ):
    assert config_environ.iterations == 3


@pytest.mark.parametrize("env_vars", ["QUANTILES=1,2,3,4,5"])
def test_config_quantiles_environ(config_environ):
    assert config_environ.quantiles == ["1", "2", "3", "4", "5"]


@pytest.mark.parametrize("env_vars", ["REFRESH_INTERVAL=9"])
def test_config_refresh_interval_environ(config_environ):
    assert config_environ.refresh_interval == 9


@pytest.mark.parametrize("env_vars", ["QUERY=SELECT * FROM test"])
def test_config_query_environ(config_environ):
    assert config_environ.query == "SELECT * FROM test"


@pytest.mark.parametrize("env_vars", ["ADDRESS=test/address"])
def test_config_address_environ(config_environ):
    assert config_environ.address == "test/address"


def test_validate_default_valid():
    config = QueryTimerConfig(adapter=DatabaseInterfaceType.Dummy)
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


def test_not_enough_results():
    config = mkconfig()
    config.iterations = 10
    config.concurrency = 1
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "CONCURRENCY" in config.invalid_configs[0]
    assert "ITERATIONS" in config.invalid_configs[0]


@mock.patch("shutil.get_terminal_size", autospec=True)
def test_terminal_too_small(mock_terminal_size):
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
def test_config_defaults_dummy(mock_isfile):
    mock_isfile.return_value = True
    config = mkconfig()
    config.adapter = DatabaseInterfaceType.Dummy
    assert config.validate_config()
    assert config.address == "localhost:12345"
    assert config.query == "SELECT 42;"


@mock.patch("os.path.isfile")
def test_config_defaults_cratedb(mock_isfile):
    mock_isfile.return_value = True
    config = mkconfig()
    config.adapter = DatabaseInterfaceType.CrateDB
    assert config.validate_config()
    assert config.address == "localhost:4200"
    assert config.query == "SELECT 1;"


@mock.patch("os.path.isfile")
def test_config_defaults_influxdb(mock_isfile):
    mock_isfile.return_value = True
    config = mkconfig()
    config.adapter = DatabaseInterfaceType.InfluxDB
    assert config.validate_config()
    assert config.address == "http://localhost:8086/"
    assert config.query is None
