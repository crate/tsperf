import json
import urllib3
import time
import logging
import tictrack
from queue import Queue, Empty
from threading import Thread, current_thread
from batch_size_automator import BatchSizeAutomator
from modules.edge import Edge
from modules.crate_db_writer import CrateDbWriter
from modules.timescale_db_writer import TimescaleDbWriter
from modules.influx_db_writer import InfluxDbWriter
from modules.mongo_db_writer import MongoDbWriter
from modules.postgres_db_writer import PostgresDbWriter
from modules.timestream_db_writer import TimeStreamWriter
from modules.mssql_db_writer import MsSQLDbWriter
from modules.config import DataGeneratorConfig
from prometheus_client import start_http_server, Gauge, Counter


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# load an validate the configuration
config = DataGeneratorConfig()
valid_config = config.validate_config()
if not valid_config:
    logging.error(f"invalid configuration: {config.invalid_configs}")
    exit(-1)

# load the model we want to use and create the metrics
f = open(config.model_path, "r")
model = json.load(f)

# global variables shared accross threads
data_batch_size = (config.id_end - config.id_start + 1)
runtime_metrics = {"rows": 0, "metrics": 0, "batch_size": config.batch_size}
edges = {}
ingest_ts_factor = 1 / config.ingest_delta
last_stat_ts = time.time()
last_ts = config.ingest_ts
current_values_queue = Queue(5000 * config.num_threads)
inserted_values_queue = Queue(5000 * config.num_threads)
stop_queue = Queue(1)
insert_finished_queue = Queue(1)

# prometheus metrics published to port 8000
c_generated_values = Counter("data_gen_generated_values", "How many values have been generated")
c_inserted_values = Counter("data_gen_inserted_values", "How many values have been inserted")
g_insert_percentage = Gauge("data_gen_insert_percentage", "Percentage of values that have been inserted")
if config.batch_size <= 0 and bool(config.ingest_mode):
    g_batch_size = Gauge("data_gen_batch_size", "The currently used batch size", labelnames=("thread",))
    g_insert_time = Gauge("data_gen_insert_time", "The average time it took to insert the current batch into the "
                                                  "database", labelnames=("thread",))
    g_rows_per_second = Gauge("data_gen_rows_per_second", "The average number of rows per second with the latest "
                                                          "batch_size", labelnames=("thread",))
    g_best_batch_size = Gauge("data_gen_best_batch_size", "The up to now best batch size found by the "
                                                          "batch_size_automator", labelnames=("thread",))
    g_best_batch_rps = Gauge("data_gen_best_batch_rps", "The rows per second for the up to now best batch size",
                             labelnames=("thread",))


def get_db_writer():
    # initialize the db_writer based on environment variable
    if config.database == 0:  # crate
        db_writer = CrateDbWriter(config.host, config.username, config.password, model,
                                  config.table_name, config.shards, config.replicas, config.partition)
    elif config.database == 1:  # timescale
        db_writer = TimescaleDbWriter(config.host, config.port, config.username, config.password,
                                      config.db_name, model, config.table_name, config.partition, config.copy,
                                      config.distributed)
    elif config.database == 2:  # influx
        db_writer = InfluxDbWriter(config.host, config.token, config.organization, model, config.db_name)
    elif config.database == 3:  # mongo
        db_writer = MongoDbWriter(config.host, config.username, config.password, config.db_name, model)
    elif config.database == 4:  # postgres
        db_writer = PostgresDbWriter(config.host, config.port, config.username, config.password,
                                     config.db_name, model, config.table_name, config.partition)
    elif config.database == 5:  # timestream
        db_writer = TimeStreamWriter(config.aws_access_key_id, config.aws_secret_access_key,
                                     config.aws_region_name, config.db_name, model)
    elif config.database == 6:  # ms_sql
        db_writer = MsSQLDbWriter(config.host, config.username, config.password,
                                  config.db_name, model, port=config.port, table_name=config.table_name)
    else:
        db_writer = None
    return db_writer


