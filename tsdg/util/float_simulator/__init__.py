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


class FloatSimulator:
    """
    The FloatSimulator produces consecutive float values based on a statistical model and the normal
    distribution. It can be used to simulate sensor data with more than 100.000 simulated values per second.

    To use the FloatSimulator instantiate an object and call the `calculate_next_value()` function
    """

    def __init__(
        self,
        mean: float,
        minimum: float,
        maximum: float,
        stdev: float,
        variance: float,
        error_rate: float = 0,
        error_length: float = 0,
    ):
        """
        :param mean: the average value of the simulator
        :param minimum: the minimum valid value of the simulator
        :param maximum: the maximum valid value of the simulator
        :param stdev: the standard deviation of the simulated values
        :param variance: the variance of the simulated values
        :param error_rate: optional. The chance that an error occurs (value below or above minimum and maximum).
            0.1 means 10% chance of error
            0.01 means 1% chance of error
            default 0 -> 0% chance of error
        :param error_length: optional. How long an error persists when it happens.
            1.1 means at least a length of 1, with a 10% chance of a length of 2
            2.3 means at least a length of 2, with a 30% chance of a length of 3
            51.01 means at least a length of 51, with a 1% chance of a length of 52
            there is always a 1% chance the error will continue longer
        """
        self.value_count = 0
        self.error_count = 0
        self.last_none_error_value = 0
        self.mean = mean
        self.minimum = minimum
        self.maximum = maximum
        self.standard_deviation = stdev
        self.default_error_rate = error_rate
        self.default_error_length = error_length
        self.current_error_rate = error_rate
        self.current_error_length = error_length
        self.variance = variance
        self.current_error = False
        self.value = round(
            random.uniform(self.mean - self.variance, self.mean + self.variance), 2
        )
        self.factors = [-1, 1]

    def calculate_next_value(self) -> float:
        """
        This function return the next value for a float_simulator instance
        :return: float
        """
        # if the last value has been an error value we first calculate if the next value is also an error
        # the chance for that is stored in the error_length variable which is a percentage value of how big
        # the chance is for the next value to be an error
        # each time the length is reduced by one, smallest chance is set to 0.1
        if self.current_error:
            self.current_error_length -= 1
            self.current_error_rate = self.current_error_length
            if self.current_error_rate < 0.01:
                self.current_error_rate = 0.01

        # this calculates if the next value is an error it takes the percentage of the error_rate variable and
        # multiplies it by 1000 and then checks if a random value in range 0 - 1000 is below the resulting value
        is_error = random.randint(0, 1000) < (self.current_error_rate * 1000)

        # if the next value is not an error the new value is calculated and the error variables reset
        # otherwise a new error is calculated
        if not is_error:
            self._new_value()
            if self.current_error:
                self.current_error = False
                self.current_error_rate = self.default_error_rate
                self.current_error_length = self.default_error_length
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
        factor = self.factors[self._decide_factor()]
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

        return (
            continue_direction
            if random.randint(0, (100 * self.standard_deviation)) < chance
            else change_direction
        )

    def _new_error_value(self):
        self.error_count += 1

        # if the next value is a consecutive error it is basically calculated in a similar way to a new value but
        # within the bounds of the respective error margin (upper or lower error)
        # otherwise a new error is calculated and chosen randomly from the upper or lower values
        if not self.current_error:
            if self.value < self.mean:
                self.value = round(
                    random.uniform(self.minimum, self.mean - self.standard_deviation), 2
                )
            else:
                self.value = round(
                    random.uniform(self.mean + self.standard_deviation, self.maximum), 2
                )
            self.current_error = True
        else:
            value_change = round(random.uniform(0, self.variance), 2)
            self.value += value_change * self.factors[random.randint(0, 1)]
