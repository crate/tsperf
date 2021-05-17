from batch_size_automator import BatchSizeAutomator


def test_is_auto_batch_mode():
    """
    This function tests if the auto_batch_mode of the BatchSizeAutomator is correctly caluclated.

    Test Case 1: batch_size is bigger than 0 and => auto_batch_mode is False
    batch_size: 2000
    ingest_mode: 1
    -> auto_batch_mode: False

    Test Case 2: batch_size is 0 and ingest_mode is 1 => auto_batch_mode is True
    batch_size: 0
    ingest_mode: 1
    -> auto_batch_mode: True

    Test Case 3: batch_size is 2000 and ingest_mode is 0 => auto_batch_mode is False
    batch_size: 2000
    ingest_mode: 0
    -> auto_batch_mode: False

    Test Case 4: batch_size is 0 and ingest_mode is 0 => auto_batch_mode is False
    batch_size: 0
    ingest_mode: 0
    -> auto_batch_mode: False

    Test Case 5: batch_size is -1000 and ingest_mode is 1 => auto_batch_mode is True
    batch_size: -1000
    ingest_mode: 1
    -> auto_batch_mode: True
    """
    # Test Case 1:
    batch_size_automator = BatchSizeAutomator(2000)
    assert not batch_size_automator.auto_batch_mode
    # Test Case 2:
    batch_size_automator = BatchSizeAutomator(0)
    assert batch_size_automator.auto_batch_mode
    # Test Case 3:
    batch_size_automator = BatchSizeAutomator(2000, active=False)
    assert not batch_size_automator.auto_batch_mode
    # Test Case 4:
    batch_size_automator = BatchSizeAutomator(0, active=False)
    assert not batch_size_automator.auto_batch_mode
    # Test Case 5:
    batch_size_automator = BatchSizeAutomator(-1000, active=True)
    assert batch_size_automator.auto_batch_mode


