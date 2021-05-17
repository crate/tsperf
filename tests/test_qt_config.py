import os
import mock
import os.path
from query_timer.config import QueryTimerConfig


def test_config_constructor_no_env_set():
    config = QueryTimerConfig()
    assert config.database == 0
    assert config.concurrency == 10
    assert config.iterations == 100
    assert config.quantiles == ["50", "60", "75", "90", "99"]
    assert config.refresh_rate == 0.1
    assert config.query == ""

    assert config.host == "localhost"
    assert config.username is None
    assert config.password is None
    assert config.db_name == ""

    assert config.port == "5432"

    assert config.token == ""
    assert config.organization == ""


def test_config_constructor_env_database_set():
    test_database = 3
    os.environ["DATABASE"] = str(test_database)
    config = QueryTimerConfig()
    assert config.database == test_database
    del os.environ["DATABASE"]


def test_config_constructor_env_concurrency_set():
    test_concurrency = 3
    os.environ["CONCURRENCY"] = str(test_concurrency)
    config = QueryTimerConfig()
    assert config.concurrency == test_concurrency
    del os.environ["CONCURRENCY"]


def test_config_constructor_env_iterations_set():
    test_iterations = 3
    os.environ["ITERATIONS"] = str(test_iterations)
    config = QueryTimerConfig()
    assert config.iterations == test_iterations
    del os.environ["ITERATIONS"]


def test_config_constructor_env_quantiles_set():
    test_quantiles = "1,2,3,4,5"
    os.environ["QUANTILES"] = test_quantiles
    config = QueryTimerConfig()
    assert config.quantiles == ["1", "2", "3", "4", "5"]
    del os.environ["QUANTILES"]


def test_config_constructor_env_refresh_rate_set():
    test_refresh_rate = 3
    os.environ["REFRESH_RATE"] = str(test_refresh_rate)
    config = QueryTimerConfig()
    assert config.refresh_rate == test_refresh_rate
    del os.environ["REFRESH_RATE"]


def test_config_constructor_env_query_set():
    test_query = "SELECT * FROM test"
    os.environ["QUERY"] = test_query
    config = QueryTimerConfig()
    assert config.query == test_query
    del os.environ["QUERY"]


def test_config_constructor_env_host_set():
    test_host = "test/host"
    os.environ["HOST"] = test_host
    config = QueryTimerConfig()
    assert config.host == test_host
    del os.environ["HOST"]


def test_config_constructor_env_username_set():
    test_username = "testUsername"
    os.environ["USERNAME"] = test_username
    config = QueryTimerConfig()
    assert config.username == test_username
    del os.environ["USERNAME"]


def test_config_constructor_env_password_set():
    test_password = "password"
    os.environ["PASSWORD"] = test_password
    config = QueryTimerConfig()
    assert config.password == test_password
    del os.environ["PASSWORD"]


def test_config_constructor_env_db_name_set():
    test_db_name = "dbName"
    os.environ["DB_NAME"] = test_db_name
    config = QueryTimerConfig()
    assert config.db_name == test_db_name
    del os.environ["DB_NAME"]


def test_config_constructor_env_port_set():
    test_port = "1234"
    os.environ["PORT"] = test_port
    config = QueryTimerConfig()
    assert config.port == test_port
    del os.environ["PORT"]


def test_config_constructor_env_token_set():
    test_token = "testToken"
    os.environ["TOKEN"] = test_token
    config = QueryTimerConfig()
    assert config.token == test_token
    del os.environ["TOKEN"]


def test_config_constructor_env_organization_set():
    test_organization = "testOrganization"
    os.environ["ORG"] = test_organization
    config = QueryTimerConfig()
    assert config.organization == test_organization
    del os.environ["ORG"]


def test_validate_config_default_true():
    config = QueryTimerConfig()
    assert config.validate_config()


def test_validate_config_database_false():
    test_database = -1
    config = QueryTimerConfig()
    config.database = test_database
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "DATABASE" in config.invalid_configs[0]


def test_validate_config_port_false():
    test_port = "0"
    config = QueryTimerConfig()
    config.port = test_port
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "PORT" in config.invalid_configs[0]


def test_not_enough_results():
    config = QueryTimerConfig()
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
    config = QueryTimerConfig()
    config.quantiles = ["1", "2"]
    assert config.validate_config()
    config.quantiles = ["1", "2", "3", "4", "5"]
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "QUANTILES" in config.invalid_configs[0]


def test_load_args():
    test_concurrency = 1
    config = QueryTimerConfig()
    config.concurrency = test_concurrency
    args = {"concurrency": 4}
    config.load_args(args)
    assert config.concurrency == 4
