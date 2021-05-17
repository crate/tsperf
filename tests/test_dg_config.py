import pytest
import time
import os
import mock
import os.path
from data_generator.config import DataGeneratorConfig


def test_config_constructor_no_env_set():
    config = DataGeneratorConfig()
    assert config.id_start == 1
    assert config.id_end == 500
    assert config.ingest_mode == 1
    assert config.ingest_size == 1000
    assert config.ingest_ts == pytest.approx(time.time(), abs=0.3)
    assert config.ingest_delta == 0.5
    assert config.model_path == ""
    assert config.batch_size == -1
    assert config.database == 0
    assert config.stat_delta == 30

    assert config.host == "localhost"
    assert config.username is None
    assert config.password is None
    assert config.db_name == ""
    assert config.table_name == ""
    assert config.partition == "week"

    assert config.shards == 4
    assert config.replicas == 0

    assert config.port == "5432"

    assert config.token == ""
    assert config.organization == ""


def test_config_constructor_env_id_start_set():
    test_id_start = 10
    os.environ["ID_START"] = str(test_id_start)
    config = DataGeneratorConfig()
    assert config.id_start == test_id_start
    del os.environ["ID_START"]


def test_config_constructor_env_id_end_set():
    test_id_end = 50
    os.environ["ID_END"] = str(test_id_end)
    config = DataGeneratorConfig()
    assert config.id_end == test_id_end
    del os.environ["ID_END"]


def test_config_constructor_env_ingest_mode_set():
    test_ingest_mode = 0
    os.environ["INGEST_MODE"] = str(test_ingest_mode)
    config = DataGeneratorConfig()
    assert config.ingest_mode == test_ingest_mode
    del os.environ["INGEST_MODE"]


def test_config_constructor_env_ingest_size_set():
    test_ingest_size = 1000
    os.environ["INGEST_SIZE"] = str(test_ingest_size)
    config = DataGeneratorConfig()
    assert config.ingest_size == test_ingest_size
    del os.environ["INGEST_SIZE"]


def test_config_constructor_env_ingest_ts_set():
    ts = time.time()
    os.environ["INGEST_TS"] = str(ts)
    config = DataGeneratorConfig()
    assert config.ingest_ts == ts
    del os.environ["INGEST_TS"]


def test_config_constructor_env_ingest_delta_set():
    test_ingest_delta = 10
    os.environ["INGEST_DELTA"] = str(test_ingest_delta)
    config = DataGeneratorConfig()
    assert config.ingest_delta == test_ingest_delta
    del os.environ["INGEST_DELTA"]


def test_config_constructor_env_model_path_set():
    test_path = "test/path"
    os.environ["MODEL_PATH"] = test_path
    config = DataGeneratorConfig()
    assert config.model_path == test_path
    del os.environ["MODEL_PATH"]


def test_config_constructor_env_batch_size_set():
    test_batch_size = 100
    os.environ["BATCH_SIZE"] = str(test_batch_size)
    config = DataGeneratorConfig()
    assert config.batch_size == test_batch_size
    del os.environ["BATCH_SIZE"]


def test_config_constructor_env_database_set():
    test_database = 3
    os.environ["DATABASE"] = str(test_database)
    config = DataGeneratorConfig()
    assert config.database == test_database
    del os.environ["DATABASE"]


def test_config_constructor_env_stat_delta_set():
    test_stat_delta = 60
    os.environ["STAT_DELTA"] = str(test_stat_delta)
    config = DataGeneratorConfig()
    assert config.stat_delta == test_stat_delta
    del os.environ["STAT_DELTA"]


def test_config_constructor_env_host_set():
    test_host = "test/host"
    os.environ["HOST"] = test_host
    config = DataGeneratorConfig()
    assert config.host == test_host
    del os.environ["HOST"]


def test_config_constructor_env_username_set():
    test_username = "testUsername"
    os.environ["USERNAME"] = test_username
    config = DataGeneratorConfig()
    assert config.username == test_username
    del os.environ["USERNAME"]


def test_config_constructor_env_password_set():
    test_password = "password"
    os.environ["PASSWORD"] = test_password
    config = DataGeneratorConfig()
    assert config.password == test_password
    del os.environ["PASSWORD"]


def test_config_constructor_env_db_name_set():
    test_db_name = "dbName"
    os.environ["DB_NAME"] = test_db_name
    config = DataGeneratorConfig()
    assert config.db_name == test_db_name
    del os.environ["DB_NAME"]


def test_config_constructor_env_table_name_set():
    test_table_name = "testTableName"
    os.environ["TABLE_NAME"] = test_table_name
    config = DataGeneratorConfig()
    assert config.table_name == test_table_name
    del os.environ["TABLE_NAME"]


def test_config_constructor_env_partition_set():
    test_partition = "day"
    os.environ["PARTITION"] = test_partition
    config = DataGeneratorConfig()
    assert config.partition == test_partition
    del os.environ["PARTITION"]


def test_config_constructor_env_shards_set():
    test_shards = 4
    os.environ["SHARDS"] = str(test_shards)
    config = DataGeneratorConfig()
    assert config.shards == test_shards
    del os.environ["SHARDS"]


