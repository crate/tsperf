from unittest import mock

import psycopg2.extras
import pytest

from tests.write.schema import test_schema1, test_schema3
from tsperf.adapter.postgresql import PostgreSQLAdapter
from tsperf.model.configuration import DatabaseConnectionConfiguration
from tsperf.model.interface import DatabaseInterfaceType


@pytest.fixture
def config():
    config = DatabaseConnectionConfiguration(
        adapter=DatabaseInterfaceType.PostgreSQL,
        address="localhost:5432",
    )
    return config


@mock.patch.object(psycopg2, "connect", autospec=True)
def test_close_connection(mock_connect):
    """
    This function tests if the .close() functions of the self.conn and self.cursor objects is called

    Pre Condition: psycopg2.client.connect() returns a Mock Object conn which returns a Mock Object
        cursor when its .cursor() function is called.
        TimescaleDbAdapter is called.
    -> mock_connect is called by TimescaleDbAdapter with values given the constructor

    Test Case 1:
    when calling TimescaleDbAdapter.close_connection() conn.close() and cursor.close() are called

    :param mock_connect: mocked function call from psycopg2.client.connect()
    """
    # Pre Condition:
    conn = mock.Mock()
    cursor = mock.Mock()
    mock_connect.return_value = conn
    conn.cursor.return_value = cursor

    config = DatabaseConnectionConfiguration(
        adapter=DatabaseInterfaceType.PostgreSQL,
        address="localhost:5432",
        username="foobar",
        password=None,
        database="test",
    )
    db_writer = PostgreSQLAdapter(config=config, schema=test_schema1)

    mock_connect.assert_called_with(
        host="localhost",
        port=5432,
        user="foobar",
        password=None,
        dbname="test",
    )
    # Test Case 1:
    db_writer.close_connection()
    conn.close.assert_called()
    cursor.close.assert_called()


@mock.patch.object(psycopg2, "connect", autospec=True)
def test_prepare_database1(mock_connect):
    """
    This function tests if the .prepare_database() function uses the correct statment to create the database table

    Pre Condition: psycopg2.client.connect() returns a Mock Object conn which returns a Mock Object
        cursor when its .cursor() function is called.
        TimescaleDbAdapter is called.
    -> mock_connect is called by TimescaleDbAdapter with values given the constructor

    Test Case 1: calling TimescaleDbAdapter.prepare_database()
    -> "temperature" is in stmt (table name)
    -> "ts_week" is in stmt (partitioning of hyper_table)

    :param mock_connect: mocked function call from psycopg2.client.connect()
    """
    # Pre Condition:
    conn = mock.Mock()
    cursor = mock.Mock()
    mock_connect.return_value = conn
    conn.cursor.return_value = cursor

    config = DatabaseConnectionConfiguration(
        adapter=DatabaseInterfaceType.PostgreSQL,
        address="localhost:5432",
        username="foobar",
        password="bazqux",
        database="test",
    )
    db_writer = PostgreSQLAdapter(config=config, schema=test_schema1)

    mock_connect.assert_called_with(
        host="localhost",
        port=5432,
        user="foobar",
        password="bazqux",
        dbname="test",
    )
    # Test Case 1:
    db_writer.prepare_database()
    stmt = cursor.execute.call_args.args[0]
    # table name is in stmt
    assert "temperature" in stmt
    # partition is default
    assert "ts_week" in stmt


@mock.patch.object(psycopg2, "connect", autospec=True)
def test_prepare_database2(mock_connect, config):
    """
    This function tests if the .prepare_database() function uses the correct statment to create the database table

    Pre Condition: psycopg2.client.connect() returns a Mock Object conn which returns a Mock Object
        cursor when its .cursor() function is called.
        TimescaleDbAdapter is called.

    Test Case 1: calling TimescaleDbAdapter.prepare_database() with default values overwritten by constructor arguments
    -> "table" is in stmt (table name)
    -> "ts_day is in stmt (partitioning of hyper_table)
    -> conn.commit function has been called

    :param mock_connect: mocked function call from psycopg2.client.connect()
    """
    # Pre Condition:
    conn = mock.Mock()
    cursor = mock.Mock()
    mock_connect.return_value = conn
    conn.cursor.return_value = cursor

    config.table = "table"
    config.partition = "day"
    db_writer = PostgreSQLAdapter(config=config, schema=test_schema1)

    # Test Case 1:
    db_writer.prepare_database()
    stmt = cursor.execute.call_args.args[0]
    # table name is in stmt
    assert "table" in stmt
    # partition is correctly set
    assert "ts_day" in stmt
    conn.commit.assert_called()


