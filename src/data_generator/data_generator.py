import json
import queue
import urllib3
import time
import logging
from tictrack import timed_function, tic_toc, tic_toc_delta, reset_delta
from modules.edge import Edge
from modules.crate_db_writer import CrateDbWriter
from modules.timescale_db_writer import TimescaleDbWriter
from modules.influx_db_writer import InfluxDbWriter
from modules.mongo_db_writer import MongoDbWriter
from modules.postgres_db_writer import PostgresDbWriter
from modules.timestream_db_writer import TimeStreamWriter
from modules.batch_size_automator import BatchSizeAutomator
from modules.config import DataGeneratorConfig
from threading import Thread
from prometheus_client import start_http_server, Gauge, Counter


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# load an validate the configuration
config = DataGeneratorConfig()
valid_config = config.validate_config()
if not valid_config:
    logging.error(f"invalid configuration: {config.invalid_configs}")
    exit(-1)

stop_thread = False
# load the model we want to use and create the metrics
f = open(config.model_path, "r")
model = json.load(f)

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
else:
    db_writer = None

batch_size_automator = BatchSizeAutomator(config.batch_size, config.ingest_mode, config.id_end - config.id_start + 1)

runtime_metrics = {"rows": 0, "metrics": 0, "batch_size": config.batch_size}
edges = {}
current_values = queue.Queue(5000)

c_generated_values = Counter("data_gen_generated_values", "How many values have been generated")
c_inserted_values = Counter("data_gen_inserted_values", "How many values have been inserted")
g_insert_percentage = Gauge("data_gen_insert_percentage", "Percentage of values that have been inserted")
if batch_size_automator.auto_batch_mode:
    g_batch_size = Gauge("data_gen_batch_size", "The currently used batch size")
    g_insert_time = Gauge("data_gen_insert_time", "The average time it took to insert the current batch into the "
                                                  "database")
    g_rows_per_second = Gauge("data_gen_rows_per_second", "The average number of rows per second with the latest "
                                                          "batch_size")
    g_best_batch_size = Gauge("data_gen_best_batch_size", "The up to now best batch size found by the "
                                                          "batch_size_automator")
    g_best_batch_rps = Gauge("data_gen_best_batch_rps", "The rows per second for the up to now best batch size")


@timed_function()
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


@timed_function()
def get_next_value():
    # for each edge in the edges list all next values are calculated and saved to the edge_value list
    # this list is then added to the FIFO queue, so each entry of the FIFO queue contains all next values for each edge
    # in the edge list
    edge_values = []
    for edge in edges.values():
        c_generated_values.inc()
        edge_values.append(edge.calculate_next_value())
    current_values.put(edge_values)


def write_to_db():
    global db_writer, tic_toc_delta
    last_insert = config.ingest_ts
    last_stat_ts = time.time()
    # while the queue is not empty and the value creation has not yet finished the loop will call the insert_operation
    # function. Because at the beginning of the script the queue is empty we use the stop_thread variable but because
    # once the value creation is done we still ned to insert the outstanding values in the queue we check if the queue
    # is empty
    while not current_values.empty() or not stop_thread:
        if not current_values.empty():
            # we calculate the time delta from the last insert to the current timestamp
            insert_delta = time.time() - last_insert
            # if we use the ingest_mode the delta can be ignored
            # otherwise delta needs to be bigger than ingest_delta
            # if delta is smaller than ingest_delta the time difference is waited (as we want an insert
            # every half second (default)
            if config.ingest_mode == 1 or insert_delta > config.ingest_delta:
                last_insert = insert_routine(last_insert)
            else:
                time.sleep(config.ingest_delta - insert_delta)
        if time.time() - last_stat_ts >= config.stat_delta:
            for key, value in tic_toc_delta.items():
                print(f"""average time for {key}: {(sum(value) / len(value))}""")
            tic_toc_delta = {}
            last_stat_ts = time.time()
    db_writer.close_connection()


@timed_function()
def insert_routine(last_ts):
    global db_writer
    batch = []
    timestamps = []
    start = None

    if batch_size_automator.auto_batch_mode:
        runtime_metrics["batch_size"] = batch_size_automator.get_next_batch_size()
        g_batch_size.set(runtime_metrics["batch_size"])
        start = time.time()

    if config.ingest_mode == 1:
        # during ingest mode execution time increase with the amount of queries we execute therefor we insert as
        # many batches as possible at a time (batch size of 10000 was empirically the best)
        while len(batch) < runtime_metrics["batch_size"]:
            if not current_values.empty():
                c_inserted_values.inc(config.id_end - config.id_start + 1)
                ts = last_ts + config.ingest_delta
                next_batch = current_values.get()
                batch.extend(next_batch)
                factor = 1 / config.ingest_delta
                last_ts = round(ts * factor) / factor
                timestamps.extend([int(last_ts * 1000)] * len(next_batch))
            else:
                break
        g_insert_percentage.set((c_inserted_values._value.get() /
                                 (config.ingest_size * (config.id_end - config.id_start + 1))) * 100)
    else:
        c_inserted_values.inc(config.id_end - config.id_start + 1)
        batch = current_values.get()
        ts = time.time()
        # we want the same timestamp for each value this timestamp should be the same even if the data_generator
        # runs in multiple containers therefor we round the timestamp to match ingest_delta this is done by multiplying
        # by ingest_delta and then dividing the result by ingest_delta
        delta_factor = 1 / config.ingest_delta
        last_ts = round(ts * delta_factor) / delta_factor
        timestamps = [int(last_ts * 1000)] * len(batch)

    runtime_metrics["rows"] += len(batch)
    runtime_metrics["metrics"] += len(batch) * len(get_sub_element("metrics").keys())

    try:
        db_writer.insert_stmt(timestamps, batch)
    except Exception as e:
        # if an exception is thrown while inserting we don't want the whole data_generator to crash
        # as the values have not been inserted we remove them from our runtime_metrics
        # TODO: more sophistic error handling on db_writer level
        logging.error(e)
        runtime_metrics["rows"] -= len(batch)
        runtime_metrics["metrics"] -= len(batch) * len(get_sub_element("metrics").keys())

    if batch_size_automator.auto_batch_mode:
        duration = time.time() - start
        g_insert_time.set(duration)
        g_rows_per_second.set(len(batch)/duration)
        g_best_batch_size.set(batch_size_automator.batch_times["best"]["size"])
        g_best_batch_rps.set(batch_size_automator.batch_times["best"]["batch_per_second"])
        batch_size_automator.insert_batch_time(duration)

    # we return the timestamp so we know when the last insert happened
    return last_ts


@timed_function()
def main():
    # prepare the database (create the table/bucket/collection if not existing)
    db_writer.prepare_database()

    # start the thread that writes to the db
    db_writer_thread = Thread(target=write_to_db)
    db_writer_thread.start()
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
        global stop_thread
        stop_thread = True
        db_writer_thread.join()


if __name__ == '__main__':
    # start prometheus server
    start_http_server(8000)

    main()
    main = 0
    # we analyze the runtime of the different function
    for k, v in tic_toc.items():
        if k == "main":
            main = sum(v) / len(v)
        print(f"""average time for {k}: {(sum(v) / len(v))}""")

    print(f"""rows per second:    {runtime_metrics["rows"] / main}""")
    print(f"""metrics per second: {runtime_metrics["metrics"] / main}""")
    print(f"""batch_size:         {batch_size_automator.batch_times["best"]["size"]}""")
    print(f"""batches/second:     {batch_size_automator.batch_times["best"]["batch_per_second"]}""")

    # finished
