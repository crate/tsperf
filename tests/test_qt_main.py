import mock
import pytest
import query_timer.__main__ as qt


@mock.patch("query_timer.__main__.CrateDbWriter", autospec=True)
@mock.patch("query_timer.__main__.TimescaleDbWriter", autospec=True)
@mock.patch("query_timer.__main__.InfluxDbWriter", autospec=True)
@mock.patch("query_timer.__main__.MsSQLDbWriter", autospec=True)
@mock.patch("query_timer.__main__.PostgresDbWriter", autospec=True)
@mock.patch("query_timer.__main__.TimeStreamWriter", autospec=True)
def test_get_db_writer(
    mock_timestream, mock_postgres, mock_mssql, mock_influx, mock_timescale, mock_crate
):
    qt.config.database = 0
    qt.get_db_writer()
    mock_crate.assert_called_once()
    qt.config.database = 1
    qt.get_db_writer()
    mock_timescale.assert_called_once()
    qt.config.database = 2
    qt.get_db_writer()
    mock_influx.assert_called_once()
    qt.config.database = 3
    with pytest.raises(ValueError):
        qt.get_db_writer()
    qt.config.database = 4
    qt.get_db_writer()
    mock_postgres.assert_called_once()
    qt.config.database = 5
    qt.get_db_writer()
    mock_timestream.assert_called_once()
    qt.config.database = 6
    qt.get_db_writer()
    mock_mssql.assert_called_once()
    qt.config.database = 7
    db_writer = qt.get_db_writer()
    assert db_writer is None


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


@mock.patch("query_timer.__main__.get_db_writer", autospec=True)
def test_start_query_run(mock_get_db_writer):
    mock_db_writer = mock.MagicMock()
    mock_db_writer.execute_query.side_effect = [[1, 2, 3], Exception("mocked failure")]
    mock_get_db_writer.return_value = mock_db_writer
    qt.config.iterations = 2
    qt.start_query_run()
    assert mock_db_writer.execute_query.call_count == 2
    assert qt.success == 1
    assert qt.failure == 1
