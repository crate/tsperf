from unittest import mock

import pytest

import tsperf.tsqt.core as qt
from tsperf.model.interface import DatabaseInterfaceType
from tsperf.tsqt.config import QueryTimerConfig


@pytest.fixture(scope="function")
def config():
    config = QueryTimerConfig(adapter=DatabaseInterfaceType.CrateDB)
    return config


@pytest.mark.parametrize("adapter", list(DatabaseInterfaceType))
@mock.patch("tsperf.adapter.AdapterManager.create", autospec=True)
def test_get_database_adapter(factory_mock, adapter, config):
    qt.config = config
    qt.config.adapter = adapter
    qt.get_database_adapter()
    factory_mock.assert_called_once()
    factory_mock.assert_called_with(
        interface=adapter,
        config=QueryTimerConfig(
            adapter=adapter,
            host="localhost",
        ),
        model={"value": "none"},
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


@mock.patch("tsperf.tsqt.core.get_database_adapter", autospec=True)
def test_start_query_run(mock_get_db_writer):
    mock_db_writer = mock.MagicMock()
    mock_db_writer.execute_query.side_effect = [[1, 2, 3], Exception("mocked failure")]
    mock_get_db_writer.return_value = mock_db_writer
    qt.config.iterations = 2
    qt.start_query_run()
    assert mock_db_writer.execute_query.call_count == 2
    assert qt.success == 1
    assert qt.failure == 1
