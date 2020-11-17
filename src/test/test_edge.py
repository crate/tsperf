import pytest
import numpy
import statistics
from modules.edge import Edge, FloatSensor, BoolSensor
from test.test_models import metrics_model_float1_bool1, metrics_model_string, \
    tag_model_plant100_line5_sensorId, float_model, bool_model


def test_init_sensors():
    """
    This function tests if the Edge Object is correctly initialized

    Test Case 1:
    Edge is initialized with:
    id: 1
    tags: valid tag model
    metrics: metrics model containing one float and one bool sensor
    -> FloatSensor must be in sensor_types
    -> BoolSensor must be in sensor_types

    Test Case 2:
    Edge is initialized with:
    id: 1
    tags: valid tag model
    metrics: metrics model containing one string sensor
    -> Constructor raises NotImplementedError
    """
    # Test Case 1:
    edge = Edge(1, tag_model_plant100_line5_sensorId, metrics_model_float1_bool1)
    sensor_types = []
    for sensor in edge.sensors:
        sensor_types.append(sensor.__class__.__name__)
    assert "FloatSensor" in sensor_types
    assert "BoolSensor" in sensor_types

    # Test Case 2:
    with pytest.raises(NotImplementedError):
        Edge(1, tag_model_plant100_line5_sensorId, metrics_model_string)


def test_calculate_next_value_edge():
    """
    This function tests if the Edge Object correctly calculates the next value of it's sensors

    Pre Condition: Edge Object created with id 1, a valid tag model and a the metrics_model_float1_bool1 model

    Test Case 1: the first value of the edge object is calculated
    -> "plant" tag is in batch
    -> "plant" values is 1
    -> "line" tag is in batch
    -> "line" value is 1
    -> "sensor_id" tag is in batch
    -> "sensor_id" value is 1
    -> "value" metric is in batch
    -> "value" value is 6.3 +-0.3
    -> "button_press" is in batch
        there is a 1:100 chance that button_press is true based on the model that's why it's value is not tested

    Test Case 2: another 1000 values for the edge object are calculated to see if button_press is at least True once
        and value is not the same value each time
    -> True is contained in button_press array
    -> length of unique values in values array is bigger than 1
    """
    # Pre Condition
    edge = Edge(1, tag_model_plant100_line5_sensorId, metrics_model_float1_bool1)
    results = []
    # Test Case 1.
    batch = edge.calculate_next_value()
    assert "plant" in batch
    assert batch["plant"] == 0
    assert "line" in batch
    assert batch["line"] == 0
    assert "sensor_id" in batch
    assert batch["sensor_id"] == 1
    assert "value" in batch
    assert batch["value"] == pytest.approx(6.3, abs=0.3)
    assert "button_press" in batch
    results.append(batch)

    # Test Case 2:
    # because button_press has a probability of 1:100 to be True, we do a thousand operations to get True for sure
    for i in range(0, 1000):
        results.append(edge.calculate_next_value())

    button_press = []
    values = []
    for result in results:
        button_press.append(result["button_press"])
        values.append(result["value"])
    assert True in button_press
    assert len(numpy.unique(values)) > 1


def test_calculate_next_value_float():
    """
    This function tests if the FloatSensor produces values that match the model

    Pre Condition: FloatSensor initialized with float_model

    Test Case 1: 10000 values for FloatSensor are created
    -> mean of generated values == mean of model +- 0.5
    -> stdev of generated values == stdev of model +- 0.1
    -> error_rate of generated values == error_rate of model +- 0.001
    """
    # Pre Condition:
    float_sensor = FloatSensor(float_model)
    # we want to test if the values we create match the model we used to initialize the sensor
    results = []
    # Test Case 1:
    for i in range(0, 100000):
        results.append(float_sensor.calculate_next_value())
    mean = statistics.mean(results)
    stdev = statistics.stdev(results)
    error_rate = float_sensor.error_count / (float_sensor.value_count + float_sensor.error_count)
    assert mean == pytest.approx(float_model["mean"]["value"], abs=0.5)
    assert stdev == pytest.approx(float_model["stdev"]["value"], abs=0.15)
    assert error_rate == pytest.approx(float_model["error_rate"]["value"], abs=0.001)


def test_calculate_next_value_bool():
    """
    This function tests if the BoolSensor produces values that match the model

    Pre Condition: BoolSensor initialized with bool_model

    Test Case 1: 10000 values for BoolSensor are created
    -> true_ratio of generated values == true_ratio of model +- 0.001
    """
    # Pre Condition:
    bool_sensor = BoolSensor(bool_model)
    results = []
    # Test Case 1:
    for i in range(0, 10000):
        results.append(bool_sensor.calculate_next_value())
    sum_true = sum(results)
    true_ratio = sum_true / len(results)
    assert true_ratio == pytest.approx(bool_model["true_ratio"]["value"], abs=0.001)
