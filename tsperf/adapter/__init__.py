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
from typing import Dict

from tsperf.model.interface import AbstractDatabaseInterface, DatabaseInterfaceType


class AdapterManager:
    registry: Dict[DatabaseInterfaceType, object] = {}

    @classmethod
    def register(cls, interface, factory):
        cls.registry[interface] = factory

    @classmethod
    def get(cls, interface):
        factory: AbstractDatabaseInterface = cls.registry[interface]
        return factory

    @classmethod
    def create(cls, interface, config, schema=None):
        factory: AbstractDatabaseInterface = cls.get(interface)
        return factory(config, schema)


# ruff: noqa: F401
def load_adapters():
    """
    Importing each adapter module will make the respective adapter
    self-register with the adapter manager.

    TODO: Load specific adapter on demand.
    """
    from tsperf.adapter.cratedb import CrateDbAdapter
    from tsperf.adapter.cratedbpg import CrateDbPgWireAdapter
    from tsperf.adapter.dummy import DummyDbAdapter
    from tsperf.adapter.influxdb import InfluxDbAdapter
    from tsperf.adapter.mongodb import MongoDbAdapter
    from tsperf.adapter.mssql import MsSQLDbAdapter
    from tsperf.adapter.postgresql import PostgreSQLAdapter
    from tsperf.adapter.timescaledb import TimescaleDbAdapter
    from tsperf.adapter.timestream import AmazonTimestreamAdapter


class DatabaseInterfaceMixin:
    def __init__(self, config):
        self.config = config

    @property
    def host(self):
        host, port = self.config.address.split(":")
        return host

    @property
    def port(self):
        host, port = self.config.address.split(":")
        return int(port)

    @property
    def username(self):
        username = self.config.username and self.config.username or self.default_username
        return username

    @property
    def password(self):
        username = self.config.password and self.config.password or self.default_password
        return username

    @property
    def database(self):
        username = self.config.database and self.config.database or self.default_database
        return username
