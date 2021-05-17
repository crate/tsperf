import mock
import pytest
import statistics
import tictrack


@pytest.fixture(scope="session", autouse=True)
def reset_tictoc_baseline():
    tictrack.reset("foo")
    tictrack.reset_delta("foo")


@pytest.fixture(scope="function", autouse=True)
def reset_tictoc():
    # to start each test function with a clean tictrack library we reset the dictionaries
    tictrack.tic_toc = {}
    tictrack.tic_toc_delta = {}


@mock.patch("builtins.print", autospec=True)
def test_decorator_default(mock_print):
    @tictrack.timed_function()
    def foo(a, b):
        return a + b

    return_value = foo(1, 2)
    assert return_value == 3
    assert "foo" in tictrack.tic_toc
    assert "foo" in tictrack.tic_toc_delta
    assert mock_print.call_count == 0


@mock.patch("builtins.print", autospec=True)
def test_decorator_print(mock_print):
    @tictrack.timed_function(True)
    def foo(a, b):
        return a + b

    return_value = foo(1, 2)
    assert return_value == 3
    assert mock_print.call_count == 1


def test_decorator_save_result_false():
    @tictrack.timed_function(save_result=False)
    def foo(a, b):
        return a + b

    return_value = foo(1, 2)
    assert return_value == 3
    assert "foo" not in tictrack.tic_toc
    assert "foo" not in tictrack.tic_toc_delta


@mock.patch("builtins.print", autospec=True)
def test_decorator_print_not_save(mock_print):
    @tictrack.timed_function(True, False)
    def foo(a, b):
        return a + b

    return_value = foo(1, 2)
    assert return_value == 3
    assert mock_print.call_count == 1
    assert "foo" not in tictrack.tic_toc
    assert "foo" not in tictrack.tic_toc_delta


def test_decorator_simple_kwargs():
    @tictrack.timed_function()
    def foo(a, b):
        return a / b

    return_value = foo(b=1, a=2)
    assert return_value == 2


def test_decorator_multi_args():
    @tictrack.timed_function()
    def foo(*args):
        return sum(args)

    return_value = foo(1, 2, 3, 4)
    assert return_value == 10

    return_value = foo(1, 2, 3, 4, 5, 6, 7)
    assert return_value == 28


def test_decorator_args_kwargs():
    @tictrack.timed_function()
    def foo(*args, a, b):
        return (sum(args) * a) / b

    return_value = foo(1, 2, 3, 4, a=2, b=4)
    assert return_value == 5

    return_value = foo(1, 2, 3, 4, 5, 6, 7, b=2, a=4)
    assert return_value == 56


def test_decorator_normal_args_kwargs():
    @tictrack.timed_function()
    def foo(x, y, *args, a, b):
        return (x * y + sum(args)) / (a / b)

    return_value = foo(1, 2, 3, 4, a=2, b=4)
    assert return_value == 18


@mock.patch("builtins.print", autospec=True)
def test_wrapper_default(mock_print):
    def foo(a, b):
        return a + b

    return_value = tictrack.execute_timed_function(foo, 1, 2)
    assert return_value == 3
    assert "foo" in tictrack.tic_toc
    assert "foo" in tictrack.tic_toc_delta
    assert mock_print.call_count == 0


@mock.patch("builtins.print", autospec=True)
def test_wrapper_print(mock_print):
    def foo(a, b):
        return a + b

    return_value = tictrack.execute_timed_function(foo, 1, 2, do_print=True)
    assert return_value == 3
    assert mock_print.call_count == 1


def test_wrapper_save_result_false():
    def foo(a, b):
        return a + b

    return_value = tictrack.execute_timed_function(foo, 1, 2, save_result=False)
    assert return_value == 3
    assert "foo" not in tictrack.tic_toc
    assert "foo" not in tictrack.tic_toc_delta


@mock.patch("builtins.print", autospec=True)
def test_wrapper_print_not_save(mock_print):
    def foo(a, b):
        return a + b

    return_value = tictrack.execute_timed_function(
        foo, 1, 2, do_print=True, save_result=False
    )
    assert return_value == 3
    assert mock_print.call_count == 1
    assert "foo" not in tictrack.tic_toc
    assert "foo" not in tictrack.tic_toc_delta


def test_wrapper_simple_kwargs():
    def foo(a, b):
        return a / b

    return_value = tictrack.execute_timed_function(foo, b=1, a=2)
    assert return_value == 2


def test_wrapper_multi_args():
    def foo(*args):
        return sum(args)

    return_value = tictrack.execute_timed_function(foo, 1, 2, 3, 4)
    assert return_value == 10

    return_value = tictrack.execute_timed_function(foo, 1, 2, 3, 4, 5, 6, 7)
    assert return_value == 28


def test_wrapper_args_kwargs():
    def foo(*args, a, b):
        return (sum(args) * a) / b

    return_value = tictrack.execute_timed_function(foo, 1, 2, 3, 4, a=2, b=4)
    assert return_value == 5

    return_value = tictrack.execute_timed_function(foo, 1, 2, 3, 4, 5, 6, 7, b=2, a=4)
    assert return_value == 56


