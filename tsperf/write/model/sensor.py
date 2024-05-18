import random

from tsperf.util.float_simulator import FloatSimulator


class Sensor:
    def __init__(self, schema):
        self.schema = schema

    def get_key(self) -> str:
        return self.schema["key"]["value"]


class FloatSensor(Sensor):
    def __init__(self, schema):
        super().__init__(schema)
        self.float_simulator = FloatSimulator(
            schema["mean"]["value"],
            schema["min"]["value"],
            schema["max"]["value"],
            schema["stdev"]["value"],
            schema["variance"]["value"],
            schema["error_rate"]["value"],
            schema["error_length"]["value"],
        )

    def calculate_next_value(self) -> float:
        return self.float_simulator.calculate_next_value()


class BoolSensor(Sensor):
    def __init__(self, schema):
        super().__init__(schema)
        self.true_ratio = self.schema["true_ratio"]["value"]

    def calculate_next_value(self) -> bool:
        return random.randint(0, int(1 / self.true_ratio)) < 1  # noqa:S311
