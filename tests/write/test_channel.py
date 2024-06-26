import numpy
import pytest

from tests.write.schema import (
    bool_schema,
    channel_schema_float1_bool1,
    channel_schema_string,
    tag_schema_list,
    tag_schema_plant100_line5_sensorId,
)
from tsperf.write.model.channel import Channel
from tsperf.write.model.sensor import BoolSensor


def test_init_sensors():
    """
    This function tests if the Channel Object is correctly initialized

    Test Case 1:
    Channel is initialized with:
    id: 1
    tags: valid tag schema
    fields: fields schema containing one float and one bool sensor
    -> FloatSensor must be in sensor_types
    -> BoolSensor must be in sensor_types

    Test Case 2:
    Channel is initialized with:
    id: 1
    tags: valid tag schema
    fields: fields schema containing one string sensor
    -> Constructor raises NotImplementedError
    """
    # Test Case 1:
    channel = Channel(1, tag_schema_plant100_line5_sensorId, channel_schema_float1_bool1)
    sensor_types = []
    for sensor in channel.sensors:
        sensor_types.append(sensor.__class__.__name__)
    assert "FloatSensor" in sensor_types
    assert "BoolSensor" in sensor_types

    # Test Case 2:
    with pytest.raises(NotImplementedError):
        Channel(1, tag_schema_plant100_line5_sensorId, channel_schema_string)


def test_calculate_next_value_channel():
    """
    This function tests if the Channel Object correctly calculates the next value of it's sensors

    Pre Condition: Channel Object created with id 1, a valid tag schema and a the `channel_schema_float1_bool1` schema

    Test Case 1: the first value of the channel object is calculated
    -> "plant" tag is in batch
    -> "plant" values is 1
    -> "line" tag is in batch
    -> "line" value is 1
    -> "sensor_id" tag is in batch
    -> "sensor_id" value is 1
    -> "value" metric is in batch
    -> "value" value is not None
    -> "button_press" is in batch
    -> "button_press" is not None

    Test Case 2: another 1000 values for the channel object are calculated to see if button_press is at least True once
        and value is not the same value each time
    -> True is contained in button_press array
    -> length of unique values in values array is bigger than 1
    """
    # Pre Condition
    channel = Channel(1, tag_schema_plant100_line5_sensorId, channel_schema_float1_bool1)
    results = []
    # Test Case 1.
    batch = channel.calculate_next_value()
    assert "plant" in batch
    assert batch["plant"] == 0
    assert "line" in batch
    assert batch["line"] == 0
    assert "sensor_id" in batch
    assert batch["sensor_id"] == 1
    assert "value" in batch
    assert batch["value"] is not None
    assert "button_press" in batch
    assert batch["button_press"] is not None
    results.append(batch)

    # Test Case 2:
    # because button_press has a probability of 1:100 to be True, we do a thousand operations to get True for sure
    for _ in range(0, 1000):
        results.append(channel.calculate_next_value())

    button_press = []
    values = []
    for result in results:
        button_press.append(result["button_press"])
        values.append(result["value"])
    assert True in button_press
    assert len(numpy.unique(values)) > 1


def test_calculate_next_value_bool():
    """
    This function tests if the BoolSensor produces values that match the schema

    Pre Condition: BoolSensor initialized with `bool_schema`

    Test Case 1: 10000 values for BoolSensor are created
    -> true_ratio of generated values == true_ratio of schema +- 0.001
    """
    # Pre Condition:
    bool_sensor = BoolSensor(bool_schema)
    results = []
    # Test Case 1:
    for _ in range(0, 10000):
        results.append(bool_sensor.calculate_next_value())
    sum_true = sum(results)
    true_ratio = sum_true / len(results)
    assert true_ratio == pytest.approx(bool_schema["true_ratio"]["value"], abs=0.001)


def test_calculate_next_value_tag_list():
    results = [
        ["A", "L1"],
        ["A", "L2"],
        ["A", "L3"],
        ["B", "L1"],
        ["B", "L2"],
        ["B", "L3"],
        ["C", "L1"],
        ["C", "L2"],
        ["C", "L3"],
        ["D", "L1"],
        ["D", "L2"],
        ["D", "L3"],
        ["E", "L1"],
        ["E", "L2"],
        ["E", "L3"],
    ]
    for i in range(1, 16):
        channel = Channel(i, tag_schema_list, channel_schema_float1_bool1)
        payload = channel.calculate_next_value()
        assert payload["plant"] == results[i - 1][0]
        assert payload["line"] == results[i - 1][1]
