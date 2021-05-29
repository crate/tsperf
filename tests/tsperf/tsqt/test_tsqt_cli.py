import pytest
from click.testing import CliRunner

import tsperf
from tsperf.model.interface import DatabaseInterfaceType
from tsperf.tsqt.config import QueryTimerConfig


@pytest.mark.skip
def test_read_cli():
    runner = CliRunner()
    result = runner.invoke(
        tsperf.cli.read,
        [
            "--adapter=cratedb",
        ],
    )
    assert result.exit_code == 0
    # assert result.output == 'Hello Peter!\n'


def test_read_cli_dryrun():
    ctx = tsperf.cli.read.make_context(
        info_name=None,
        args=[
            "--adapter=cratedb",
        ],
    )
    config = QueryTimerConfig.create(**ctx.params)

    assert config.adapter == DatabaseInterfaceType.CrateDB
