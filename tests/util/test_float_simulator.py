import pytest
import statistics
from float_simulator import FloatSimulator


float_model = {
    "mean": 6.4,
    "min": 6.0,
    "max": 7.4,
    "stdev": 0.2,
    "variance": 0.03,
    "error_rate": 0.001,
    "error_length": 1.08,
}


def test_calculate_next_value_float_no_error():
    """
    This function tests if the FloatSimulator produces values that match the model

    Pre Condition: FloatSimulator initialized with float_model without error values

    Test Case 1: 10000 values for FloatSensor are created
    -> mean of generated values == mean of model +- 0.5
    -> stdev of generated values == stdev of model +- 0.1
    -> error_rate of generated values == 0
    """
    # Pre Condition:
    float_sensor = FloatSimulator(
        float_model["mean"],
        float_model["min"],
        float_model["max"],
        float_model["stdev"],
        float_model["variance"],
    )
    # we want to test if the values we create match the model we used to initialize the sensor
    results = []
    # Test Case 1:
    for i in range(0, 100000):
        results.append(float_sensor.calculate_next_value())
    mean = statistics.mean(results)
    stdev = statistics.stdev(results)
    error_rate = float_sensor.error_count / (
        float_sensor.value_count + float_sensor.error_count
    )
    assert mean == pytest.approx(float_model["mean"], abs=0.3)
    assert stdev == pytest.approx(float_model["stdev"], abs=0.15)
    assert error_rate == 0


def test_calculate_next_value_float_with_error():
    """
    This function tests if the FloatSimulator produces values that match the model

    Pre Condition: FloatSimulator initialized with float_model with error values

    Test Case 1: 10000 values for FloatSensor are created
    -> mean of generated values == mean of model +- 0.5
    -> stdev of generated values == stdev of model +- 0.1
    -> error_rate of generated values == error_rate of model +- 0.001
    """
    # Pre Condition:
    float_sensor = FloatSimulator(
        float_model["mean"],
        float_model["min"],
        float_model["max"],
        float_model["stdev"],
        float_model["variance"],
        float_model["error_rate"],
        float_model["error_length"],
    )
    # we want to test if the values we create match the model we used to initialize the sensor
    results = []
    # Test Case 1:
    for i in range(0, 100000):
        results.append(float_sensor.calculate_next_value())
    mean = statistics.mean(results)
    stdev = statistics.stdev(results)
    error_rate = float_sensor.error_count / (
        float_sensor.value_count + float_sensor.error_count
    )
    assert mean == pytest.approx(float_model["mean"], abs=0.3)
    assert stdev == pytest.approx(float_model["stdev"], abs=0.15)
    assert error_rate == pytest.approx(float_model["error_rate"], abs=0.001)