def test_wrapper_normal_args_kwargs():
    def foo(x, y, *args, a, b):
        return (x * y + sum(args)) / (a / b)

    return_value = tictrack.execute_timed_function(foo, 1, 2, 3, 4, a=2, b=4)
    assert return_value == 18


def test_stats_no_values():
    with pytest.raises(ValueError):
        tictrack.timed_function_statistics("foo")


def test_stats_no_values_delta():
    with pytest.raises(ValueError):
        tictrack.timed_function_statistics("foo", delta=True)


def test_stats_mean():
    tictrack.tic_toc["foo"] = [1, 2, 3, 4, 5, 6, 7]
    return_value = tictrack.timed_function_statistics("foo")
    assert return_value == 4


def test_stats_mean_delta():
    tictrack.tic_toc_delta["foo"] = [1, 2, 3, 4, 5, 6, 7]
    return_value = tictrack.timed_function_statistics("foo", delta=True)
    assert return_value == 4


def test_stats_missing_arguments():
    def bar(a, b):
        return sum(a) + b

    tictrack.tic_toc["foo"] = [1, 2, 3, 4, 5, 6, 7]
    with pytest.raises(SyntaxError):
        tictrack.timed_function_statistics("foo", bar)


def test_stats_missing_arguments_delta():
    def bar(a, b):
        return sum(a) + b

    tictrack.tic_toc_delta["foo"] = [1, 2, 3, 4, 5, 6, 7]
    with pytest.raises(SyntaxError):
        tictrack.timed_function_statistics("foo", bar, delta=True)


def test_stats_arguments():
    def bar(a, b):
        return sum(a) + b

    tictrack.tic_toc["foo"] = [1, 2, 3, 4, 5, 6, 7]
    return_value = tictrack.timed_function_statistics("foo", bar, 2)
    assert return_value == 30


def test_stats_arguments_delta():
    def bar(a, b):
        return sum(a) + b

    tictrack.tic_toc_delta["foo"] = [1, 2, 3, 4, 5, 6, 7]
    return_value = tictrack.timed_function_statistics("foo", bar, 2, delta=True)
    assert return_value == 30


def test_stats_args_kwargs():
    def bar(a, b, c, d):
        return sum(a) + (c / b) - d

    tictrack.tic_toc["foo"] = [1, 2, 3, 4, 5, 6, 7]
    return_value = tictrack.timed_function_statistics("foo", bar, 2, d=4, c=2)
    assert return_value == 25


def test_stats_args_kwargs_delta():
    def bar(a, b, c, d):
        return sum(a) + (c / b) - d

    tictrack.tic_toc_delta["foo"] = [1, 2, 3, 4, 5, 6, 7]
    return_value = tictrack.timed_function_statistics(
        "foo", bar, 2, delta=True, d=4, c=2
    )
    assert return_value == 25


def test_consolidate_no_values():
    with pytest.raises(ValueError):
        tictrack.consolidate("foo")


def test_consolidate_no_values_delta():
    with pytest.raises(ValueError):
        tictrack.consolidate("foo", delta=True)


def test_consolidate_mean():
    tictrack.tic_toc["foo"] = [1, 2, 3, 4, 5, 6, 7]
    tictrack.consolidate("foo")
    assert tictrack.tic_toc["foo"] == [4]


def test_consolidate_mean_delta():
    tictrack.tic_toc_delta["foo"] = [1, 2, 3, 4, 5, 6, 7]
    tictrack.consolidate("foo", delta=True)
    assert tictrack.tic_toc_delta["foo"] == [4]


def test_consolidate_missing_arguments():
    def bar(a, b):
        return sum(a) + b

    tictrack.tic_toc["foo"] = [1, 2, 3, 4, 5, 6, 7]
    with pytest.raises(SyntaxError):
        tictrack.consolidate("foo", bar)


def test_consolidate_missing_arguments_delta():
    def bar(a, b):
        return sum(a) + b

    tictrack.tic_toc_delta["foo"] = [1, 2, 3, 4, 5, 6, 7]
    with pytest.raises(SyntaxError):
        tictrack.consolidate("foo", bar, delta=True)


def test_consolidate_arguments():
    def bar(a, b):
        return sum(a) + b

    tictrack.tic_toc["foo"] = [1, 2, 3, 4, 5, 6, 7]
    tictrack.consolidate("foo", bar, 2)
    assert tictrack.tic_toc["foo"] == [30]


def test_consolidate_arguments_delta():
    def bar(a, b):
        return sum(a) + b

    tictrack.tic_toc_delta["foo"] = [1, 2, 3, 4, 5, 6, 7]
    tictrack.consolidate("foo", bar, 2, delta=True)
    assert tictrack.tic_toc_delta["foo"] == [30]


def test_consolidate_args_kwargs():
    def bar(a, b, c, d):
        return [sum(a) + (c / b) - d]

    tictrack.tic_toc["foo"] = [1, 2, 3, 4, 5, 6, 7]
    tictrack.consolidate("foo", bar, 2, d=4, c=2)
    assert tictrack.tic_toc["foo"] == [25]