@tictrack.timed_function()
def create_edges():
    # this function creates metric objects in the given range [id_start, id_end]
    for i in range(config.id_start, config.id_end + 1):
        edges[i] = Edge(i, get_sub_element("tags"), get_sub_element("metrics"))


def get_sub_element(sub):
    element = {}
    for key in model.keys():
        if key != "description":
            element = model[key][sub]
    if "description" in element:
        element.pop("description")
    return element


@tictrack.timed_function()
def get_next_value():
    global last_ts
    # for each edge in the edges list all next values are calculated and saved to the edge_value list
    # this list is then added to the FIFO queue, so each entry of the FIFO queue contains all next values for each edge
    # in the edge list
    edge_values = []
    for edge in edges.values():
        edge_values.append(edge.calculate_next_value())
    c_generated_values.inc(len(edge_values))
    if config.ingest_mode == 1:
        ts = last_ts + config.ingest_delta
        last_ts = round(ts * ingest_ts_factor) / ingest_ts_factor
        timestamps = [int(last_ts * 1000)] * len(edge_values)
        current_values_queue.put({"timestamps": timestamps, "batch": edge_values})
    else:
        current_values_queue.put(edge_values)


def calculate_next_value(edge):
    return edge.calculate_next_value()


def log_stat_delta(last_stat_ts_local):
    if time.time() - last_stat_ts_local >= config.stat_delta:
        for key, value in tictrack.tic_toc_delta.items():
            logging.info(f"average time for {key}: {(sum(value) / len(value))}")
        tictrack.tic_toc_delta = {}
    return time.time()


def stat_delta_thread_function():
    last_stat_ts_local = time.time()
    while not stop_process():
        if time.time() - last_stat_ts_local >= config.stat_delta:
            last_stat_ts_local = log_stat_delta(last_stat_ts_local)
        else:
            # we could calculate the exact time to sleep until next output but this would block the
            # the thread until it happens, this would mean at the end the whole data generator could
            # sleep for another `config.stat_delta` seconds before finishing
            time.sleep(1)


def insert_routine():
    name = current_thread().name
    db_writer = get_db_writer()
    db_writer.prepare_database()
    insert_bsa = BatchSizeAutomator(batch_size=config.batch_size,
                                    active=bool(config.ingest_mode),
                                    data_batch_size=data_batch_size)

    while not current_values_queue.empty() or not stop_process():
        batch = []
        timestamps = []

        local_batch_size = insert_bsa.get_next_batch_size()
        if insert_bsa.auto_batch_mode:
            g_batch_size.labels(thread=name).set(local_batch_size)

        while len(batch) < local_batch_size:
            batch_values = current_values_queue.get()
            batch.extend(batch_values["batch"])
            timestamps.extend(batch_values["timestamps"])

        if len(batch) > 0:
            start = time.time()
            try:
                db_writer.insert_stmt(timestamps, batch)
                inserted_values_queue.put_nowait(len(batch))
            except Exception as e:
                # if an exception is thrown while inserting we don't want the whole data_generator to crash
                # as the values have not been inserted we remove them from our runtime_metrics
                # TODO: more sophistic error handling on db_writer level
                logging.error(e)

            if insert_bsa.auto_batch_mode and len(batch) == local_batch_size:
                duration = time.time() - start
                g_insert_time.labels(thread=name).set(duration)
                g_rows_per_second.labels(thread=name).set(len(batch)/duration)
                g_best_batch_size.labels(thread=name).set(insert_bsa.batch_times["best"]["size"])
                g_best_batch_rps.labels(thread=name).set(insert_bsa.batch_times["best"]["batch_per_second"])
                insert_bsa.insert_batch_time(duration)

    db_writer.close_connection()


def spawn_insert_threads():
    insert_threads = []
    for i in range(config.num_threads):
        insert_threads.append(Thread(target=insert_routine, name=f"insert_thread_{i}"))
    for thread in insert_threads:
        thread.start()
    for thread in insert_threads:
        thread.join()
    # signal the prometheus thread that insert is finished
    insert_finished_queue.put_nowait(True)


