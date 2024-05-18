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
import logging
from typing import Dict, Optional, Union

import psycopg2

from tsperf.adapter import AdapterManager, DatabaseInterfaceMixin
from tsperf.adapter.cratedb import CrateDbAdapter
from tsperf.model.interface import DatabaseInterfaceType
from tsperf.read.config import QueryTimerConfig
from tsperf.write.config import DataGeneratorConfig

logger = logging.getLogger(__name__)


class CrateDbPgWireAdapter(CrateDbAdapter, DatabaseInterfaceMixin):
    default_address = "localhost:5432"
    default_username = "crate"
    default_query = "SELECT 1;"

    def __init__(
        self,
        config: Union[DataGeneratorConfig, QueryTimerConfig],
        schema: Optional[Dict] = None,
    ):
        DatabaseInterfaceMixin.__init__(self, config=config)

        self.conn = psycopg2.connect(
            dbname=config.database,
            user=self.username,
            password=config.password,
            host=self.host,
            port=self.port,
        )
        self.cursor = self.conn.cursor()
        self.schema = schema
        self.table_name = (config.table, self._get_schema_table_name())[config.table is None or config.table == ""]
        self.partition = config.partition

        logger.info(f"Configuring CrateDB with {config.shards} shards and {config.replicas} replicas")
        self.shards = config.shards
        self.replicas = config.replicas


AdapterManager.register(interface=DatabaseInterfaceType.CrateDBpg, factory=CrateDbPgWireAdapter)
