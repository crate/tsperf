from unittest import mock

import pytest

from tests.write.schema import test_schema1
from tsperf.adapter.timestream import AmazonTimestreamAdapter
from tsperf.model.configuration import DatabaseConnectionConfiguration
from tsperf.model.interface import DatabaseInterfaceType


@pytest.fixture
def config():
    config = DatabaseConnectionConfiguration(
        adapter=DatabaseInterfaceType.Timestream,
        # TODO: address="ingest-cell1.timestream.us-west-2.amazonaws.com",
    )
    return config


@mock.patch("tsperf.adapter.timestream.boto3", autospec=True)
def test_close_connection(mock_boto, config):
    """
    Test if the .close_connection() function of AmazonTimestreamAdapter calls the close() function of self.client

    Test Case 1:boto.session.Session() returns a Mock Object session
        AmazonTimestreamAdapter is called.
    -> Parameters of AmazonTimestreamAdapter match constructor parameters

    :param mock_boto: mocked boto3 class
    """
    session = mock.MagicMock()
    mock_boto.session.Session.return_value = session

    config = DatabaseConnectionConfiguration(
        adapter=DatabaseInterfaceType.Timestream,
        # TODO: address="ingest-cell1.timestream.us-west-2.amazonaws.com",
        aws_access_key_id="foobar",
        aws_secret_access_key="bazqux",
        aws_region_name="us-west-2",
    )
    _ = AmazonTimestreamAdapter(config=config, schema=test_schema1)

    mock_boto.session.Session.assert_called_with("foobar", aws_secret_access_key="bazqux", region_name="us-west-2")


@mock.patch("tsperf.adapter.timestream.boto3", autospec=True)
def test_insert_stmt(mock_boto, config):
    """
    This function tests if the .insert_stmt() function of AmazonTimestreamAdapter creates the correct json object

    Pre Condition: boto.session.Session() returns a Mock Object session
        AmazonTimestreamAdapter is called.
    -> Parameters of AmazonTimestreamAdapter match constructor parameters

    Test Case 1:
    calling AmazonTimestreamAdapter.insert_stmt()
    -> the function call has on argument
    -> the argument is the same as the record

    :param mock_boto: mocked boto3 class
    """
    session = mock.MagicMock()
    mock_boto.session.Session.return_value = session
    write_client = mock.MagicMock()
    session.client.return_value = write_client

    db_writer = AmazonTimestreamAdapter(config=config, schema=test_schema1)

    # Test Case 1:
    db_writer.insert_stmt(
        [1586327807000],
        [{"plant": 2, "line": 2, "sensor_id": 2, "value": 6.7, "button_press": False}],
    )
    """
    records = [
        {
            "Time": "1586327807000",
            "Dimensions": [
                {"Name": "plant", "Value": "2"},
                {"Name": "line", "Value": "2"},
                {"Name": "sensor_id", "Value": "2"},
            ],
            "MeasureName": "value",
            "MeasureValue": "6.7",
            "MeasureValueType": "DOUBLE",
        },
        {
            "Time": "1586327807000",
            "Dimensions": [
                {"Name": "plant", "Value": "2"},
                {"Name": "line", "Value": "2"},
                {"Name": "sensor_id", "Value": "2"},
            ],
            "MeasureName": "button_press",
            "MeasureValue": "False",
            "MeasureValueType": "BOOLEAN",
        },
    ]
    """
    write_client.write_records.assert_called_once()
    args = write_client.write_records.call_args.kwargs
    rec_arg = [
        {
            "MeasureName": "value",
            "MeasureValue": "6.7",
            "MeasureValueType": "DOUBLE",
            "Time": "1586327807000",
        },
        {
            "MeasureName": "button_press",
            "MeasureValue": "False",
            "MeasureValueType": "BOOLEAN",
            "Time": "1586327807000",
        },
    ]
    common_attr = {
        "Dimensions": [
            {"Name": "plant", "Value": "2"},
            {"Name": "line", "Value": "2"},
            {"Name": "sensor_id", "Value": "2"},
        ]
    }
    assert len(args) == 4
    assert args["Records"] == rec_arg
    assert args["CommonAttributes"] == common_attr


@mock.patch("tsperf.adapter.timestream.boto3", autospec=True)
def test_execute_query(mock_boto, config):
    """
    This function tests if the .execute_query() function of AmazonTimestreamAdapter uses the correct argument

    Pre Condition: boto.session.Session() returns a Mock Object session
        AmazonTimestreamAdapter is called.

    Test Case 1:
    calling AmazonTimestreamAdapter.execute_query()
    -> the function call has on argument
    -> the argument is the same as execute_query argument

    :param mock_boto: mocked boto3 class
    """
    session = mock.MagicMock()
    mock_boto.session.Session.return_value = session
    query_client = mock.MagicMock()
    session.client.return_value = query_client
    paginator = mock.MagicMock()
    query_client.get_paginator.return_value = paginator

    # Test Case 1:
    db_writer = AmazonTimestreamAdapter(config=config, schema=test_schema1)
    query = "SELECT * FROM temperature;"
    db_writer.execute_query(query)
    paginator.paginate.assert_called_once()
    args = paginator.paginate.call_args.kwargs
    assert len(args) == 1
    assert args["QueryString"] == query


@mock.patch("tsperf.adapter.timestream.boto3", autospec=True)
def test_prepare_database_not_existing_db_and_table(mock_boto, config):
    """
    This function tests if the .execute_query() function of AmazonTimestreamAdapter uses the correct argument

    Pre Condition: boto.session.Session() returns a Mock Object session
        AmazonTimestreamAdapter is called.

    Test Case 1:
    calling AmazonTimestreamAdapter.prepare_database()
    -> write_client.create_database is called once
    -> write_client.create_table is called once

    :param mock_boto: mocked boto3 class
    """
    session = mock.MagicMock()
    mock_boto.session.Session.return_value = session
    write_client = mock.MagicMock()
    session.client.return_value = write_client

    # Test Case 1:
    db_writer = AmazonTimestreamAdapter(config=config, schema=test_schema1)
    db_writer.prepare_database()
    write_client.create_database.assert_called_once()
    write_client.create_table.assert_called_once()


@mock.patch("tsperf.adapter.timestream.boto3", autospec=True)
def test_prepare_database_existing_db_and_table(mock_boto, config):
    """
    This function tests if the .execute_query() function of AmazonTimestreamAdapter uses the correct argument

    Pre Condition: boto.session.Session() returns a Mock Object session
        AmazonTimestreamAdapter is called.

    Test Case 1:
    calling AmazonTimestreamAdapter.prepare_database()
    -> write_client.create_database is called once
    -> write_client.create_table is called once

    :param mock_boto: mocked boto3 class
    """
    session = mock.MagicMock()
    mock_boto.session.Session.return_value = session
    write_client = mock.MagicMock()
    session.client.return_value = write_client

    # Test Case 1:
    db_writer = AmazonTimestreamAdapter(config=config, schema=test_schema1)
    write_client.create_database.side_effect = Exception()
    write_client.create_table.side_effect = Exception()
    db_writer.prepare_database()
    write_client.create_database.assert_called_once()
    write_client.create_table.assert_called_once()
