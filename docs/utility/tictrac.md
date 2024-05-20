(tictrack)=
# tictrack

A utility to measure function execution times, and apply statistical functions on the results.

## Why?
Other libraries that measure function execution times require the same
repetitive code for each time you want to use it. This reduces readability
and code needs to be changed when execution times no longer want to be
tracked. Also, if an average (or other statistical value) execution time
needs to be calculated time keeping needs to be implemented again.

## Features
`tictrack` solves this with the following features:
+ [decorator](#decorator) for function to automatically track the execution time of each function call
+ [wrapper](#wrapper) function that can be put around each function call that should be tracked
+ simple on/off [switch](#disabling-tictrack) to disable execution time tracking with minimal code changes
+ automatically keeping execution times saved grouped by the function name to later apply statistical functions
+ [function](#analyzing-the-result) to apply these statistical functions to a result set
+ [function](#consolidating-the-result) to consolidate large result sets
+ additional [`delta`](#delta) time tracking so two results can be kept at the same time

## Usage

There are two ways to use `tictrack`, the optimal one depends on your specific use case.

- If you want to track every execution of one or more function, using the decorator is the easiest solution.
- If you only want to track certain executions of one or more functions, the wrapper function is the better solution.

### Decorator

This is the easiest way to use `tictrack`:

```python

from tsperf.util import tictrack


@tictrack.timed_function()
def foo(a, b):
    return a + b


foo_results = []
for i in range(0, 10):
    for j in range(10, 20):
        foo_results = foo(i, j)
```

You can than calculate the average execution time like so:

```python
average_foo_execution_time = tictrack.timed_function_statistics("foo")
```

The decorator supports any type of function with any combination of arguments, *args and **kwargs.

You can also track nested functions like this:

```python

from tsperf.util import tictrack


@tictrack.timed_function()
def foo(a, b):
    return a + b


@tictrack.timed_function()
def bar(x):
    return foo(x, x)


bar_results = []
for i in range(0, 10):
    bar_results = bar(i)
```

You can now calculate the average execution time of `foo` and `bar` like so:

```python
from tsperf.util import tictrack
average_foo_execution_time = tictrack.timed_function_statistics("foo")
average_bar_execution_time = tictrack.timed_function_statistics("bar")
```

#### Decorator Arguments

The Decorator has two optional arguments:
+ `do_print`: default `False`. If set to `True` the result of the measurement will be printed in the following format:
  `"function_name took: x seconds"`
+ `save_result` default `True`. If set to `False` the result of the measurement will not be saved and cannot be used for
  later analysis.

For example if you just want to use `tictrack` to output each execution time and no analyse averages or percentiles you
could set `do_print=True` and `save_result=False`. 

### Wrapper

The Wrapper can be used to only track certain function executions:

```python

from tsperf.util import tictrack


def foo(a, b):
    return a + b


x = foo(1, 2)  # this is not tracked
y = tictrack.execute_timed_function(foo, 2, 3)  # this is tracked
```

The Wrapper supports any kind of function using any kind of combination of arguments, *args and **kwargs. As in the
Decorator the Wrapper supports nested usage.

#### Wrapper Arguments

The Wrapper has two optional arguments:
+ `do_print`: default `False`. If set to `True` the result of the measurement will be printed in the following format:
  `"function_name took: x seconds"`
+ `save_result` default `True`. If set to `False` the result of the measurement will not be saved and cannot be used for
  later analysis.

For example if you just want to use `tictrack` to output each execution time and no analyse averages or percentiles you
could set `do_print=True` and `save_result=False`. 

**Note:** these arguments must be passed before any function `**kwargs` as keyword arguments to
`tictrack.execute_timed_function` as described in the function documentation.

### Disabling tictrack

To disable tictrack on a global scale this line needs to be added to you code before any measurements happen:

```python
tictrack.enabled = False
```

This will reduce the influence of `tictrack` on the runtime to a minimum with no additional code changes necessary. This
makes it easy to switch `tictrack` on and off without searching the whole code base where it is used.


## Result Processing

### Delta

`tictrack` offers a second set of results which can be used to only analyze a subset of values. This option is enabled 
by default, to disable it add the following line to you code:

```python
tictrack.delta_enabled = False
```

With the `reset_delta` function the result set for a single function can be reset. A possible use case could be the
following:

Your application runs for 10 minutes and you want to track the function `foo` throughout this time to calculate the
average execution time of foo. Additionally, the input parameters for `foo` change every minute and you want to keep 
track for the averages each minute as well:

```python

from tsperf.util import tictrack


@tictrack.timed_function()
def foo(a, b):
    # code
    pass


delta_averages = []

while not ten_minutes_have_passed:
    ...
    foo(a, b)
    if one_minute_has_passed:
        delta_averages.append(tictrack.timed_function_statistics("foo", delta=True))
        tictrack.reset_delta("foo")
    ...

# print the results
for avg in delta_averages:
    print(f"foo delta took {avg} seconds on average")

print(f"foo took {tictrack.timed_function_statistics('foo')} seconds on average")

``` 

### Analyzing the result

The result set generated by `tictrack` can be analyzed by directly accessing the result set like so:

```python

from tsperf.util import tictrack

...
foo_result = tictrack.tic_toc["foo"]  # general results
foo_delta_result = tictrack.tic_toc_delta["foo"]  # delta results
```

For additional safety accessing values the `timed_function_statistics` exists. It takes the tracked function name as a
string as first argument and a function as optional second argument. If no function as second argument is supplied
`statistics.mean` will be used. This function is then applied to the chosen result set and the result returned:

```python
from tsperf.util import tictrack
average_foo_time = tictrack.timed_function_statistics("foo")  # default function
median_foo_time = tictrack.timed_function_statistics("foo", statistics.median)  # median function
```

The supplied function must take a list of numbers as first argument, additional arguments can be used with the
*args and **kwargs arguments of `timed_function_statistics`.

In case the function name has not been tracked a `ValueError` is raised. If the given function cannot handle the result
set a `SyntaxError` is raised.

To apply the same function to all result sets a loop is required but a option for `timed_function_statistics` is on the
roadmap:

```python
for function_name in tictrack.tic_toc.keys():
    print(f"average execution time of {function_name}: {tictrack.timed_function_statistics(function_name)}s")
```

### Consolidating the result

In a long running application the result sets might grow big an have a memory impact. To mitigate this the consolidate
function can be used. It applies the given function to a result set and saves the returned value as the new result set,
by default `statistics.mean` is used:

```python

from tsperf.util import tictrack


@tictrack.timed_function()
def foo(a, b):
    pass


# code
# tictrack.tic_toc["foo"] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

tictrack.consolidate("foo")
# tictrack.tic_toc["foo"] = [4.5]
```

The given function must take a list of numbers as first argument and return either a list of numbers or a number (which
is cast to a list). This ensures that further operations with the result set are possible.

If the given function name is not in the dictionary a `ValueError` is raised. If either the result of the given function
is neither number nor list of numbers or if the function cannot be applied to a list of numbers a `SyntaxError` is
raised.

### Resetting the result

It is also possible to delete an entire result set by calling either `tictrack.reset("function_name)` or
`tictrack.reset_delta("function_name")`:

```python

from tsperf.util import tictrack

# tictrack.tic_toc["foo"] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
tictrack.reset("foo")
# "foo" in tictrack.tic_toc is False
```
