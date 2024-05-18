import statistics

factors = [-1, 1]


class BatchSizeAutomator:
    def __init__(self, batch_size, ingest_mode, data_batch_size=1):
        self.auto_batch_mode = batch_size <= 0 and ingest_mode == 1
        self.data_batch_size = data_batch_size  # the size the data set has at minimum for the batch operation
        self._set_batch_size((batch_size, 2500)[batch_size <= 0])
        self.batch_times = {"current": {
                                "size": self.batch_size,
                                "times": [],
                                "avg_time": -1,
                                "batch_per_second": 0.0},
                            "best": {
                                "size": self.batch_size,
                                "times": [],
                                "avg_time": -1,
                                "batch_per_second": 0.0}}
        # batch_mode is only run when ingest_mode is set to 1
        self.alpha = 1.0
        # smaller steps than data_batch_size make no sense at this is the smallest batch_size
        self.step_size = 500 if 500 > self.data_batch_size else self.data_batch_size
        self.test_size = 20
        self.bigger_batch_size = True
        self.surveillance_mode = False

    def get_next_batch_size(self):
        return self.batch_size

    def insert_batch_time(self, duration):
        self.batch_times["current"]["times"].append(duration)
        if len(self.batch_times["current"]["times"]) >= self.test_size:
            self._calc_better_batch_time()

    def _set_batch_size(self, batch_size):
        if batch_size < self.data_batch_size:
            # if batch_size goes down to a number smaller than data_batch_size it is set to 1 and the direction
            # turned upwards
            self.bigger_batch_size = not self.bigger_batch_size
            self.batch_size = self.data_batch_size
        else:
            # the batch_size must always be a multitude of self.data_batch_size
            if batch_size % self.data_batch_size != 0:
                batch_size = self.data_batch_size * round(batch_size/self.data_batch_size)
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
                self.alpha -= self.alpha / 10  # reduce step_size by 10% each calculation
                # if step_size is smaller than 100 no more adjustment necessary. batch_size_automator will go into
                # surveillance mode and only check periodically if batch_performance has gotten worse
                if self.step_size * self.alpha < 100:
                    self._start_surveillance_mode()
                else:
                    # if we didn't change into surveillance mode we change the direction of the batch_size adjustment
                    # and let the automator run with a new batch_size
                    self.bigger_batch_size = not self.bigger_batch_size  # change direction of batch_size adjustment
                    self._adjust_batch_size(False)
        # reset current batch_times for next batch_size
        self.batch_times["current"] = {"size": self.batch_size, "times": [], "avg_time": -1}

    def _adjust_batch_size(self, take_current):
        if take_current:
            self.batch_times["best"] = self.batch_times["current"]
        batch_size_change = factors[self.bigger_batch_size] * self.alpha * self.step_size
        # there would be no change in real batch size if the change was less than data_batch_size
        if abs(batch_size_change) < self.data_batch_size:
            batch_size_change = self.data_batch_size
        self._set_batch_size(round(self.batch_times["best"]["size"] + batch_size_change))

    def _start_surveillance_mode(self):
        self.test_size = 1000
        self._set_batch_size(self.batch_times["best"]["size"])
        self.surveillance_mode = True

    def _stop_surveillance_mode(self):
        self.surveillance_mode = False
        self.test_size = 20
        self.alpha = 0.5

    def _is_current_batch_size_better(self):
        current_avg = statistics.mean(self.batch_times["current"]["times"])
        self.batch_times["current"]["avg_time"] = current_avg
        best_avg = self.batch_times["best"]["avg_time"]
        best_per_second = self.batch_times["best"]["size"] / best_avg
        current_per_second = self.batch_times["current"]["size"] / current_avg
        self.batch_times["best"]["batch_per_second"] = best_per_second  # this is not really necessary
        self.batch_times["current"]["batch_per_second"] = current_per_second
        current_was_better = current_per_second > best_per_second
        # if best_avg is -1 no best batch_size has been calculated yet
        return best_avg == -1 or current_was_better
