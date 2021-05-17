import mock
from datetime import datetime
from data_generator.mongo_db_writer import MongoDbWriter
from tests.test_models import test_model


@mock.patch("data_generator.mongo_db_writer.MongoClient", autospec=True)
def test_close_connection(mock_client):
    """
    This function tests if the .close_connection() function of MongoDbWriter calls the close() function of self.client

    Pre Condition: MongoDBClient() returns a Mock Object client
        MongoDbWriter is called.
    -> Parameters of MongoDbWriter match constructor parameters

    Test Case 1:
    when calling MongoDbWriter.close_connection() self.client.close() is called
    -> client.close() is called

    :param mock_client: mocked MongoDBClient class
    """
    # Pre Condition:
    client = mock.MagicMock()
    mock_client.return_value = client
    db_writer = MongoDbWriter("localhost", "mongo", "password", "db_name", test_model)
    mock_client.assert_called_with("mongodb://mongo:password@localhost")
    # Test Case 1:
    db_writer.close_connection()
    client.close.assert_called()


@mock.patch("data_generator.mongo_db_writer.MongoClient", autospec=True)
def test_insert_stmt(mock_client):
    """
    This function tests if the .insert_stmt() function of MongoDbWriter creates the correct json object

    Pre Condition: MongoDBClient() returns a Mock Object client
        MongoDbWriter is called.
    -> Parameters of MongoDbWriter match constructor parameters

    Test Case 1:
    calling MongoDbWriter.insert_stmt()
    -> the function call has on argument
    -> the argument is the same as the document

    :param mock_client: mocked MongoDBClient class
    """
    client = mock.MagicMock()
    mock_client.return_value = client
    db_writer = MongoDbWriter("srvhost", "mongo", "password", "db_name", test_model)
    mock_client.assert_called_with("mongodb+srv://mongo:password@srvhost")
    # Test Case 1:
    db_writer.insert_stmt(
        [1586327807000],
        [{"plant": 2, "line": 2, "sensor_id": 2, "value": 6.7, "button_press": False}],
    )
    document = {
        "measurement": "temperature",
        "date": datetime.fromtimestamp(1586327807),
        "tags": {"plant": 2, "line": 2, "sensor_id": 2},
        "metrics": {"value": 6.7, "button_press": False},
    }
    # [2] because there have be 2 prior function calls on client (getting db and collection)
    args = client.mock_calls[2].args
    assert len(args) == 1
    assert args[0] == [document]


@mock.patch("data_generator.mongo_db_writer.MongoClient", autospec=True)
def test_execute_query(mock_client):
    """
    This function tests if the .execute_query() function of MongoDbWriter uses the correct argument

    Pre Condition: MongoDBClient() returns a Mock Object client
        MongoDbWriter is called.
    -> Parameters of MongoDbWriter match constructor parameters

    Test Case 1:
    calling MongoDbWriter.execute_query()
    -> the function call has on argument
    -> the argument is the same as execute_query argument

    :param mock_client: mocked MongoDBClient class
    """
    client = mock.MagicMock()
    mock_client.return_value = client
    db_writer = MongoDbWriter("srvhost", "mongo", "password", "db_name", test_model)
    # Test Case 1:
    db_writer.execute_query({"plant": 1})
    # [2] because there have be 2 prior function calls on client (getting db and collection)
    args = client.mock_calls[2].args
    assert len(args) == 1
    assert args[0] == {"plant": 1}
