import logging
import sys

import urllib3


def setup_logging(level=logging.INFO) -> None:
    log_format = "%(asctime)-15s [%(name)-15s] %(levelname)-7s: %(message)s"
    logging.basicConfig(format=log_format, stream=sys.stderr, level=level)

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
