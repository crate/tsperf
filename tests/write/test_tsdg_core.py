import time
from queue import Empty
from unittest import mock

import pytest

import tsperf
from tsperf.model.interface import DatabaseInterfaceType
from tsperf.write import core as dg
from tsperf.write.config import DataGeneratorConfig
from tsperf.write.model import IngestMode


@pytest.fixture(scope="function")
def config():
    config = DataGeneratorConfig(adapter=DatabaseInterfaceType.CrateDB)
    return config


@mock.patch("tsperf.adapter.AdapterManager.create", autospec=True)
def test_get_database_adapter_cratedb(mock_cratedb, config):
    dg.config = config
    dg.get_database_adapter()
    mock_cratedb.assert_called_once()
    mock_cratedb.assert_called_with(
        interface=DatabaseInterfaceType.CrateDB,
        config=DataGeneratorConfig(
            adapter=DatabaseInterfaceType.CrateDB,
            host="localhost",
            port=None,
            username=None,
            password=None,
            db_name="",
            table_name="",
            partition="week",
            shards=4,
            replicas=1,
        ),
        schema={},
    )


@pytest.mark.parametrize("adapter", list(DatabaseInterfaceType))
@mock.patch("tsperf.adapter.AdapterManager.create", autospec=True)
def test_get_database_adapter(factory_mock, adapter, config):
    dg.config = config
    dg.config.adapter = adapter
    dg.get_database_adapter()
    factory_mock.assert_called_once()
    factory_mock.assert_called_with(
        interface=adapter,
        config=DataGeneratorConfig(
            adapter=adapter,
            host="localhost",
        ),
        schema={},
    )


@mock.patch("tsperf.write.core.Channel", autospec=True, return_value=mock.MagicMock)
def test_create_channels(mock_channel, config):
    dg.config = config
    dg.config.id_start = 0
    dg.config.id_end = 0
    channels = dg.create_channels()
    assert len(channels) == 1
    assert 0 in list(channels.keys())


def test_get_sub_element():
    dg.schema = {"description": 1}
    element = dg.get_sub_element("test")
    assert element == {}
    dg.schema = {"description": 1, "test": {"x": {"z": 3, "description": 4}, "y": 2}}
    element = dg.get_sub_element("x")
    assert element == {"z": 3}
    element = dg.get_sub_element("z")
    assert element == {}


def test_get_next_value_ingest():
    dg.config.ingest_mode = IngestMode.FAST

    # no channels
    dg.get_next_value({})
    assert dg.current_values_queue.empty()

    # ingest includes timestamp
    channel = mock.MagicMock()
    channel.calculate_next_value.return_value = 1
    dg.get_next_value({"0": channel})
    assert not dg.current_values_queue.empty()
    values = dg.current_values_queue.get()
    assert "timestamps" in values
    assert "batch" in values
    assert values["batch"][0] == 1


def test_get_next_value_continuous():
    dg.config.ingest_mode = 0

    # no channels
    dg.get_next_value({})
    assert dg.current_values_queue.empty()

    # continuous does not include timestamp
    channel = mock.MagicMock()
    channel.calculate_next_value.return_value = 1
    dg.get_next_value({"0": channel})
    assert not dg.current_values_queue.empty()
    values = dg.current_values_queue.get()
    assert "timestamps" not in values
    assert 1 in values
    assert len(values) == 1


@mock.patch("tsperf.write.core.tictrack", autospec=True)
@mock.patch("tsperf.write.core.logger", autospec=True)
def test_log_stat_delta(mock_log, mock_tictrack):
    # delta not reached no output
    dg.config.stat_delta = 1
    dg.log_stat_delta(time.time())
    mock_log.info.assert_not_called()
    # no values in tic_toc_delta no output
    dg.log_stat_delta(time.time() - 2)
    mock_log.info.assert_not_called()
    # output when everything is ok
    mock_tictrack.tic_toc_delta = {"foo": [1, 2, 3, 4, 5]}
    dg.log_stat_delta(time.time() - 2)
    mock_log.info.assert_called()


@mock.patch("tsperf.write.core.logger", autospec=True)
def test_do_insert(mock_log):
    db_writer = mock.MagicMock()
    dg.do_insert(db_writer, [1], [1])
    assert tsperf.write.model.metrics.c_inserts_performed_success._value.get() == 1
    assert tsperf.write.model.metrics.c_inserts_failed._value.get() == 0
    mock_log.error.assert_not_called()
    db_writer.insert_stmt.side_effect = Exception("mocked exception")
    dg.do_insert(db_writer, [2], [2])
    assert tsperf.write.model.metrics.c_inserts_performed_success._value.get() == 1
    assert tsperf.write.model.metrics.c_inserts_failed._value.get() == 1
    mock_log.error.assert_called_once()