def test_consolidate_args_kwargs_delta():
    def bar(a, b, c, d):
        return [sum(a) + (c / b) - d]

    tictrack.tic_toc_delta["foo"] = [1, 2, 3, 4, 5, 6, 7]
    tictrack.consolidate("foo", bar, 2, delta=True, d=4, c=2)
    assert tictrack.tic_toc_delta["foo"] == [25]


def test_consolidate_invalid_return_type():
    def bar(a):
        return str(sum(a))

    tictrack.tic_toc["foo"] = [1, 2, 3]
    with pytest.raises(SyntaxError):
        tictrack.consolidate("foo", bar)


def test_consolidate_invalid_return_type_delta():
    def bar(a):
        return str(sum(a))

    tictrack.tic_toc_delta["foo"] = [1, 2, 3]
    with pytest.raises(SyntaxError):
        tictrack.consolidate("foo", bar, delta=True)


def test_consolidate_invalid_return_list():
    def bar(a):
        return [sum(a), statistics.mean(a), str(sum(a))]

    tictrack.tic_toc["foo"] = [1, 2, 3]
    with pytest.raises(SyntaxError):
        tictrack.consolidate("foo", bar)


def test_consolidate_invalid_return_list_delta():
    def bar(a):
        return [sum(a), statistics.mean(a), str(sum(a))]

    tictrack.tic_toc_delta["foo"] = [1, 2, 3]
    with pytest.raises(SyntaxError):
        tictrack.consolidate("foo", bar, delta=True)


def test_reset_delta():
    tictrack.tic_toc_delta["foo"] = [1, 2, 3]
    assert "foo" in tictrack.tic_toc_delta
    tictrack.reset_delta("foo")
    assert "foo" not in tictrack.tic_toc_delta


def test_reset_empty_delta():
    tictrack.reset_delta("foo")
    assert "foo" not in tictrack.tic_toc_delta


def test_reset_no_delta():
    tictrack.tic_toc["foo"] = [1, 2, 3]
    assert "foo" in tictrack.tic_toc
    assert "foo" not in tictrack.tic_toc_delta
    tictrack.reset("foo")
    assert "foo" not in tictrack.tic_toc
    assert "foo" not in tictrack.tic_toc_delta


def test_reset_empty_no_delta():
    tictrack.reset("foo")
    assert "foo" not in tictrack.tic_toc
    assert "foo" not in tictrack.tic_toc_delta


def test_reset_with_delta():
    tictrack.tic_toc["foo"] = [1, 2, 3]
    tictrack.tic_toc_delta["foo"] = [1, 2, 3]
    assert "foo" in tictrack.tic_toc
    assert "foo" in tictrack.tic_toc_delta
    tictrack.reset("foo")
    assert "foo" not in tictrack.tic_toc
    assert "foo" not in tictrack.tic_toc_delta


def test_reset_empty():
    tictrack.reset("foo", delta=False)
    assert "foo" not in tictrack.tic_toc
    assert "foo" not in tictrack.tic_toc_delta


def test_reset_without_delta():
    tictrack.tic_toc["foo"] = [1, 2, 3]
    tictrack.tic_toc_delta["foo"] = [1, 2, 3]
    assert "foo" in tictrack.tic_toc
    assert "foo" in tictrack.tic_toc_delta
    tictrack.reset("foo", delta=False)
    assert "foo" not in tictrack.tic_toc
    assert "foo" in tictrack.tic_toc_delta


def test_reset_without_no_delta():
    tictrack.tic_toc["foo"] = [1, 2, 3]
    assert "foo" in tictrack.tic_toc
    assert "foo" not in tictrack.tic_toc_delta
    tictrack.reset("foo", delta=False)
    assert "foo" not in tictrack.tic_toc
    assert "foo" not in tictrack.tic_toc_delta


def test_reset_without_delta_only():
    tictrack.tic_toc_delta["foo"] = [1, 2, 3]
    assert "foo" not in tictrack.tic_toc
    assert "foo" in tictrack.tic_toc_delta
    tictrack.reset("foo", delta=False)
    assert "foo" not in tictrack.tic_toc
    assert "foo" in tictrack.tic_toc_delta


def test_decorator_disabled_tictoc():
    @tictrack.timed_function()
    def foo():
        return 2

    tictrack.enabled = False
    assert foo() == 2
    assert "foo" not in tictrack.tic_toc
    assert "foo" not in tictrack.tic_toc_delta
    tictrack.enabled = True


def test_decorator_disabled_tictoc_delta():
    @tictrack.timed_function()
    def foo():
        return 2

    tictrack.delta_enabled = False
    assert foo() == 2
    assert "foo" in tictrack.tic_toc
    assert "foo" not in tictrack.tic_toc_delta
    tictrack.delta_enabled = True


def test_decorate_nested_functions():
    @tictrack.timed_function()
    def foo(a, b):
        return a + b

    @tictrack.timed_function()
    def bar(x):
        return foo(x, x)

    bar(1)
    assert "foo" in tictrack.tic_toc
    assert "bar" in tictrack.tic_toc
