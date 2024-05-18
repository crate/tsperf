import statistics

import pytest

from tsperf.util.float_simulator import FloatSimulator

float_schema = {
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
    This function tests if the FloatSimulator produces values that match the schema

    Pre Condition: FloatSimulator initialized with float_schema without error values

    Test Case 1: 10000 values for FloatSensor are created
    -> mean of generated values == mean of schema +- 0.5
    -> stdev of generated values == stdev of schema +- 0.1
    -> error_rate of generated values == 0
    """
    # Pre Condition:
    float_sensor = FloatSimulator(
        float_schema["mean"],
        float_schema["min"],
        float_schema["max"],
        float_schema["stdev"],
        float_schema["variance"],
    )
    # we want to test if the values we create match the schema we used to initialize the sensor
    results = []
    # Test Case 1:
    for _ in range(0, 100000):
        results.append(float_sensor.calculate_next_value())
    mean = statistics.mean(results)
    stdev = statistics.stdev(results)
    error_rate = float_sensor.error_count / (float_sensor.value_count + float_sensor.error_count)
    assert mean == pytest.approx(float_schema["mean"], abs=0.3)
    assert stdev == pytest.approx(float_schema["stdev"], abs=0.15)
    assert error_rate == 0


def test_calculate_next_value_float_with_error():
    """
    This function tests if the FloatSimulator produces values that match the schema

    Pre Condition: FloatSimulator initialized with float_schema with error values

    Test Case 1: 10000 values for FloatSensor are created
    -> mean of generated values == mean of schema +- 0.5
    -> stdev of generated values == stdev of schema +- 0.1
    -> error_rate of generated values == error_rate of schema +- 0.001
    """
    # Pre Condition:
    float_sensor = FloatSimulator(
        float_schema["mean"],
        float_schema["min"],
        float_schema["max"],
        float_schema["stdev"],
        float_schema["variance"],
        float_schema["error_rate"],
        float_schema["error_length"],
    )
    # we want to test if the values we create match the schema we used to initialize the sensor
    results = []
    # Test Case 1:
    for _ in range(0, 100000):
        results.append(float_sensor.calculate_next_value())
    mean = statistics.mean(results)
    stdev = statistics.stdev(results)
    error_rate = float_sensor.error_count / (float_sensor.value_count + float_sensor.error_count)
    assert mean == pytest.approx(float_schema["mean"], abs=0.3)
    assert stdev == pytest.approx(float_schema["stdev"], abs=0.15)
    assert error_rate == pytest.approx(float_schema["error_rate"], abs=0.001)