def test_insert_batch_time_normal():
    """
    This function tests for the correct behavior of the BatchSizeAutomator when using the insert_batch_time function

    Pre-Condition: A BatchSizeAutomator is created with batch_size 0 and ingest_mode 1 -> auto_batch_mode = True
        get_next_batch_size() returns 2500

    Test Case 1: For one full test_cycle (test_size) insert_batch_time is called with duration 10
    duration: 10
    times: test_size
    -> batch_times["best"]["avg_time"]: 10
    -> batch_times["best"]["batch_per_second"]: 250
    -> get_next_batch_size(): 3000

    Test Case 2: For one full test_cycle (test_size) insert_batch_time is called with duration 5
        because batch_size is calculated with a reduced step_size each cycle we calculate it as well
        as we want to test if the direction of the step is correct
    duration: 5
    times: test_size
    -> batch_times["best"]["avg_time"]: 5
    -> batch_times["best"]["batch_per_second"]: 600
    -> get_next_batch_size(): increased by step_size * alpha

    Test Case 3: For one full test_cycle (test_size) insert_batch_time is called with duration 7
        avg_time and batch_per_second for best stays the same but new batch_size is decreased from the
        last batch_size
    duration: 5
    times: test_size
    -> batch_times["best"]["avg_time"]: 5
    -> batch_times["best"]["batch_per_second"]: 600
    -> get_next_batch_size(): decreased by step_size * alpha

    Test Case 4: For one full test_cycle (test_size) insert_batch_time is called with duration 4
        avg_time and batch_per_second for best are updated and batch_size is further decreased
    duration: 5
    times: test_size
    -> batch_times["best"]["avg_time"]: 4
    -> batch_times["best"]["batch_per_second"]: batch_size / 4
    -> get_next_batch_size(): decreased by step_size * alpha

    Test Case 5: Until BatchSizeAutomator switches to surveillance mode insert_batch_time is called with duration 5
        Afterwards for one full test_cycle (test_size) insert_batch_time is called with duration 3
        As performance is better we stay in surveillance mode
    duration: 5
    times: until surveillance_mode True
    duration: 3
    times: test_size
    -> batch_times["best"]["avg_time"]: 3
    -> batch_times["best"]["batch_per_second"]: batch_size / 3
    -> surveillance_mode: True

    Test Case 6: For one full test_cycle (test_size) insert_batch_time is called with duration 5
    duration: 5
    times: test_size
    -> surveillance_mode: True
    """
    # Pre-Condition:
    batch_size_automator = BatchSizeAutomator(0)
    initial_batch_size = 2500
    assert batch_size_automator.get_next_batch_size() == initial_batch_size

    # Test Case 1:
    # ten will be the first best time
    duration = 10
    for i in range(0, batch_size_automator.test_size):
        batch_size_automator.insert_batch_time(duration)

    assert batch_size_automator.batch_times["best"]["avg_time"] == duration
    assert (
        batch_size_automator.batch_times["best"]["batch_per_second"]
        == initial_batch_size / duration
    )
    # because for the next iteration batch_size is increased by 500
    initial_step_size = 500
    assert (
        batch_size_automator.get_next_batch_size()
        == initial_batch_size + initial_step_size
    )

    # Test Case 2:
    # five will be the first best time making 3000 the best batchsize
    duration = 5
    for i in range(0, batch_size_automator.test_size):
        batch_size_automator.insert_batch_time(duration)
    current_batch_size = initial_batch_size + initial_step_size
    current_batch_per_second = current_batch_size / duration

    assert batch_size_automator.batch_times["best"]["avg_time"] == duration
    assert (
        batch_size_automator.batch_times["best"]["batch_per_second"]
        == current_batch_per_second
    )
    batch_size = 3000 + batch_size_automator.step_size * batch_size_automator.alpha
    assert batch_size_automator.get_next_batch_size() == batch_size

    # Test Case 3:
    # next is worse
    duration = 7
    for i in range(0, batch_size_automator.test_size):
        batch_size_automator.insert_batch_time(duration)

    assert batch_size_automator.batch_times["best"]["avg_time"] == 5  # last duration
    assert (
        batch_size_automator.batch_times["best"]["batch_per_second"]
        == current_batch_per_second
    )
    # batch_size is decreased this time because no better value was found and calculated based on best_size
    batch_size = (
        batch_size_automator.batch_times["best"]["size"]
        - batch_size_automator.step_size * batch_size_automator.alpha
    )
    assert batch_size_automator.get_next_batch_size() == batch_size

    # Test Case 4:
    # next is best
    duration = 4
    for i in range(0, batch_size_automator.test_size):
        batch_size_automator.insert_batch_time(duration)

    assert batch_size_automator.batch_times["best"]["avg_time"] == duration
    assert (
        batch_size_automator.batch_times["best"]["batch_per_second"]
        == batch_size_automator.batch_times["best"]["size"] / duration
    )
    # batch_size is further decreased
    batch_size = (
        batch_size - batch_size_automator.step_size * batch_size_automator.alpha
    )
    assert batch_size_automator.get_next_batch_size() == batch_size

    # Test Case 5:
    # we insert batch times until we switch to surveillance mode
    duration = 5
    while not batch_size_automator.surveillance_mode:
        batch_size_automator.insert_batch_time(duration)

    # for the next surveillance period we have no change in best batch size
    duration = 3
    for i in range(0, batch_size_automator.test_size):
        batch_size_automator.insert_batch_time(duration)

    assert batch_size_automator.batch_times["best"]["avg_time"] == duration
    assert (
        batch_size_automator.batch_times["best"]["batch_per_second"]
        == batch_size_automator.batch_times["best"]["size"] / duration
    )
    assert batch_size_automator.surveillance_mode

    # Test Case 6:
    # performance is worse so we switch out of surveillance mode and try to find best batch size again
    duration = 5
    for i in range(0, batch_size_automator.test_size):
        batch_size_automator.insert_batch_time(duration)

    assert not batch_size_automator.surveillance_mode


