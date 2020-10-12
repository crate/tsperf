import os
import urllib3
import statistics
import time
import shutil
import modules.helper as helper
from modules.config import DataGeneratorConfig
from modules.crate_db_writer import CrateDbWriter
from modules.postgres_db_writer import PostgresDbWriter
from modules.timescale_db_writer import TimescaleDbWriter
from modules.influx_db_writer import InfluxDbWriter
from modules.mongo_db_writer import MongoDbWriter
from threading import Thread

from modules.timestream_db_writer import TimeStreamWriter

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

host = os.getenv("HOST", "localhost:4200")
port = os.getenv("PORT", "5432")
username = os.getenv("dbUser", None)
password = os.getenv("dbPassword", None)
table_name = os.getenv("TABLE_NAME", "timeseries")
database = int(os.getenv("DATABASE", 0))  # 0:crate, 1:timescale, 2:influx
db_name = os.getenv("DB_NAME", "")
token = os.getenv("TOKEN", "")
concurrency = os.getenv("CONCURRENCY", 10)
iterations = os.getenv("ITERATIONS", 100)
quantile_list = os.getenv("QUANTILES", "50,60,75,90,99")
query = os.getenv("QUERY", 'SELECT * FROM "data_generator_test"."temperature" LIMIT 100')
model = {"value": "none"}

query_results = []
total_queries = 0
stop_thread = False
start_time = time.time()
terminal_size = shutil.get_terminal_size()

config = DataGeneratorConfig()

# initialize the db_writer based on environment variable
if config.database == 0:  # crate
    db_writer = CrateDbWriter(config.host, config.username, config.password, model,
                              config.table_name, config.shards, config.replicas, config.partition)
elif config.database == 1:  # timescale
    db_writer = TimescaleDbWriter(config.host, config.port, config.username, config.password,
                                  config.db_name, model, config.table_name, config.partition)
elif config.database == 2:  # influx
    db_writer = InfluxDbWriter(config.host, config.token, config.organization, model, config.db_name)
elif config.database == 3:  # mongo
    db_writer = MongoDbWriter(config.host, config.username, config.password, config.db_name, model)
    print("QueryTimer for MongoDB needs hardcoded queries inside the query_time.py scripts")
elif config.database == 4:  # postgres
    db_writer = PostgresDbWriter(config.host, config.port, config.username, config.password,
                                 config.db_name, model, config.table_name, config.partition)
elif config.database == 5:  # timestream
    db_writer = TimeStreamWriter(config.aws_access_key_id, config.aws_secret_access_key,
                                 config.aws_region_name, config.db_name, model)
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
    global total_queries, errors
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
        print(f"errors: {errors}")
    # finished