def test_config_constructor_env_replicas_set():
    test_replicas = 2
    os.environ["REPLICAS"] = str(test_replicas)
    config = DataGeneratorConfig()
    assert config.replicas == test_replicas
    del os.environ["REPLICAS"]


def test_config_constructor_env_port_set():
    test_port = "1234"
    os.environ["PORT"] = test_port
    config = DataGeneratorConfig()
    assert config.port == test_port
    del os.environ["PORT"]


def test_config_constructor_env_token_set():
    test_token = "testToken"
    os.environ["TOKEN"] = test_token
    config = DataGeneratorConfig()
    assert config.token == test_token
    del os.environ["TOKEN"]


def test_config_constructor_env_organization_set():
    test_organization = "testOrganization"
    os.environ["ORG"] = test_organization
    config = DataGeneratorConfig()
    assert config.organization == test_organization
    del os.environ["ORG"]


@mock.patch("os.path.isfile")
def test_validate_config_default_true(mock_isfile):
    mock_isfile.return_value = True
    config = DataGeneratorConfig()
    assert config.validate_config()


@mock.patch("os.path.isfile")
def test_validate_config_id_end_false(mock_isfile):
    mock_isfile.return_value = True
    test_id_end = -1
    config = DataGeneratorConfig()
    config.id_end = test_id_end
    assert not config.validate_config()
    assert len(config.invalid_configs) == 2  # id_end is also smaller than id_start
    assert "ID_END" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_config_id_start_id_end_false(mock_isfile):
    mock_isfile.return_value = True
    test_id_start = 100
    test_id_end = 50
    config = DataGeneratorConfig()
    config.id_start = test_id_start
    config.id_end = test_id_end
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "ID_START" in config.invalid_configs[0]
    assert "ID_END" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_config_ingest_mode_false(mock_isfile):
    mock_isfile.return_value = True
    test_ingest_mode = -1
    config = DataGeneratorConfig()
    config.ingest_mode = test_ingest_mode
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "INGEST_MODE" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_config_ingest_size_false(mock_isfile):
    mock_isfile.return_value = True
    test_ingest_size = -1
    config = DataGeneratorConfig()
    config.ingest_size = test_ingest_size
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "INGEST_SIZE" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_config_ingest_ts_false(mock_isfile):
    mock_isfile.return_value = True
    test_ingest_ts = -1
    config = DataGeneratorConfig()
    config.ingest_ts = test_ingest_ts
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "INGEST_TS" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_config_ingest_delta_false(mock_isfile):
    mock_isfile.return_value = True
    test_ingest_delta = -1
    config = DataGeneratorConfig()
    config.ingest_delta = test_ingest_delta
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "INGEST_DELTA" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_config_model_path_false(mock_isfile):
    mock_isfile.return_value = False
    config = DataGeneratorConfig()
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "MODEL_PATH" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_config_database_false(mock_isfile):
    mock_isfile.return_value = True
    test_database = -1
    config = DataGeneratorConfig()
    config.database = test_database
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "DATABASE" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_config_stat_delta_false(mock_isfile):
    mock_isfile.return_value = True
    test_stat_delta = -1
    config = DataGeneratorConfig()
    config.stat_delta = test_stat_delta
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "STAT_DELTA" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_config_partition_false(mock_isfile):
    mock_isfile.return_value = True
    test_partition = "invalid_partition"
    config = DataGeneratorConfig()
    config.partition = test_partition
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "PARTITION" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_config_id_start_false(mock_isfile):
    mock_isfile.return_value = True
    test_id_start = -1
    config = DataGeneratorConfig()
    config.id_start = test_id_start
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "ID_START" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_config_shards_false(mock_isfile):
    mock_isfile.return_value = True
    test_shards = 0
    config = DataGeneratorConfig()
    config.shards = test_shards
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "SHARDS" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_config_replicas_false(mock_isfile):
    mock_isfile.return_value = True
    test_replicas = -1
    config = DataGeneratorConfig()
    config.replicas = test_replicas
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "REPLICAS" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_config_port_false(mock_isfile):
    mock_isfile.return_value = True
    test_port = "0"
    config = DataGeneratorConfig()
    config.port = test_port
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "PORT" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_config_prometheus_port_false(mock_isfile):
    mock_isfile.return_value = True
    test_port = 0
    config = DataGeneratorConfig()
    config.prometheus_port = test_port
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "PROMETHEUS_PORT" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_validate_config_num_threads_false(mock_isfile):
    mock_isfile.return_value = True
    test_num_threads = 0
    config = DataGeneratorConfig()
    config.num_threads = test_num_threads
    assert not config.validate_config()
    assert len(config.invalid_configs) == 1
    assert "NUM_THREADS" in config.invalid_configs[0]


@mock.patch("os.path.isfile")
def test_load_args(mock_isfile):
    mock_isfile.return_value = True
    test_num_threads = 1
    config = DataGeneratorConfig()
    config.num_threads = test_num_threads
    args = {"num_threads": 4}
    config.load_args(args)
    assert config.num_threads == 4
