import os
import urllib3
import statistics
import time
import shutil
import json
import modules.helper as helper
from modules.crate_db_writer import CrateDbWriter
from modules.timescale_db_writer import TimescaleDbWriter
from modules.influx_db_writer import InfluxDbWriter
from modules.mongo_db_writer import MongoDbWriter
from threading import Thread


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

host = os.getenv("HOST", "localhost:4200")
port = os.getenv("PORT", "5432")
username = os.getenv("dbUser", None)
password = os.getenv("dbPassword", None)
table_name = os.getenv("TABLE_NAME", "timeseries")
database = int(os.getenv("DATABASE", 0))  # 0:crate, 1:timescale, 2:influx
db_name = os.getenv("DB_NAME", "")
token = os.getenv("TOKEN", "")
concurrency = os.getenv("CONCURRENCY", 20)
iterations = os.getenv("ITERATIONS", 50)
quantile_list = os.getenv("QUANTILES", "50,60,75,90,99")
query = os.getenv("QUERY", "SELECT COUNT(*) FROM timeseries;")

query_results = []
total_queries = 0
stop_thread = False
start_time = time.time()
terminal_size = shutil.get_terminal_size()

if database == 0:  # crate
    db_writer = CrateDbWriter(host, username, password, table_name)
elif database == 1:  # timescale
    db_writer = TimescaleDbWriter(host, username, password, table_name, db_name, port)
elif database == 2:  # influx
    db_writer = InfluxDbWriter(host, token, db_name)
elif database == 3:  # mongo
    db_writer = MongoDbWriter(host, username, password, db_name)
    query = json.loads(query)  # mongo uses queries in json format
else:
    db_writer = None


def print_progressbar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', print_end="\r"):
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
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    now = time.time()
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print('\r%s |%s| %s%% %s %ss' % (prefix, bar, percent, suffix, round(now-start_time, 2)), end=print_end)
    # Print New Line on Complete
    if iteration == total:
        print()
    os.get_terminal_size()


def start_query_run():
    global total_queries
    for x in range(0, iterations):
        result = helper.execute_timed_function(db_writer.execute_query, query)
        total_queries += 1
        terminal_size_thread = shutil.get_terminal_size()
        print_progressbar(total_queries, concurrency * iterations,
                          prefix='Progress:', suffix='Complete', length=(terminal_size_thread.columns - 40))
        query_results.append(result)


def main():
    global start_time
    start_time = time.time()
    threads = []
    for y in range(0, concurrency):
        thread = Thread(target=start_query_run)
        threads.append(thread)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


if __name__ == '__main__':
    if concurrency * iterations < 100:
        raise ValueError("query_timer needs at least 100 queries (concurrent * iterations) to work properly")

    print(f"""concurrency: {concurrency}\niterations : {iterations}""")
    print_progressbar(0, concurrency * iterations,
                      prefix='Progress:', suffix='Complete', length=(terminal_size.columns - 40))

    main()
    q_list = quantile_list.split(",")
    for k, v in helper.tic_toc.items():
        # TODO: define rate, currently it is: iterations per average duration per second times concurrency
        print(f"""rate : {round(((iterations * concurrency) / (statistics.mean(v)*1000)) * concurrency, 3)}qs/s""")
        print(f"""mean : {round(statistics.mean(v)*1000, 3)}ms""")
        print(f"""stdev: {round(statistics.stdev(v)*1000, 3)}ms""")
        print(f"""min  : {round(min(v)*1000, 3)}ms""")
        print(f"""max  : {round(max(v)*1000, 3)}ms""")
        qus = statistics.quantiles(v, n=100, method="inclusive")
        for i in range(0, len(qus)):
            if str(i + 1) in q_list:
                print(f"""p{i+1}  : {round(qus[i]*1000, 3)}ms""")

    # finished
