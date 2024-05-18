from unittest import mock

import psycopg2
import pytest

from tests.write.schema import test_schema1, test_schema2
from tsperf.adapter.cratedbpg import CrateDbPgWireAdapter
from tsperf.model.configuration import DatabaseConnectionConfiguration
from tsperf.model.interface import DatabaseInterfaceType


@pytest.fixture
def config():
    config = DatabaseConnectionConfiguration(
        adapter=DatabaseInterfaceType.CrateDBpg,
        address="localhost:5432",
    )
    return config


@mock.patch.object(psycopg2, "connect", autospec=True)
def test_close_connection(mock_connect):
    """
    This function tests if the .close() functions of the self.conn and self.cursor objects is called

    Pre Condition: crate.client.connect() returns a Mock Object conn which returns a Mock Object
        cursor when its .cursor() function is called.
        CrateDbAdapter is called.
    -> mock_connect is called by CrateDbAdapter with values given the constructor

    Test Case 1:
    when calling CrateDbAdapter.close_connection() conn.close() and cursor.close() are called

    :param mock_connect: mocked function call from crate.client.connect()
    """
    # Pre Condition:
    conn = mock.Mock()
    cursor = mock.Mock()
    mock_connect.return_value = conn
    conn.cursor.return_value = cursor
    config = DatabaseConnectionConfiguration(
        adapter=DatabaseInterfaceType.CrateDBpg,
        address="localhost:5432",
        username="foobar",
        password=None,
        database="mydb",
    )
    db_writer = CrateDbPgWireAdapter(config=config, schema=test_schema1)
    mock_connect.assert_called_with(
        host="localhost",
        port=5432,
        user="foobar",
        password=None,
        dbname="mydb",
    )

    # Test Case 1:
    db_writer.close_connection()
    conn.close.assert_called()
    cursor.close.assert_called()


@mock.patch.object(psycopg2, "connect", autospec=True)
def test_prepare_database1(mock_connect):
    """
    This function tests if the .prepare_database() functions of the adapter uses the correct values when
        creating the the database tables

    Pre Condition: crate.client.connect() returns a Mock Object conn which returns a Mock Object
        cursor when its .cursor() function is called.
        CrateDbAdapter is called.
    -> mock_connect is called by CrateDbAdapter with values given the constructor

    Test Case 1:
    when calling CrateDbAdapter.prepare_database() the statement given to cursor.execute() contains the correct values:
    -> "temperature" is used in stmt as table name
    -> "g_ts_week" is used as partitioning column
    -> "4 SHARDS" are configured for table
    -> "number_of_replicas = 1" is set for table

    :param mock_connect: mocked function call from crate.client.connect()
    """
    # Pre Condition:
    conn = mock.Mock()
    cursor = mock.Mock()
    mock_connect.return_value = conn
    conn.cursor.return_value = cursor

    config = DatabaseConnectionConfiguration(
        adapter=DatabaseInterfaceType.CrateDBpg,
        address="localhost:8200",
        username="crate2",
        password="password2",
    )
    db_writer = CrateDbPgWireAdapter(config=config, schema=test_schema1)

    mock_connect.assert_called_with(
        host="localhost",
        port=8200,
        user="crate2",
        password="password2",
        dbname=None,
    )

    # Test Case 1:
    db_writer.prepare_database()
    stmt = cursor.execute.call_args.args[0]
    # table name is in stmt
    assert "temperature" in stmt
    # partition is default
    assert "g_ts_week" in stmt
    # shards is default
    assert "4 SHARDS" in stmt
    # replicas is default
    assert "number_of_replicas = 1" in stmt


@mock.patch.object(psycopg2, "connect", autospec=True)
def test_prepare_database2(mock_connect, config):
    """
    This function tests if the .prepare_database() functions of the adapter uses the correct values when
        creating the the database tables

    Pre Condition: crate.client.connect() returns a Mock Object conn which returns a Mock Object
        cursor when its .cursor() function is called.
        CrateDbAdapter is called.
    -> mock_connect is called by CrateDbAdapter with values given the constructor

    Test Case 1:
    A new CrateDbAdapter is initialized that overwrites default values used in prepare_database()
    -> "table" is used in stmt as table name
    -> "g_ts_day" is used as partitioning column
    -> "3 SHARDS" are configured for table
    -> "number_of_replicas = 0" is set for table

    :param mock_connect: mocked function call from crate.client.connect()
    """
    # Pre Condition:
    conn = mock.Mock()
    cursor = mock.Mock()
    mock_connect.return_value = conn
    conn.cursor.return_value = cursor

    config.table = "foobar"
    config.shards = 3
    config.replicas = 0
    config.partition = "day"
    db_writer = CrateDbPgWireAdapter(config=config, schema=test_schema2)

    db_writer.prepare_database()
    # Test Case 1:
    stmt = cursor.execute.call_args.args[0]
    # table name is in stmt
    assert "foobar" in stmt
    # partition is default
    assert "g_ts_day" in stmt
    # shards is default
    assert "3 SHARDS" in stmt
    # replicas is default
    assert "number_of_replicas = 0" in stmt


@mock.patch.object(psycopg2, "connect", autospec=True)
def test_insert_stmt(mock_connect, config):
    """
    This function tests if the .insert_stmt() functions of CrateDbAdapter uses the correct table name and arguments

    Pre Condition: crate.client.connect() returns a Mock Object conn which returns a Mock Object
        cursor when its .cursor() function is called.
        CrateDbAdapter is called.

    Test Case 1:
    when calling CrateDbAdapter.insert_stmt() the correct values are used for cursor.execute()
    -> stmt contains the correct table name
    -> values are equal to the insert_stmt arguments

    :param mock_connect: mocked function call from crate.client.connect()
    """
    # Pre Condition:
    conn = mock.Mock()
    cursor = mock.Mock()
    mock_connect.return_value = conn
    conn.cursor.return_value = cursor

    db_writer = CrateDbPgWireAdapter(config=config, schema=test_schema1)

    # Test Case 1:
    db_writer.insert_stmt(
        [1586327807000],
        [{"plant": 1, "line": 1, "sensor_id": 1, "value": 6.7, "button_press": False}],
    )
    call_arguments = cursor.execute.call_args.args
    stmt = call_arguments[0]
    values = call_arguments[1]
    assert stmt == "INSERT INTO temperature (ts, payload) (SELECT col1, col2 FROM UNNEST(?,?))"
    assert values == (
        [1586327807000],
        [{"plant": 1, "line": 1, "sensor_id": 1, "value": 6.7, "button_press": False}],
    )


@mock.patch.object(psycopg2, "connect", autospec=True)
def test_execute_query(mock_connect, config):
    """
    This function tests if the .execute_query() functions of CrateDbAdapter uses the correct query

    Pre Condition: crate.client.connect() returns a Mock Object conn which returns a Mock Object
        cursor when its .cursor() function is called.
        CrateDbAdapter is called.

    Test Case 1:
    when calling CrateDbAdapter.execute_query() the correct values are used for cursor.execute()
    -> cursor.execute is called with argument from execute_query
    -> fetchall is called

    :param mock_connect: mocked function call from crate.client.connect()
    """
    # Pre Condition:
    conn = mock.Mock()
    cursor = mock.Mock()
    mock_connect.return_value = conn
    conn.cursor.return_value = cursor

    db_writer = CrateDbPgWireAdapter(config=config, schema=test_schema1)

    # Test Case 1:
    db_writer.execute_query("SELECT * FROM temperature;")
    cursor.execute.assert_called_with("SELECT * FROM temperature;")
    cursor.fetchall.assert_called()
