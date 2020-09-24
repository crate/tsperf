import random


factors = [-1, 1]


class Edge:
    def __init__(self, identifier, tags, edge_model):
        self.id = identifier
        self.tags = tags
        self.edge_model = edge_model
        self.sensors = []
        self.payload = {}
        self._init_sensors()

    def _init_sensors(self):
        for key, value in self.edge_model.items():
            sensor_type = value["type"]["value"].lower()
            if sensor_type == "float":
                self.sensors.append(FloatSensor(value))
            elif sensor_type == "bool":
                self.sensors.append(BoolSensor(value))
            else:
                raise NotImplementedError("only FLOAT and BOOL Type have been implemented")

    def calculate_next_value(self):
        if self.payload == {}:
            self._assign_tag_values()

        for sensor in self.sensors:
            self.payload[sensor.get_key()] = sensor.calculate_next_value()

        # a copy of payload is returned so we don't overwrite the previously returned values
        return dict(self.payload)

    def _assign_tag_values(self):
        items = list(self.tags.items())
        elements_identifier = 0
        for i in range(len(items) - 1, -1, -1):
            key = items[i][0]
            value = items[i][1]
            if value == "id":
                self.payload[key] = self.id
            else:
                if isinstance(value, list):
                    identifiers = value
                else:
                    identifiers = list(range(0, value))

                if elements_identifier == 0:
                    self.payload[key] = identifiers[(self.id - 1) % len(identifiers)]
                else:
                    self.payload[key] = identifiers[int((self.id - 1) / elements_identifier) % len(identifiers)]

                elements_identifier += len(identifiers)


class Sensor:
    def __init__(self, model):
        self.model = model

    def get_key(self):
        return self.model["key"]["value"]


class FloatSensor(Sensor):
    def __init__(self, model):
        super().__init__(model)
        self.value_count = 0
        self.error_count = 0
        self.last_none_error_value = 0
        self.mean = model["mean"]["value"]
        self.minimum = model["min"]["value"]
        self.maximum = model["max"]["value"]
        self.standard_deviation = model["stdev"]["value"]
        self.error_rate = model["error_rate"]["value"]
        self.error_length = model["error_length"]["value"]
        self.variance = model["variance"]["value"]
        self.current_error = False
        self.value = round(random.uniform(self.mean - self.variance, self.mean + self.variance), 2)

    def calculate_next_value(self):
        # if the last value has been an error value we first calculate if the next value is also an error
        # the chance for that is stored in the error_length variable which is a percentage value of how big
        # the chance is for the next value to be an error
        # each time the length is reduced by one, smallest chance is set to 0.1
        if self.current_error:
            self.error_length -= 1
            self.error_rate = self.error_length
            if self.error_rate < 0.01:
                self.error_rate = 0.01

        # this calculates if the next value is an error it takes the percentage of the error_rate variable and
        # multiplies it by 1000 and then checks if a random value in range 0 - 1000 is below the resulting value
        is_error = random.randint(0, 1000) < (self.error_rate * 1000)

        # if the next value is not an error the new value is calculated and the error variables reset
        # otherwise a new error is calculated
        if not is_error:
            self._new_value()
            if self.current_error:
                self.current_error = False
                self.error_rate = self.model["error_rate"]["value"]
                self.error_length = self.model["error_length"]["value"]
        else:
            # to continue the good values where they ended the last time we save the last good value
            if not self.current_error:
                self.last_none_error_value = self.value
            self._new_error_value()

        return self.value

    def _new_value(self):
        self.value_count += 1

        # value change is calculated by adding a value within the variance range to the current value
        # by multiplying `factors[random.randint(0,1)]` to the value_change variable it is either
        # added or subtracted from the last value
        value_change = random.uniform(0, self.variance)

        # chance of going up or down is also influenced how far from the mean we are
        factor = factors[self._decide_factor()]
        # last value has been an error
        if self.current_error:
            self.value = self.last_none_error_value + (value_change * factor)
        else:
            self.value += value_change * factor

    def _decide_factor(self):
        if self.value > self.mean:
            distance = self.value - self.mean
            continue_direction = 1
            change_direction = 0
        else:
            distance = self.mean - self.value
            continue_direction = 0
            change_direction = 1
        chance = (50 * self.standard_deviation) - distance

        return continue_direction if random.randint(0, (100 * self.standard_deviation)) < chance else change_direction

    def _new_error_value(self):
        self.error_count += 1

        # if the next value is a consecutive error it is basically calculated in a similar way to a new value but
        # within the bounds of the respective error margin (upper or lower error)
        # otherwise a new error is calculated and chosen randomly from the upper or lower values
        if not self.current_error:
            if self.value < self.mean:
                self.value = round(random.uniform(self.minimum, self.mean - self.standard_deviation), 2)
            else:
                self.value = round(random.uniform(self.mean + self.standard_deviation, self.maximum), 2)
            self.current_error = True
        else:
            value_change = round(random.uniform(0, self.variance), 2)
            self.value += value_change * factors[random.randint(0, 1)]


class BoolSensor(Sensor):
    def __init__(self, model):
        super().__init__(model)
        self.true_ratio = self.model["true_ratio"]["value"]

    def calculate_next_value(self):
        return random.randint(0, (1 / self.true_ratio)) < 1
