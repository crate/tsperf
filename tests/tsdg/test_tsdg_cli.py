from tsdg.cli import args_info
from tsdg.config import DataGeneratorConfig


def test_each_config_has_arg():
    config = DataGeneratorConfig()
    config_elements = vars(config)
    config_elements.pop("invalid_configs")
    arg_elements = list(args_info)
    assert sorted(arg_elements) == sorted(list(config_elements))
