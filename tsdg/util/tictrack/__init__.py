# MIT License
#
# Copyright (c) 2020 Joshua Hercher
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import time
import statistics

from typing import Callable, Any


tic_toc = {}
tic_toc_delta = {}
enabled = True
delta_enabled = True


def timed_function(do_print: bool = False, save_result: bool = True) -> Callable:
    """
    Decorator for functions to enable automatic execution time tracking.

    :param do_print: boolean to decide if result is printed or not (optional) default False.
    :param save_result: boolean to decide if result is saved for later statistical analysis (optional) default True
    :return: decorator
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            return execute_timed_function(
                func, *args, **kwargs, do_print=do_print, save_result=save_result
            )

        return wrapper

    return decorator


def execute_timed_function(
    func: Callable, *args, do_print: bool = False, save_result: bool = True, **kwargs
) -> Any:
    """
    function that takes another function as an argument and measures its execution time and saves it to a dictionary
    so statistical functions can be used for many executions of the given function

    :param func: function where execution time should be measured
    :param args: arguments for func
    :param do_print: boolean to decide if result is printed or not (optional) default False
    :param save_result: boolean to decide if result is saved for later statistical analysis (optional) default True
    :param kwargs: keyword arguments for func
    :return: return value of func
    """
    if not enabled:
        return func(*args, **kwargs)

    tic = time.monotonic()  # starting time measurement
    function_return = func(*args, **kwargs)
    toc = time.monotonic() - tic  # stopping time measurement

    if save_result:
        if func.__name__ not in tic_toc:
            tic_toc[func.__name__] = []

        tic_toc[func.__name__].append(toc)

        if delta_enabled:
            if func.__name__ not in tic_toc_delta:
                tic_toc_delta[func.__name__] = []

            tic_toc_delta[func.__name__].append(toc)

    if do_print:
        print(f"{func.__name__} took: {toc} seconds")
    return function_return


def timed_function_statistics(
    function_name: str,
    func: Callable = statistics.mean,
    *args,
    delta: bool = False,
    **kwargs,
) -> Any:
    """
    this function takes the saved execution times and applies `func` to it. The return value of `func` is returned.
    `func` must take a list of numbers as first argument otherwise execution will fail and a `SyntaxError` will be
    raised.
    If no execution times for function_name exist this function will throw a `ValueError`.

    :param function_name: the name of the function for which the executions times will be analyzed
    :param func: the function that is applied to the execution times (optional) default `statistics.mean`
    :param args: arguments for func
    :param delta: boolean if set to True the calculation is done on the delta values (optional) default False
    :param kwargs: keyword arguments for func
    :return: return value of func
    """
    times = tic_toc_delta if delta else tic_toc

    if function_name in times:
        try:
            return func(times[function_name], *args, **kwargs)
        except Exception as e:
            raise SyntaxError(
                f"calling {func.__name__} on result raises an exception: {e}\n"
            )
    else:
        raise ValueError(f"no execution times saved for {function_name}")


def consolidate(
    function_name: str,
    func: Callable = statistics.mean,
    *args,
    delta: bool = False,
    **kwargs,
):
    """
    this function can be used to consolidate saved values to reduce memory usage. This function overwrites previously
    saved results for the given `function_name` so when e.g. applying statistics.mean quantiles can no longer be
    calculated.
    `func` must take a list of numbers as first argument otherwise execution will fail and a `SyntaxError` will be
    raised.

    :param function_name: the name of the function for which the executions times will be consolidated
    :param func: the function that is applied to the execution times (optional) default `statistics.mean`. The first
        argument for this function is automatically gathered from the saved execution times and must no be provided
    :param args: arguments for func
    :param delta: boolean if set to True the calculation is done on the delta values (optional) default False
    :param kwargs: keyword arguments for func
    """
    times = tic_toc_delta if delta else tic_toc
    if function_name in times:
        try:
            consolidated_value = func(times[function_name], *args, **kwargs)
        except Exception as e:
            raise SyntaxError(
                f"calling {func.__name__} on result raises an exception: {e}\n"
            )
        if _valid_value(consolidated_value):
            if type(consolidated_value) == int or type(consolidated_value) == float:
                consolidated_value = [consolidated_value]
            times[function_name] = consolidated_value
        else:
            raise SyntaxError(
                f"{func.__name__} must return either int, float, list<int> or list<float>"
            )
    else:
        raise ValueError(f"no execution times saved for {function_name}")


def _valid_value(value):
    """
    this function is used to determine if the result of the consolidate function is valid. Valid types include int,
    float and lists of numbers.

    :param value: return value of the `consolidate` function
    :return: True if type is valid otherwise False
    """
    value_type = type(value)
    if value_type == int or value_type == float:
        return True
    elif value_type == list:
        for v in value:
            v_type = type(v)
            if v_type != int and v_type != float:
                return False
        return True
    else:
        return False


def reset_delta(function_name: str):
    """
    this function deletes the result set from the delta values of `function_name` if it exists

    :param function_name: name of the function for which the result set will be deleted from the delta values
    """
    if function_name in tic_toc_delta:
        del tic_toc_delta[function_name]


def reset(function_name: str, delta: bool = True):
    """
    this function deletes the result set of `function_name` if it exists. By default the result set of delta is also
    deleted.

    :param function_name: name of the function for which the result set will be deleted
    :param delta: boolean to decide if result set from should also be removed from delta, default True (optional)
    """
    if function_name in tic_toc:
        del tic_toc[function_name]
    if delta and function_name in tic_toc_delta:
        del tic_toc_delta[function_name]
