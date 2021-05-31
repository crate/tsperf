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
from tsperf.util.common import read_configuration

from .config import QueryTimerConfig

args_info = {
    "quantiles": {
        "help": "Which quantiles should be displayed at the end of the run. Values "
        "are separated by ','",
        "type": str,
    },
    "refresh_rate": {
        "help": "Output refresh interval in seconds.",
        "type": float,
    },
}


def parse_arguments(config: QueryTimerConfig) -> QueryTimerConfig:  # pragma: no cover
    return read_configuration(
        config=config,
        args_info=args_info,
        description="Timeseries Database Query Timer - A program to benchmark TSDBs.",
    )
