import time


tic_toc = {}
tic_toc_delta = {}


def execute_timed_function(function, *args, do_print=False):
    # this helper function measures the execution time of a function and saves the value to a dictionary
    # all execution times are stored in a list accessible by the function name, this enables to calculate an
    # average function runtime
    tic = time.time()  # starting time measurement
    function_return = function(*args)
    toc = time.time() - tic  # stopping time measurement

    if function.__name__ not in tic_toc:
        tic_toc[function.__name__] = []

    tic_toc[function.__name__].append(toc)

    if function.__name__ not in tic_toc_delta:
        tic_toc_delta[function.__name__] = []

    tic_toc_delta[function.__name__].append(toc)

    if do_print:
        # print(function.__name__ + " took: " + str(toc) + " seconds")
        print("average time for " + function.__name__ + ": " +
              str(sum(tic_toc[function.__name__]) / len(tic_toc[function.__name__])))

    return function_return


def reset_delta():
    tic_toc_delta.clear()
