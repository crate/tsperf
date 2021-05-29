import pytest
from click.testing import CliRunner

import tsperf.cli
from tsperf.model.interface import DatabaseInterfaceType
from tsperf.write.config import DataGeneratorConfig


@pytest.mark.skip
def test_write_cli():
    runner = CliRunner()
    result = runner.invoke(
        tsperf.cli.write,
        [
            "--schema=foobar.json",
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
            "--schema=foobar.json",
            "--adapter=cratedb",
            "--id-end=3",
            "--ingest-size=3",
        ],
    )
    options = ctx.params
    config = DataGeneratorConfig.create(**options)

    assert config.schema == "foobar.json"
    assert config.adapter == DatabaseInterfaceType.CrateDB
    assert config.id_end == 3
    assert config.ingest_size == 3
