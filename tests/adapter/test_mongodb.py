from datetime import datetime
from unittest import mock

import pytest

from tests.write.schema import test_schema1
from tsperf.adapter.mongodb import MongoDbAdapter
from tsperf.model.configuration import DatabaseConnectionConfiguration
from tsperf.model.interface import DatabaseInterfaceType


@pytest.fixture
def config():
    config = DatabaseConnectionConfiguration(
        adapter=DatabaseInterfaceType.MongoDB,
        address="localhost:27017",
        database="foobar",
    )
    return config


@mock.patch("tsperf.adapter.mongodb.MongoClient", autospec=True)
def test_close_connection(mock_client, config):
    """
    This function tests if the .close_connection() function of MongoDbAdapter calls the close() function of self.client

    Pre Condition: MongoDBClient() returns a Mock Object client
        MongoDbAdapter is called.
    -> Parameters of MongoDbAdapter match constructor parameters

    Test Case 1:
    when calling MongoDbAdapter.close_connection() self.client.close() is called
    -> client.close() is called

    :param mock_client: mocked MongoDBClient class
    """
    # Pre Condition:
    client = mock.MagicMock()
    mock_client.return_value = client

    config.username = "mongo"
    config.password = "password"
    db_writer = MongoDbAdapter(config=config, schema=test_schema1)

    mock_client.assert_called_with("mongodb://mongo:password@localhost")
    # Test Case 1:
    db_writer.close_connection()
    client.close.assert_called()


@mock.patch("tsperf.adapter.mongodb.MongoClient", autospec=True)
def test_insert_stmt(mock_client, config):
    """
    This function tests if the .insert_stmt() function of MongoDbAdapter creates the correct json object

    Pre Condition: MongoDBClient() returns a Mock Object client
        MongoDbAdapter is called.
    -> Parameters of MongoDbAdapter match constructor parameters

    Test Case 1:
    calling MongoDbAdapter.insert_stmt()
    -> the function call has on argument
    -> the argument is the same as the document

    :param mock_client: mocked MongoDBClient class
    """
    client = mock.MagicMock()
    mock_client.return_value = client
    config.address = "srvhost:27017"
    db_writer = MongoDbAdapter(config=config, schema=test_schema1)
    mock_client.assert_called_with("mongodb+srv://srvhost")
    # Test Case 1:
    db_writer.insert_stmt(
        [1586327807000],
        [{"plant": 2, "line": 2, "sensor_id": 2, "value": 6.7, "button_press": False}],
    )
    document = {
        "measurement": "temperature",
        "date": datetime.fromtimestamp(1586327807),
        "tags": {"plant": 2, "line": 2, "sensor_id": 2},
        "fields": {"value": 6.7, "button_press": False},
    }
    # [2] because there have be 2 prior function calls on client (getting db and collection)
    args = client.mock_calls[2].args
    assert len(args) == 1
    assert args[0] == [document]


@mock.patch("tsperf.adapter.mongodb.MongoClient", autospec=True)
def test_execute_query(mock_client, config):
    """
    This function tests if the .execute_query() function of MongoDbAdapter uses the correct argument

    Pre Condition: MongoDBClient() returns a Mock Object client
        MongoDbAdapter is called.
    -> Parameters of MongoDbAdapter match constructor parameters

    Test Case 1:
    calling MongoDbAdapter.execute_query()
    -> the function call has on argument
    -> the argument is the same as execute_query argument

    :param mock_client: mocked MongoDBClient class
    """
    client = mock.MagicMock()
    mock_client.return_value = client
    db_writer = MongoDbAdapter(config=config, schema=test_schema1)
    # Test Case 1:
    db_writer.execute_query({"plant": 1})
    # [2] because there have be 2 prior function calls on client (getting db and collection)
    args = client.mock_calls[2].args
    assert len(args) == 1
    assert args[0] == {"plant": 1}
