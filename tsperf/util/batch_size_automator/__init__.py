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

import statistics


class BatchSizeAutomator:
    """
    The BatchSizeAutomator class allows to calculate optimized batch
    sizes for any operations using batch sizes, e.g. database inserts
    or batch operations.
    It works by first calculating an optimized batch size and then
    surveying the performance. If the performance drops it searches
    for the optimized batch size again. This allows long running
    applications to react to environment changes or even performance
    changes on the server side.

    To use the BSA your code should follow the following structure:

    `
    bsa = BatchSizeAutomator()

    while True:
        batch_size = bsa.get_next_batch_size()
        start = time.monotonic()
        # do you're batch operation here using batch_size
        duration = time.monotonic() - start
        bsa.insert_batch_time(duration)
    `
    """

    def __init__(
        self,
        batch_size: int = 0,
        data_batch_size: int = 1,
        active: bool = True,
        test_size: int = 20,
        step_size: int = 500,
    ):
        """
        the __init__ function sets the BSA up for further operation:

        if the `batch_size` is smaller than `1` and `active` is `True` the BSA will
        search for the best batch_size. otherwise the initially set batch_size will
        always be returned.

        the initial batch_size is either the given `batch_size` or 2500 if `batch_size`
        is smaller than `1`

        the step_size is set to the value of `step_size` if it's bigger than `data_batch_size`
        otherwise it will be set to `data_batch_size`

        :param batch_size: optional
            default: 0
            when given a value higher than 0 will disable automatic batch_size optimizing and
            always return this as batch_size
        :param data_batch_size: optional
            default: 1
            the minimum batch_size of the data that will be handled, e.g. if a data set always
            consists of 5 datapoints which will not be split in the next operation independent
            of returned batch_size `data_batch_size` should be set to `5` this ensures the returned
            batch_size will always be a multitude of 5.
        :param active: optional
            default: True
            boolean that if set to `False` will disable automatic batch_size optimizing.
            Can be used to switch of the BSA to reduce impact on runtime (it will get worse ;P)
            without other code changes
        :param test_size: optional
            default: 20
            Is used to decided after how many operations the current and best batch sizes
            will be compared and therefore a new batch_size will be calculated. Should not be
            lower than 20, setting it to a big value will increase the time it takes to find
            the optimal batch size
        :param step_size: optional
            default: 500
            Sets the initial step_size that is used to change the batch_size between operations.
            If it is smaller than `data_batch_size`, `data_batch_size` will be used as
            initial step_size
        """
        self.factors = [-1, 1]
        self.auto_batch_mode = batch_size <= 0 and active
        # The size the data set has at minimum for the batch operation
        self.data_batch_size = data_batch_size
        self.bigger_batch_size = True
        self._set_batch_size((batch_size, 2500)[batch_size <= 0])
        self.batch_times = {
            "current": {
                "size": self.batch_size,
                "times": [],
                "avg_time": -1,
                "batch_per_second": 0.0,
            },
            "best": {
                "size": self.batch_size,
                "times": [],
                "avg_time": -1,
                "batch_per_second": 0.0,
            },
        }
        self.alpha = 1.0
        # smaller steps than data_batch_size make no sense at this is the smallest batch_size
        self.step_size = (
            step_size if step_size > self.data_batch_size else self.data_batch_size
        )
        self.test_size = test_size
        self.default_test_size = test_size
        self.surveillance_mode = False

    def get_next_batch_size(self) -> int:
        """
        this function returns the batch_size that should be used for the next insert

        :return: int: size of the next batch
        """
        return self.batch_size

    def insert_batch_time(self, duration: float):
        """
        This function is used to insert the duration of the last insert operation.
        If enough iterations have been done it triggers the calculation of the next batch size.

        :param duration: the duration of the last insert operation
        """
        if self.auto_batch_mode:
            self.batch_times["current"]["times"].append(duration)
            if len(self.batch_times["current"]["times"]) >= self.test_size:
                self._calc_better_batch_time()

    def _set_batch_size(self, batch_size: int):
        if batch_size < self.data_batch_size:
            # if batch_size goes down to a number smaller than data_batch_size
            # it is set to data_batch_size and the direction flipped
            self.bigger_batch_size = not self.bigger_batch_size
            self.batch_size = self.data_batch_size
        else:
            # the batch_size must always be a multitude of self.data_batch_size
            if batch_size % self.data_batch_size != 0:
                batch_size = self.data_batch_size * round(
                    batch_size / self.data_batch_size
                )
            self.batch_size = batch_size

    def _calc_better_batch_time(self):
        if self._is_current_batch_size_better():
            # if during surveillance_mode the performance changes quit surveillance
            # and calculate better batch_size faster
            self._adjust_batch_size(True)
        else:
            # if we were in surveillance mode and the performance got worse we want to readjust the batch_size,
            # this means we stop surveillance mode and do a retest over 10 batches with slightly adjusted batch_size.
            if self.surveillance_mode:
                self._stop_surveillance_mode()
                self._adjust_batch_size(True)
            else:
                self.alpha -= (
                    self.alpha / 10
                )  # reduce step_size by 10% each calculation
                # if step_size is smaller than 100 no more adjustment necessary. batch_size_automator will go into
                # surveillance mode and only check periodically if batch_performance has gotten worse
                if self.step_size * self.alpha < 100:
                    self._start_surveillance_mode()
                else:
                    # if we didn't change into surveillance mode we change the direction of the batch_size adjustment
                    # and let the automator run with a new batch_size
                    self.bigger_batch_size = (
                        not self.bigger_batch_size
                    )  # change direction of batch_size adjustment
                    self._adjust_batch_size(False)
        # reset current batch_times for next batch_size
        self.batch_times["current"] = {
            "size": self.batch_size,
            "times": [],
            "avg_time": -1,
        }

    def _adjust_batch_size(self, take_current: bool):
        if take_current:
            self.batch_times["best"] = self.batch_times["current"]
        batch_size_change = (
            self.factors[self.bigger_batch_size] * self.alpha * self.step_size
        )
        # there would be no change in real batch size if the change was less than data_batch_size
        if abs(batch_size_change) < self.data_batch_size:
            # we got to preserve the direction
            batch_size_change = self.data_batch_size * (
                batch_size_change / abs(batch_size_change)
            )
        self._set_batch_size(
            round(self.batch_times["best"]["size"] + batch_size_change)
        )

    def _start_surveillance_mode(self):
        self.test_size = 1000
        self._set_batch_size(self.batch_times["best"]["size"])
        self.surveillance_mode = True

    def _stop_surveillance_mode(self):
        self.surveillance_mode = False
        self.test_size = self.default_test_size
        self.alpha = 0.5  # we want a shorter iteration this time

    def _is_current_batch_size_better(self):
        current_avg = statistics.mean(self.batch_times["current"]["times"])
        self.batch_times["current"]["avg_time"] = current_avg
        best_avg = self.batch_times["best"]["avg_time"]
        best_per_second = self.batch_times["best"]["size"] / best_avg
        current_per_second = self.batch_times["current"]["size"] / current_avg
        self.batch_times["best"][
            "batch_per_second"
        ] = best_per_second  # this is not really necessary
        self.batch_times["current"]["batch_per_second"] = current_per_second
        current_was_better = current_per_second > best_per_second
        # if best_avg is -1 no best batch_size has been calculated yet
        return best_avg == -1 or current_was_better
