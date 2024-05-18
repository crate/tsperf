import json

from click.testing import CliRunner

import tsperf.cli


def test_schema_list():
    runner = CliRunner()
    result = runner.invoke(
        tsperf.cli.schema,
        [
            "--list",
        ],
    )
    assert result.exit_code == 0

    response = json.loads(result.output)
    assert len(response) >= 4
