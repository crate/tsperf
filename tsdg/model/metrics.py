# -*- coding: utf-8; -*-
#
# Licensed to Crate.io GmbH ("Crate") under one or more contributor
# license agreements.  See the NOTICE file distributed with this work for
# additional information regarding copyright ownership.  Crate licenses
# this file to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  You may
# obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations
# under the License.
#
# However, if you have executed another commercial license agreement
# with Crate these terms will supersede the license and you may use the
# software solely pursuant to the terms of the relevant commercial agreement.
"""
Define Prometheus metrics published to port config.prometheus_port
"""
from prometheus_client import Counter, Gauge

c_values_queue_was_empty = Counter(
    "data_gen_values_queue_empty",
    "How many times the values_queue was empty when "
    "insert_routine needed more values",
)
c_inserts_performed_success = Counter(
    "data_gen_inserts_performed_success",
    "How many times the an insert into the " "database was performed successfully",
)
c_inserts_failed = Counter(
    "data_gen_inserts_failed",
    "How many times an insert operation failed due to an error",
)
c_generated_values = Counter(
    "data_gen_generated_values", "How many values have been generated"
)
c_inserted_values = Counter(
    "data_gen_inserted_values", "How many values have been inserted"
)
g_insert_percentage = Gauge(
    "data_gen_insert_percentage", "Percentage of values that have been inserted"
)
g_batch_size = Gauge(
    "data_gen_batch_size", "The currently used batch size", labelnames=("thread",)
)
g_insert_time = Gauge(
    "data_gen_insert_time",
    "The average time it took to insert the current batch into the " "database",
    labelnames=("thread",),
)
g_rows_per_second = Gauge(
    "data_gen_rows_per_second",
    "The average number of rows per second with the latest " "batch_size",
    labelnames=("thread",),
)
g_best_batch_size = Gauge(
    "data_gen_best_batch_size",
    "The up to now best batch size found by the " "batch_size_automator",
    labelnames=("thread",),
)
g_best_batch_rps = Gauge(
    "data_gen_best_batch_rps",
    "The rows per second for the up to now best batch size",
    labelnames=("thread",),
)
