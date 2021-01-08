from query_timer.argument_parser import args_info
from query_timer.config import QueryTimerConfig


def test_each_config_has_arg():
    config = QueryTimerConfig()
    config_elements = vars(config)
    config_elements.pop("invalid_configs")
    arg_elements = list(args_info)
    assert sorted(arg_elements) == sorted(list(config_elements))
