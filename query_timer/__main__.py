import curses
import numpy
import os
import urllib3
import statistics
import time
import shutil
from queue import Queue
from tictrack import tic_toc, timed_function
from threading import Thread
from data_generator.config import DataGeneratorConfig
from data_generator.crate_db_writer import CrateDbWriter
from data_generator.postgres_db_writer import PostgresDbWriter
from data_generator.timescale_db_writer import TimescaleDbWriter
from data_generator.influx_db_writer import InfluxDbWriter
from data_generator.mongo_db_writer import MongoDbWriter
from data_generator.mssql_db_writer import MsSQLDbWriter
from data_generator.db_writer import DbWriter

from data_generator.timestream_db_writer import TimeStreamWriter

console = curses.initscr()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

concurrency = int(os.getenv("CONCURRENCY", 100))
iterations = int(os.getenv("ITERATIONS", 100))
quantile_list = os.getenv("QUANTILES", "50,60,75,90,99")
refresh_rate = float(os.getenv("REFRESH_RATE", 0.1))
query = os.getenv("QUERY", 'SELECT * FROM table LIMIT 100')
model = {"value": "none"}

stop_thread = False
start_time = time.time()
success = 0
failure = 0
queries_done = Queue(1)

config = DataGeneratorConfig()

def get_db_writer() -> DbWriter:  # noqa
    if config.database == 0:  # crate
        db_writer = CrateDbWriter(config.host, config.username, config.password, model)
    elif config.database == 1:  # timescale
        db_writer = TimescaleDbWriter(config.host, config.port, config.username, config.password,
                                      config.db_name, model)
    elif config.database == 2:  # influx
        db_writer = InfluxDbWriter(config.host, config.token, config.organization, model)
    elif config.database == 3:  # mongo
        raise ValueError("MongoDB queries are not supported (but can be manually added to the script - see "
                         "query_timer documentation)")
        # db_writer = MongoDbWriter(config.host, config.username, config.password, config.db_name, model)
    elif config.database == 4:  # postgres
        db_writer = PostgresDbWriter(config.host, config.port, config.username, config.password,
                                     config.db_name, model)
    elif config.database == 5:  # timestream
        db_writer = TimeStreamWriter(config.aws_access_key_id, config.aws_secret_access_key,
                                     config.aws_region_name, config.db_name, model)
    elif config.database == 6:  # ms_sql
        db_writer = MsSQLDbWriter(config.host, config.username, config.password,
                                  config.db_name, model, port=config.port)
    else:
        db_writer = None
    return db_writer


@timed_function()
def print_progressbar(iteration, total, prefix="", suffix="", decimals=1, length=100, fill='█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    now = time.time()
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)

    if "execute_query" in tic_toc:
        values = tic_toc["execute_query"]
        console.addstr(3, 0, f"{prefix} |{bar}| {percent}%% {suffix} {round(now - start_time, 2)}s")
        if len(values) > 1:
            pass
            console.addstr(5, 0, f"rate : {round((1 / numpy.mean(values)) * concurrency, 3)}qs/s\n")
            console.addstr(6, 0, f"mean : {round(numpy.mean(values) * 1000, 3)}ms\n")
            console.addstr(7, 0, f"stdev: {round(numpy.std(values) * 1000, 3)}ms\n")
            console.addstr(8, 0, f"min  : {round(min(values) * 1000, 3)}ms\n")
            console.addstr(9, 0, f"max  : {round(max(values) * 1000, 3)}ms\n")
            console.addstr(10, 0, f"success: {success} - failure: {failure}")
    console.refresh()


def start_query_run():
    global success, failure
    db_writer = get_db_writer()
    for x in range(0, iterations):
        try:
            db_writer.execute_query(query)
            success += 1
        except Exception:
            failure += 1


def print_progress_thread():
    while queries_done.empty():
        time.sleep(refresh_rate)
        total_queries = success + failure
        terminal_size = shutil.get_terminal_size()
        print_progressbar(total_queries, concurrency * iterations,
                          prefix='Progress:', suffix='Complete', length=(terminal_size.columns - 40))


def run_qt():
    global start_time
    start_time = time.time()
    progress_thread = Thread(target=print_progress_thread)
    progress_thread.start()
    threads = []
    for y in range(0, concurrency):
        thread = Thread(target=start_query_run)
        threads.append(thread)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    queries_done.put_nowait(True)
    progress_thread.join()


def main():
    terminal_size = shutil.get_terminal_size()
    if concurrency * iterations < 100:
        raise ValueError("query_timer needs at least 100 queries (concurrent * iterations) to work properly")
    q_list = quantile_list.split(",")
    if terminal_size.lines < len(q_list) + 11:
        raise ValueError(f"query_timer needs a terminal windows with a hight of at least {len(q_list) + 10}. "
                         f"Try reducing values in environment variable QUANTILES")

    console.addstr(f"""concurrency: {concurrency}\niterations : {iterations}""")
    console.refresh()
    terminal_size = shutil.get_terminal_size()
    print_progressbar(0, concurrency * iterations,
                      prefix='Progress:', suffix='Complete', length=(terminal_size.columns - 40))

    run_qt()

    if "execute_query" in tic_toc:
        values = tic_toc["execute_query"]
        qus = statistics.quantiles(values, n=100, method="inclusive")
        line = 11
        for i in range(0, len(qus)):
            if str(i + 1) in q_list:
                line += 1
                console.addstr(line, 0, f"p{i+1}  : {round(qus[i]*1000, 3)}ms")
    console.refresh()


if __name__ == '__main__':
    main()
