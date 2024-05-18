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
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Union

import pkg_resources

from tsperf.adapter import AdapterManager
from tsperf.model.interface import AbstractDatabaseInterface, DatabaseInterfaceType
from tsperf.read.config import QueryTimerConfig
from tsperf.write.config import DataGeneratorConfig

logger = logging.getLogger(__name__)


class TsPerfEngine:
    def __init__(
        self,
        config: Union[DataGeneratorConfig, QueryTimerConfig],
        schema: Optional[Dict] = None,
    ):
        self.config = config
        self.schema = schema or {}

    def adapter_factory(self) -> AbstractDatabaseInterface:
        adapter = AdapterManager.create(
            interface=DatabaseInterfaceType(self.config.adapter),
            config=self.config,
            schema=self.schema,
        )
        return adapter

    def create_adapter(self):
        adapter = self.adapter_factory()
        logger.info(f"Database adapter »{adapter}« loaded successfully")
        return adapter

    def bootstrap(self):
        # Load and validate configuration.
        valid_config = self.config.validate_config()
        if not valid_config:
            logger.error(f"Invalid configuration: {self.config.invalid_configs}")
            sys.exit(-1)

        logger.info(f"Connecting to database at »{self.config.address}« using adapter »{self.config.adapter}«")


def load_schema(schema_reference: Union[str, Path]):
    """
    Load schema for data generation.

    A reference to a schema in JSON format. It can either be the name of a Python resource in
    full-qualified dotted `pkg_resources`-compatible notation, or an absolute or relative path.
    """

    if schema_reference is None:
        logger.info("Not loading any schema")
        return None

    logger.info(f"Loading schema from {schema_reference}")

    if isinstance(schema_reference, Path) or ":" not in schema_reference:
        f = open(schema_reference, "r")
        data = json.load(f)

    else:
        module, name = schema_reference.split(":")
        resource = pkg_resources.resource_stream(module, name)
        data = json.load(resource)

    return data
