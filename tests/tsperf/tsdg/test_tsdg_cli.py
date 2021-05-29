import pytest
from click.testing import CliRunner

import tsperf.cli
from tsperf.model.interface import DatabaseInterfaceType
from tsperf.tsdg.config import DataGeneratorConfig


@pytest.mark.skip
def test_write_cli():
    runner = CliRunner()
    result = runner.invoke(
        tsperf.cli.write,
        [
            "--model=examples/temperature.json",
            "--adapter=cratedb",
            "--id-end=3",
            "--ingest-size=3",
        ],
    )
    assert result.exit_code == 0
    # assert result.output == 'Hello Peter!\n'


def test_write_cli_dryrun():
    ctx = tsperf.cli.write.make_context(
        info_name=None,
        args=[
            "--model=examples/temperature.json",
            "--adapter=cratedb",
            "--id-end=3",
            "--ingest-size=3",
        ],
    )
    options = ctx.params
    config = DataGeneratorConfig.create(**options)

    assert config.model == "examples/temperature.json"
    assert config.adapter == DatabaseInterfaceType.CrateDB
    assert config.id_end == 3
    assert config.ingest_size == 3