def fast_insert():
    fast_insert_threads = [Thread(target=spawn_insert_threads, name="spawn_insert_threads"),
                           Thread(target=stat_delta_thread_function, name="stat_delta_thread")]
    for thread in fast_insert_threads:
        thread.start()
    for thread in fast_insert_threads:
        thread.join()


def consecutive_insert():
    global last_ts
    db_writer = get_db_writer()
    db_writer.prepare_database()
    last_insert = config.ingest_ts
    last_stat_ts_local = time.time()
    while not current_values_queue.empty() or not stop_process():
        # we calculate the time delta from the last insert to the current timestamp
        insert_delta = time.time() - last_insert
        # delta needs to be bigger than ingest_delta
        # if delta is smaller than ingest_delta the time difference is waited (as we want an insert
        # every `config.ingest_delta` second
        if insert_delta > config.ingest_delta:
            last_stat_ts_local = log_stat_delta(last_stat_ts_local)
            c_inserted_values.inc(config.id_end - config.id_start + 1)
            batch = current_values_queue.get_nowait()
            ts = time.time()
            # we want the same timestamp for each value this timestamp should be the same
            # even if the data_generator runs in multiple containers therefore we round the
            # timestamp to match ingest_delta this is done by multiplying
            # by ingest_delta and then dividing the result by ingest_delta
            last_insert = round(ts * ingest_ts_factor) / ingest_ts_factor
            timestamps = [int(last_insert * 1000)] * len(batch)
            try:
                db_writer.insert_stmt(timestamps, batch)
                runtime_metrics["rows"] += len(batch)
                runtime_metrics["metrics"] += len(batch) * len(get_sub_element("metrics").keys())
            except Exception as e:
                logging.error(e)
        else:
            time.sleep(config.ingest_delta - insert_delta)
    db_writer.close_connection()
    # signal the prometheus thread that insert is finished
    insert_finished_queue.put_nowait(True)


def stop_process():
    return not stop_queue.empty()


def prometheus_insert_percentage():
    while not inserted_values_queue.empty() or insert_finished_queue.empty():
        try:
            inserted_values = inserted_values_queue.get_nowait()
            c_inserted_values.inc(inserted_values)
            g_insert_percentage.set((c_inserted_values._value.get() /
                                     (config.ingest_size * (config.id_end - config.id_start + 1))) * 100)
        except Empty:
            # get_nowait throws Empty exception which might happen if the inserted_values_queue
            # is empty and the insert_finished_queue is as well
            pass


@tictrack.timed_function()
def main():
    # start the thread that writes to the db
    if config.ingest_mode == 0:
        db_writer_thread = Thread(target=consecutive_insert, name="consecutive_insert_thread")
    else:
        db_writer_thread = Thread(target=fast_insert, name="fast_insert_thread")
    db_writer_thread.start()

    # start the thread that collects the insert metrics from the db_writer threads
    prometheus_insert_percentage_thread = Thread(target=prometheus_insert_percentage,
                                                 name="prometheus_insert_percentage_thread")
    prometheus_insert_percentage_thread.start()

    try:
        create_edges()

        # TODO: this should not have an endless loop for now stop with ctrl+C
        # we are either in endless mode or have a certain amount of values to create
        while_count = 0
        while config.ingest_size == 0 or while_count < config.ingest_size:
            while_count += 1
            get_next_value()
    except Exception as e:
        logging.exception(e)
    finally:
        # once value creation is finished we signal the db_writer thread to stop and wait for it to join
        stop_queue.put(True)
        db_writer_thread.join()
        prometheus_insert_percentage_thread.join()


if __name__ == '__main__':
    # start prometheus server
    start_http_server(8000)

    main()
    main = 0
    # we analyze the runtime of the different function
    for k, v in tictrack.tic_toc.items():
        if k == "main":
            main = sum(v) / len(v)
        logging.info(f"average time for {k}: {(sum(v) / len(v))}")

    logging.info(f"""rows per second:    {data_batch_size * config.ingest_size / main}""")
    logging.info(f"""metrics per second: {data_batch_size * config.ingest_size * len(get_sub_element("metrics").keys()) / main}""")

    # finished
