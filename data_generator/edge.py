# -*- coding: utf-8; -*-
#
# Licensed to Crate.io GmbH ("Crate") under one or more contributor
# license agreements.  See the NOTICE file distributed with this work for
# additional information regarding copyright ownership.  Crate licenses
# this file to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  You may
# obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations
# under the License.
#
# However, if you have executed another commercial license agreement
# with Crate these terms will supersede the license and you may use the
# software solely pursuant to the terms of the relevant commercial agreement.

import random
from float_simulator import FloatSimulator


factors = [-1, 1]


class Edge:
    def __init__(self, identifier: int, tags: dict, edge_model: dict):
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
                raise NotImplementedError(
                    "only FLOAT and BOOL Type have been implemented"
                )

    def calculate_next_value(self) -> dict:
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
                    self.payload[key] = identifiers[
                        int((self.id - 1) / elements_identifier) % len(identifiers)
                    ]

                elements_identifier += len(identifiers)


class Sensor:
    def __init__(self, model):
        self.model = model

    def get_key(self) -> str:
        return self.model["key"]["value"]


class FloatSensor(Sensor):
    def __init__(self, model):
        super().__init__(model)
        self.float_simulator = FloatSimulator(
            model["mean"]["value"],
            model["min"]["value"],
            model["max"]["value"],
            model["stdev"]["value"],
            model["variance"]["value"],
            model["error_rate"]["value"],
            model["error_length"]["value"],
        )

    def calculate_next_value(self) -> float:
        return self.float_simulator.calculate_next_value()


class BoolSensor(Sensor):
    def __init__(self, model):
        super().__init__(model)
        self.true_ratio = self.model["true_ratio"]["value"]

    def calculate_next_value(self) -> bool:
        return random.randint(0, (1 / self.true_ratio)) < 1
