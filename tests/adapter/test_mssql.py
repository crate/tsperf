from unittest import mock

import pytest

from tests.write.schema import test_schema1, test_schema3
from tsperf.adapter.mssql import MsSQLDbAdapter
from tsperf.model.configuration import DatabaseConnectionConfiguration
from tsperf.model.interface import DatabaseInterfaceType

pyodbc = pytest.importorskip("pyodbc")


@pytest.fixture
def config():
    config = DatabaseConnectionConfiguration(
        adapter=DatabaseInterfaceType.MicrosoftSQL,
        address="localhost:1433",
    )
    return config


@mock.patch.object(pyodbc, "connect", autospec=True)
def test_prepare_database1(mock_connect, config):
    """
    This function tests if the .prepare_database() function uses the correct statement to create the database table

    Pre Condition: pyodbc.connect() returns a Mock Object conn which returns a Mock Object
        cursor when its .cursor() function is called.
        MsSQLDbAdapter is called.
    -> mock_connect is called by MsSQLDbAdapter with values given the constructor

    Test Case 1: calling MsSQLDbAdapter.prepare_database()
    -> "temperature" is in stmt (table name)

    :param mock_connect: mocked function call from psycopg2.client.connect()
    """
    # Pre Condition:
    conn = mock.Mock()
    cursor = mock.Mock()
    mock_connect.return_value = conn
    conn.cursor.return_value = cursor

    config = DatabaseConnectionConfiguration(
        adapter=DatabaseInterfaceType.MicrosoftSQL,
        address="localhost:1433",
        username="foobar",
        password="bazqux",
        database="testdrive",
        schema=test_schema1,
    )
    db_writer = MsSQLDbAdapter(config=config, schema=test_schema1)

    connection_string = (
        "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;"
        "DATABASE=testdrive;UID=foobar;PWD=bazqux;CONNECTION TIMEOUT=10;"
    )
    mock_connect.assert_called_with(connection_string, timeout=15)
    # Test Case 1:
    db_writer.prepare_database()
    stmt = cursor.execute.call_args.args[0]
    # table name is in stmt
    assert "temperature" in stmt


@mock.patch.object(pyodbc, "connect", autospec=True)
def test_prepare_database2(mock_connect, config):
    """
    This function tests if the .prepare_database() function uses the correct statment to create the database table

    Pre Condition: pyodbc.connect() returns a Mock Object conn which returns a Mock Object
        cursor when its .cursor() function is called.
        MsSQLDbAdapter is called.

    Test Case 1: calling MsSQLDbAdapter.prepare_database() with default values overwritten by constructor arguments
    -> "table" is in stmt (table name)
    -> conn.commit function has been called

    :param mock_connect: mocked function call from psycopg2.client.connect()
    """
    # Pre Condition:
    conn = mock.Mock()
    cursor = mock.Mock()
    mock_connect.return_value = conn
    conn.cursor.return_value = cursor

    config.table = "foobar"
    db_writer = MsSQLDbAdapter(config=config, schema=test_schema1)

    # Test Case 1:
    db_writer.prepare_database()
    stmt = cursor.execute.call_args.args[0]
    # table name is in stmt
    assert "foobar" in stmt
    conn.commit.assert_called()


@mock.patch.object(pyodbc, "connect", autospec=True)
def test_prepare_database3(mock_connect, config):
    """
    This function tests if the .prepare_database() function uses the correct statement to create the database table

    Pre Condition: pyodbc.connect() returns a Mock Object conn which returns a Mock Object
        cursor when its .cursor() function is called.
        MsSQLDbAdapter is called.

    Test Case 1: calling MsSQLDbAdapter.prepare_database() with default values overwritten by constructor arguments
    -> tags are of type STRING
    -> conn.commit function has been called

    :param mock_connect: mocked function call from psycopg2.client.connect()
    """
    # Pre Condition:
    conn = mock.Mock()
    cursor = mock.Mock()
    mock_connect.return_value = conn
    conn.cursor.return_value = cursor

    db_writer = MsSQLDbAdapter(config=config, schema=test_schema3)

    # Test Case 1:
    db_writer.prepare_database()
    stmt = cursor.execute.call_args.args[0]
    assert "plant TEXT" in stmt
    assert "line TEXT" in stmt
    conn.commit.assert_called()


@mock.patch.object(pyodbc, "connect", autospec=True)
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

    db_writer = MsSQLDbAdapter(config=config, schema=test_schema1)

    # Test Case 1:
    db_writer.insert_stmt(
        [1586327807000],
        [{"plant": 1, "line": 1, "sensor_id": 1, "value": 6.7, "button_press": False}],
    )
    call_arguments = cursor.executemany.call_args.args
    stmt = call_arguments[0]
    # all properties must be in statement
    assert "plant" in stmt
    assert "line" in stmt
    assert "sensor_id" in stmt
    assert "value" in stmt
    assert "button_press" in stmt
    conn.commit.assert_called()


@mock.patch.object(pyodbc, "connect", autospec=True)
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

    db_writer = MsSQLDbAdapter(config=config, schema=test_schema1)

    db_writer.execute_query("SELECT * FROM temperature;")
    cursor.execute.assert_called_with("SELECT * FROM temperature;")
    cursor.fetchall.assert_called()
