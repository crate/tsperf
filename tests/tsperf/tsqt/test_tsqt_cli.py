from tsperf.tsqt.cli import args_info
from tsperf.tsqt.config import QueryTimerConfig


def test_each_config_has_arg():
    config = QueryTimerConfig()
    config_elements = vars(config)
    config_elements.pop("invalid_configs")
    config_elements.pop("partition")
    config_elements.pop("table_name")
    config_elements.pop("replicas")
    config_elements.pop("shards")
    arg_elements = list(args_info)
    assert sorted(arg_elements) == sorted(list(config_elements))
