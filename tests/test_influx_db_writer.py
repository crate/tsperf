import mock
from dotmap import DotMap
from influxdb_client import Bucket
from influxdb_client.client.write_api import Point
from data_generator.influx_db_writer import InfluxDbWriter
from tests.test_models import test_model


@mock.patch("data_generator.influx_db_writer.InfluxDBClient", autospec=True)
def test_close_connection(mock_client):
    """
    This function tests if the .close_connection() function of InfluxDbWriter calls the close() function of self.client

    Pre Condition: InfluxDBClient() returns a Mock Object client
        InfluxDbWriter is called.
    -> Parameters of InfluxDbWriter match constructor parameters

    Test Case 1:
    when calling InfluxDbWriter.close_connection() self.client.close() is called
    -> client.close() is called

    :param mock_client: mocked InfluxDBClient class
    """
    # Pre Condition:
    client = mock.Mock()
    mock_client.return_value = client
    db_writer = InfluxDbWriter("localhost", "token", "org", test_model)
    mock_client.assert_called_with("localhost", token="token")
    # Test Case 1
    db_writer.close_connection()
    client.close.assert_called()


@mock.patch("data_generator.influx_db_writer.InfluxDBClient", autospec=True)
def test_prepare_database_bucket_exists(mock_client):
    """
    This function tests if the .prepare_database() function of InfluxDbWriter loads the correct bucket

    Pre Condition: InfluxDBClient() returns a Mock Object client
        client.buckets_api() returns a Mock Object buckets_api
        buckets_api.find_buckets() returns a DotMap Object where .buckets returns a list of influx Buckets
        InfluxDbWriter is called.
    -> Parameters of InfluxDbWriter match constructor parameters

    Test Case 1:
    calling InfluxDbWriter.prepare_database() with a already existing Bucket in the Influx DB
    -> buckets_api.create_bucket() is not called

    :param mock_client: mocked InfluxDBClient class
    """
    # Pre Condition:
    client = mock.Mock()
    buckets_api = mock.Mock()
    client.buckets_api.return_value = buckets_api
    mock_client.return_value = client
    db_writer = InfluxDbWriter("localhost", "token1", "org1", test_model)
    mock_client.assert_called_with("localhost", token="token1")
    bucket_list = DotMap()
    bucket_list.buckets = [
        Bucket(name="", retention_rules=[]),
        Bucket(name="temperature", retention_rules=[]),
    ]
    buckets_api.find_buckets.return_value = bucket_list
    # Test Case 1:
    db_writer.prepare_database()
    buckets_api.create_bucket.assert_not_called()


@mock.patch("data_generator.influx_db_writer.InfluxDBClient", autospec=True)
def test_prepare_database_bucket_not_exists(mock_client):
    """
    This function tests if the .prepare_database() function of InfluxDbWriter loads the correct bucket

    Pre Condition: InfluxDBClient() returns a Mock Object client
        client.buckets_api() returns a Mock Object buckets_api
        buckets_api.find_buckets() returns a DotMap Object where .buckets returns a list of influx Buckets
        InfluxDbWriter is called.
    -> Parameters of InfluxDbWriter match constructor parameters

    Test Case 1:
    calling InfluxDbWriter.prepare_database() with the matching Bucket not in bucket_list
    -> buckets_api.create_bucket() is called

    :param mock_client: mocked InfluxDBClient class
    """
    # Pre Condition:
    client = mock.Mock()
    buckets_api = mock.Mock()
    client.buckets_api.return_value = buckets_api
    mock_client.return_value = client
    db_writer = InfluxDbWriter("localhost", "token2", "org2", test_model)
    mock_client.assert_called_with("localhost", token="token2")
    bucket_list = DotMap()
    bucket_list.buckets = [
        Bucket(name="x", retention_rules=[]),
        Bucket(name="y", retention_rules=[]),
    ]
    buckets_api.find_buckets.return_value = bucket_list
    # Test Case 1:
    db_writer.prepare_database()
    buckets_api.create_bucket.assert_called()


@mock.patch("data_generator.influx_db_writer.InfluxDBClient", autospec=True)
def test_insert_stmt(mock_client):
    """
    This function tests if the .insert_stmt() function of InfluxDbWriter uses the correct arguments for write_api.write

    Pre Condition: InfluxDBClient() returns a Mock Object client
        client.write_api() returns a Mock Object write_api
        InfluxDbWriter is called.

    Test Case 1:
    calling InfluxDbWriter.insert_stmt() with one timestamp and one batch and check write parameters
    -> org is "org"
    -> data is of type list
    -> data is of length 1
    -> element in data is of type influxdb_client.Point

    :param mock_client: mocked InfluxDBClient class
    """
    # Pre Condition:
    client = mock.Mock()
    write_api = mock.Mock()
    mock_client.return_value = client
    client.write_api.return_value = write_api
    db_writer = InfluxDbWriter("localhost", "token", "org", test_model)
    # Test Case 1:
    db_writer.insert_stmt(
        [1586327807000],
        [{"plant": 2, "line": 2, "sensor_id": 2, "value": 6.7, "button_press": False}],
    )
    call_arguments = write_api.write.call_args[1]
    org = call_arguments["org"]
    data = call_arguments["record"]
    assert org == "org"
    assert isinstance(data, list)
    assert len(data) == 1
    assert isinstance(data[0], Point)


@mock.patch("data_generator.influx_db_writer.InfluxDBClient", autospec=True)
def test_execute_query(mock_client):
    """
    This function tests if the .execute_query() function of InfluxDbWriter uses the correct arguments

    Pre Condition: InfluxDBClient() returns a Mock Object client
        client.query_api() returns a Mock Object query_api
        InfluxDbWriter is called.

    Test Case 1:
    calling InfluxDbWriter.execute_query()
    -> query_api.query is called with the same query given execute_query

    :param mock_client: mocked InfluxDBClient class
    """
    client = mock.Mock()
    query_api = mock.Mock()
    mock_client.return_value = client
    client.query_api.return_value = query_api
    db_writer = InfluxDbWriter("localhost", "token", "org", test_model)
    db_writer.execute_query("SELECT * FROM temperature;")
    query_api.query.assert_called_with("SELECT * FROM temperature;")
