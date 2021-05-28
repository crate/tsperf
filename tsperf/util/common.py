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
import argparse
import logging
import sys
from typing import Dict

import urllib3


def setup_logging(level=logging.INFO) -> None:
    log_format = (
        "%(asctime)-15s [%(threadName)-20s] [%(name)-25s] %(levelname)-7s: %(message)s"
    )
    logging.basicConfig(format=log_format, stream=sys.stderr, level=level)

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def read_configuration(
    config: object, args_info: Dict, description: str
):  # pragma: no cover

    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    for element in vars(config):
        if element in args_info:
            kwargs = {}

            if "action" in args_info[element]:
                kwargs["action"] = args_info[element]["action"]
            if "required" in args_info[element]:
                kwargs["required"] = args_info[element]["required"]
            if "default" in args_info[element]:
                kwargs["default"] = args_info[element]["default"]
            else:
                kwargs["default"] = getattr(config, element)

            if "choices" in args_info[element]:
                kwargs["choices"] = args_info[element]["choices"]
            if "type" in args_info[element]:
                kwargs["type"] = args_info[element]["type"]

            parser.add_argument(
                f"--{element}",
                help=args_info[element]["help"],
                **kwargs,
            )

    arguments = parser.parse_args()
    config.load_args(vars(arguments))
    return config