def test_get_insert_values():
    # current_values_queue is empty
    batch, timestamps = dg.get_insert_values(1)
    assert len(batch) == 0
    assert len(timestamps) == 0
    assert tsperf.write.model.metrics.c_values_queue_was_empty._value.get() == 1

    # current_values_queue has to few entries
    dg.current_values_queue.put({"timestamps": [1, 1, 1], "batch": [1, 2, 3]})
    batch, timestamps = dg.get_insert_values(4)
    assert len(batch) == 3
    assert len(timestamps) == 3
    assert tsperf.write.model.metrics.c_values_queue_was_empty._value.get() == 2

    # current_values_queue has to few entries
    dg.current_values_queue.put({"timestamps": [1, 1, 1], "batch": [1, 2, 3]})
    batch, timestamps = dg.get_insert_values(1)
    assert len(batch) == 3
    assert len(timestamps) == 3
    assert tsperf.write.model.metrics.c_values_queue_was_empty._value.get() == 2


@mock.patch("tsperf.write.core.get_database_adapter", autospec=True)
def test_insert_routine_auto_batch_mode(mock_get_database_adapter):
    # Immediately signal stop to not run indefinitely.
    dg.stop_queue.put(True)
    dg.config = DataGeneratorConfig(
        adapter=DatabaseInterfaceType.CrateDB,
        ingest_mode=IngestMode.FAST,
        batch_size=0,
        id_start=0,
        id_end=0,
    )
    mock_db_writer = mock.MagicMock()
    mock_get_database_adapter.return_value = mock_db_writer
    # populate current values
    for _ in range(0, 10000):
        dg.current_values_queue.put({"timestamps": [1], "batch": [1]})
    dg.insert_routine()
    mock_db_writer.insert_stmt.assert_called()
    mock_db_writer.close_connection.assert_called_once()
    dg.stop_queue.get()  # resetting the stop queue


@mock.patch("tsperf.write.core.get_database_adapter", autospec=True)
def test_insert_routine_fixed_batch_mode(mock_get_database_adapter, config):
    dg.stop_queue.put(True)  # we signal stop to not run indefinitely

    dg.config = config

    dg.config.batch_size = 5
    dg.config.ingest_mode = 1
    dg.config.id_start = 0
    dg.config.id_end = 0  # only a single channel
    mock_db_writer = mock.MagicMock()
    mock_get_database_adapter.return_value = mock_db_writer
    # populate current values
    dg.current_values_queue.put({"timestamps": [1], "batch": [1]})
    dg.insert_routine()
    mock_db_writer.insert_stmt.assert_called()
    mock_db_writer.close_connection.assert_called_once()
    dg.stop_queue.get()  # resetting the stop queue


@mock.patch("tsperf.write.core.get_database_adapter", autospec=True)
@mock.patch("tsperf.write.core.current_values_queue", autospec=True)
def test_insert_routine_empty_batch(
    mock_current_values_queue, mock_get_database_adapter
):
    dg.stop_queue.put(True)  # we signal stop to not run indefinitely
    mock_current_values_queue.empty.side_effect = [False, True]
    mock_current_values_queue.get_nowait.side_effect = Empty()
    dg.config.batch_size = 5
    dg.config.ingest_mode = 1
    dg.config.id_start = 0
    dg.config.id_end = 0  # only a single channel
    mock_db_writer = mock.MagicMock()
    mock_get_database_adapter.return_value = mock_db_writer
    dg.insert_routine()
    mock_db_writer.insert_stmt.assert_not_called()
    mock_db_writer.close_connection.assert_called_once()
    dg.stop_queue.get()  # resetting the stop queue


@mock.patch("tsperf.write.core.get_database_adapter", autospec=True)
@mock.patch("tsperf.write.core.current_values_queue", autospec=True)
def test_consecutive_insert_queue_empty(
    mock_current_values_queue, mock_get_database_adapter
):
    dg.stop_queue.put(True)  # we signal stop to not run indefinitely
    mock_current_values_queue.empty.side_effect = [False, True]
    mock_current_values_queue.get_nowait.side_effect = Empty()
    dg.config.ingest_mode = 0
    dg.config.id_start = 0
    dg.config.id_end = 0  # only a single channel
    mock_db_writer = mock.MagicMock()
    mock_get_database_adapter.return_value = mock_db_writer
    dg.consecutive_insert()
    mock_db_writer.insert_stmt.assert_not_called()
    mock_db_writer.close_connection.assert_called_once()
    dg.stop_queue.get()  # resetting the stop queue
    dg.insert_finished_queue.get()


@mock.patch("tsperf.write.core.get_database_adapter", autospec=True)
def test_consecutive_insert(mock_get_database_adapter):
    dg.stop_queue.put(True)  # we signal stop to not run indefinitely
    dg.config.ingest_mode = 0
    dg.config.id_start = 0
    dg.config.id_end = 0  # only a single channel
    mock_db_writer = mock.MagicMock()
    mock_get_database_adapter.return_value = mock_db_writer
    # populate current values
    dg.current_values_queue.put({"timestamps": [1], "batch": [1]})
    dg.current_values_queue.put({"timestamps": [1], "batch": [1]})
    dg.consecutive_insert()
    mock_db_writer.insert_stmt.assert_called()
    mock_db_writer.close_connection.assert_called_once()
    dg.stop_queue.get()  # resetting the stop queue
    dg.insert_finished_queue.get()


def test_stop_process():
    # default stop process returns false
    assert not dg.stop_process()
    # if stop_queue is not empty it returns true
    dg.stop_queue.put(1)
    assert dg.stop_process()
    dg.stop_queue.get()  # resetting the stop queue