@mock.patch.object(psycopg2, "connect", autospec=True)
def test_prepare_database3(mock_connect, config):
    """
    This function tests if the .prepare_database() function uses the correct statment to create the database table

    Pre Condition: psycopg2.client.connect() returns a Mock Object conn which returns a Mock Object
        cursor when its .cursor() function is called.
        TimescaleDbAdapter is called.

    Test Case 1: calling TimescaleDbAdapter.prepare_database() with default values overwritten by constructor arguments
    -> tags are of type TEXT
    -> conn.commit function has been called

    :param mock_connect: mocked function call from psycopg2.client.connect()
    """
    # Pre Condition:
    conn = mock.Mock()
    cursor = mock.Mock()
    mock_connect.return_value = conn
    conn.cursor.return_value = cursor

    db_writer = PostgreSQLAdapter(config=config, schema=test_schema3)

    # Test Case 1:
    db_writer.prepare_database()
    stmt = cursor.execute.call_args.args[0]
    assert "plant TEXT" in stmt
    assert "line TEXT" in stmt
    conn.commit.assert_called()


@mock.patch.object(psycopg2, "connect", autospec=True)
def test_insert_stmt(mock_connect, config):
    """
    This function tests if the .insert_stmt() function uses the correct statement to insert values

    Pre Condition: psycopg2.client.connect() returns a Mock Object conn which returns a Mock Object
        cursor when its .cursor() function is called.
        TimescaleDbAdapter is called.

    Test Case 1: calling TimescaleDbAdapter.insert_stmt()
    -> "plant" is in stmt
    -> "line" is in stmt
    -> "sensor_id" is in stmt
    -> "value" is in stmt
    -> "button_press" is in stmt
    -> conn.commit() function has been called

    :param mock_connect: mocked function call from psycopg2.client.connect()
    """
    # Pre Condition:
    conn = mock.Mock()
    cursor = mock.Mock()
    mock_connect.return_value = conn
    conn.cursor.return_value = cursor

    db_writer = PostgreSQLAdapter(config=config, schema=test_schema1)

    # Test Case 1:
    db_writer.insert_stmt(
        [1586327807000],
        [{"plant": 1, "line": 1, "sensor_id": 1, "value": 6.7, "button_press": False}],
    )
    call_arguments = cursor.execute.call_args.args
    stmt = call_arguments[0]
    # all properties must be in statement
    assert "plant" in stmt
    assert "line" in stmt
    assert "sensor_id" in stmt
    assert "value" in stmt
    assert "button_press" in stmt
    conn.commit.assert_called()


@mock.patch.object(psycopg2, "connect", autospec=True)
def test_execute_query(mock_connect, config):
    """
    This function tests if the .execute_query() function uses the given query

    Pre Condition: psycopg2.client.connect() returns a Mock Object conn which returns a Mock Object
        cursor when its .cursor() function is called.
        TimescaleDbAdapter is called.

    Test Case 1: calling TimescaleDbAdapter.execute_query()
    -> cursor.execute function is called with given argument
    -> cursor.fetchall function is called

    :param mock_connect: mocked function call from psycopg2.client.connect()
    """
    # Pre Condition:
    conn = mock.Mock()
    cursor = mock.Mock()
    mock_connect.return_value = conn
    conn.cursor.return_value = cursor

    db_writer = PostgreSQLAdapter(config=config, schema=test_schema1)

    db_writer.execute_query("SELECT * FROM temperature;")
    cursor.execute.assert_called_with("SELECT * FROM temperature;")
    cursor.fetchall.assert_called()