def test_insert_batch_time_smallest_batch():
    """
    This function tests if batch_size is correctly adjusted before getting smaller than 1

    Pre Condition: BatchSizeAutomator with batch_size 0 and ingest_mode 1 -> auto_batch_mode is True

    Test Case 1: At first we create a baseline for our test where a batch takes 10000 on average
        For the next cycle a batch takes 100000 on average so the batch_size adjustment is reversed to produce smaller
        batch sizes each cycle
        Next we decrease the duration so the average goes down each test cycle and batch_size is decreased further
        We stop when batch_size is set to 1, which means we went below 0 and the next batch_size should be increased
    -> bigger_batch_size: True
    """
    # Pre Condition:
    batch_size_automator = BatchSizeAutomator(0)

    # Test Case 1:
    # batch size will allways get smaller until we are under 1
    # first we have a baseline
    long_duration = 10000
    for i in range(0, batch_size_automator.test_size):
        batch_size_automator.insert_batch_time(long_duration)

    # then we get worse so direction of optimization is reversed
    worse_duration = 100000
    for i in range(0, batch_size_automator.test_size):
        batch_size_automator.insert_batch_time(worse_duration)

    # now we get better each time until we reach batch_size 1
    duration = (
        batch_size_automator.batch_size
        / batch_size_automator.batch_times["best"]["batch_per_second"]
    ) - 10
    batch_size = batch_size_automator.batch_size
    while batch_size_automator.batch_size != 1:
        if batch_size != batch_size_automator.batch_size:
            duration = (
                batch_size_automator.batch_size
                / batch_size_automator.batch_times["best"]["batch_per_second"]
            ) - 10
            batch_size = batch_size_automator.batch_size
        batch_size_automator.insert_batch_time(duration)

    # once we reached a negative batch_size and it was reset to 1 the batch_size should get bigger again
    assert batch_size_automator.bigger_batch_size


def test_manual_batch_mode_no_calculation():
    """
    This function tests if auto_batch_mode=False any action is taken when inserting batch times

    Test Case 1: auto_batch_mode = True; insert_batch_times called;
    ->self.batch_times["current"]["times"] has size=1

    Test Case 2: auto_batch_mode = False; insert_batch_times called;
    ->self.batch_times["current"]["times"] has size=0
    """

    # Test Case 1:
    batch_size_automator = BatchSizeAutomator(0)
    batch_size_automator.insert_batch_time(10)
    assert len(batch_size_automator.batch_times["current"]["times"]) == 1

    # Test Case 2:
    batch_size_automator = BatchSizeAutomator(0, active=False)
    batch_size_automator.insert_batch_time(10)
    assert len(batch_size_automator.batch_times["current"]["times"]) == 0


def test_step_size_is_default():
    default_step_size = 500
    batch_size_automator = BatchSizeAutomator(0, step_size=default_step_size)

    assert batch_size_automator.step_size == default_step_size


def test_step_size_is_data_batch_size():
    default_step_size = 500
    data_batch_size = 1000
    batch_size_automator = BatchSizeAutomator(
        0, data_batch_size=data_batch_size, step_size=default_step_size
    )

    assert batch_size_automator.step_size == data_batch_size


def test_batch_size_is_multitude_of_data_batch_size():
    data_batch_size = 500
    batch_size = 700
    batch_size_automator = BatchSizeAutomator(
        batch_size, data_batch_size=data_batch_size
    )

    assert batch_size_automator.batch_size == 500

    data_batch_size = 500
    batch_size = 800
    batch_size_automator = BatchSizeAutomator(
        batch_size, data_batch_size=data_batch_size
    )

    assert batch_size_automator.batch_size == 1000

    data_batch_size = 500
    batch_size = 400
    batch_size_automator = BatchSizeAutomator(
        batch_size, data_batch_size=data_batch_size
    )

    assert batch_size_automator.batch_size == 500


def test_batch_size_change_is_at_least_data_batch_size():
    data_batch_size = 500
    test_size = 1
    batch_size_automator = BatchSizeAutomator(
        0, data_batch_size=data_batch_size, test_size=test_size
    )

    # initial test cycle:
    batch_size_automator.insert_batch_time(1)
    assert (
        batch_size_automator.get_next_batch_size() == 3000
    )  # initially bath_size will go up
    # second test cycle:
    batch_size_automator.insert_batch_time(
        2
    )  # worse batch performance reduces alpha and leads to smaller step_size
    assert (
        batch_size_automator.get_next_batch_size() == 2000
    )  # batch_size is changed by at least data_batch_size
