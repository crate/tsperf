from unittest import mock

import pytest

import tsperf.read.core as qt
from tsperf.engine import TsPerfEngine
from tsperf.model.interface import DatabaseInterfaceType
from tsperf.read.config import QueryTimerConfig


@pytest.fixture(scope="function")
def config() -> QueryTimerConfig:
    config = QueryTimerConfig(adapter=DatabaseInterfaceType.Dummy)
    return config


@pytest.mark.parametrize("adapter", list(DatabaseInterfaceType))
@mock.patch("tsperf.adapter.AdapterManager.create", autospec=True)
def test_get_database_adapter(factory_mock, adapter, config):
    config.adapter = adapter
    engine = TsPerfEngine(config=config)
    engine.bootstrap()
    engine.create_adapter()

    factory_mock.assert_called_once()
    factory_mock.assert_called_with(
        interface=adapter,
        config=QueryTimerConfig(
            adapter=adapter,
            address=mock.ANY,
            query=mock.ANY,
        ),
        schema={},
    )


def test_percentage_to_rgb():
    r, g, b = qt.percentage_to_rgb(0)
    assert r == 255
    assert g == 0
    assert b == 0
    r, g, b = qt.percentage_to_rgb(50)
    assert r == 255
    assert g == 255
    assert b == 0
    r, g, b = qt.percentage_to_rgb(100)
    assert r == 127.5
    assert g == 255
    assert b == 0


@mock.patch("tsperf.read.core.engine", autospec=True)
def test_start_query_run(mock_engine, config):
    mock_db_writer = mock.MagicMock()
    mock_db_writer.execute_query.side_effect = [[1, 2, 3], Exception("mocked failure")]
    mock_engine.create_adapter.return_value = mock_db_writer

    # FIXME: This uses variables in the module scope. Get rid of it.
    qt.config = config

    qt.config.iterations = 2
    qt.start_query_run()
    assert mock_db_writer.execute_query.call_count == 2
    assert qt.success == 1
    assert qt.failure == 1
