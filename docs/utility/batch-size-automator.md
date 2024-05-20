(bsa)=
(batch-size-automator)=
# Batch Size Automator

A utility to automatically detect the best batch size for optimized data insert operations.

## Features
The BSA utility provides two modes:

+ Finding best batch size
+ Surveillance

### Finding best batch size

1. The BSA calculates how many rows were inserted per second during the last
   test cycle (`test_size` inserts).
2. The BSA compares if the current result is better than the best.

   a. If current was better, the batch size is adjusted by the step size.

   b. If current was worse, the batch size is adjusted in the opposite direction
      of the last adjustment and the step size is reduced.

3. Repeat steps 1 to 2 until step size is below a threshold. This means that we
   entered 2.b. often and should have found our optimum batch size.
4. Change to surveillance mode.

### Surveillance

1. The BSA increases the length of the test cycle to 1000 inserts.
2. After 1000 inserts, the BSA calculates if performance got worse.

   a. if performance is worse test cycle length is set to 20, and we switch to
      finding best batch size mode.

   b. If performance is the same or better repeat steps 1 to 2.


## Usage

The most basic version on how to use the BSA. This will take care of your batch size and over time optimize it for maximum performance.

```python
import time
from tsperf.util.batch_size_automator import BatchSizeAutomator

bsa = BatchSizeAutomator()

while True:
    batch_size = bsa.get_next_batch_size()  # returns the batch_size which should be used for the next operation cycle
    start = time.monotonic()
    # do your batch operation here using the batch_size variable
    duration = time.monotonic() - start
    bsa.insert_batch_time(duration)  # will trigger a recalculation of the best batch size after 20 iterations
```

## Settings

This chapter gives an overview on the constructor arguments and how they influence the behaviour of the BSA.

### batch_size

When given a value higher than 0 will disable automatic batch size optimizing and always return this when calling `get_next_batch_size`.

```python
import time
from tsperf.util.batch_size_automator import BatchSizeAutomator

bsa = BatchSizeAutomator(batch_size=100)

while True:
    batch_size = bsa.get_next_batch_size()  # will always return 100
    start = time.monotonic()
    # do your batch operation here using the batch_size variable
    duration = time.monotonic() - start
    bsa.insert_batch_time(duration)  # will not do anything
```

### data_batch_size

The minimum batch_size of the data that will be handled, e.g. if a data set always consists of 5 datapoints which will not be split in the next operation independent of returned batch_size `data_batch_size` should be set to `5` this ensures the returned batch_size will always be a multitude of 5.

```python
import time
from tsperf.util.batch_size_automator import BatchSizeAutomator

bsa = BatchSizeAutomator(data_batch_size=5)

while True:
    batch_size = bsa.get_next_batch_size()  # will always return a multitude of 5 (e.g. 5, 10, 20, 100, 555, ...)
    start = time.monotonic()
    # do your batch operation here using the batch_size variable
    duration = time.monotonic() - start
    bsa.insert_batch_time(duration)
```

### active

Boolean that if set to `False` will disable automatic batch_size optimizing. Can be used to switch of the BSA to reduce impact on runtime (it will get worse ;P) without other code changes.

```python
import time
from tsperf.util.batch_size_automator import BatchSizeAutomator

bsa = BatchSizeAutomator(active=False)

while True:
    batch_size = bsa.get_next_batch_size()  # will always return 0 (or `batch_size` if set)
    start = time.monotonic()
    # do your batch operation here using the batch_size variable
    duration = time.monotonic() - start
    bsa.insert_batch_time(duration)  # will not do anything
```

### test_size

Is used to decided after how many operations the current and best batch sizes will be compared and therefore a new batch_size will be calculated. Should not be lower than 20 (to decrease influence of outliers), setting it to a big value will increase the time it takes to find the optimal batch size.

```python
import time
from tsperf.util.batch_size_automator import BatchSizeAutomator

bsa = BatchSizeAutomator(test_size=40)

while True:
    batch_size = bsa.get_next_batch_size()
    start = time.monotonic()
    # do your batch operation here using the batch_size variable
    duration = time.monotonic() - start
    bsa.insert_batch_time(duration)  # will trigger recalculation of batch size after 40 iterations
```

### set_size

Sets the initial step_size that is used to change the batch_size between operations. If it is smaller than `data_batch_size`, `data_batch_size` will be used as initial step_size

```python
import time
from tsperf.util.batch_size_automator import BatchSizeAutomator

bsa = BatchSizeAutomator(step_size=300)

while True:
    batch_size = bsa.get_next_batch_size()  # will return initial batch_size + 300 after the first recalculation
    start = time.monotonic()
    # do your batch operation here using the batch_size variable
    duration = time.monotonic() - start
    bsa.insert_batch_time(duration)
```
