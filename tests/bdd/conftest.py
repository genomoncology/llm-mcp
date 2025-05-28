import shlex

import pytest
from click.testing import CliRunner, Result
from llm.cli import cli as llm_cli
from pytest_bdd import given, parsers, then, when


@pytest.fixture(scope="session")
def cli_runner(llm_user_dir) -> CliRunner:
    cli_runner = CliRunner()

    # check path is set via logs path output
    # noinspection PyTypeChecker
    result = cli_runner.invoke(llm_cli, ["logs", "path"])
    assert result.exit_code == 0
    assert str(llm_user_dir / "logs.db") == result.output.strip()

    return cli_runner


# noinspection PyTypeChecker
@given(parsers.parse('I run "{command}"'), target_fixture="cli_result")
@when(parsers.parse('I run "{command}"'), target_fixture="cli_result")
def cli_result(cli_runner, data_dir, command: str) -> Result:
    """Run the CLI command with Click's CliRunner."""
    command = command.replace("$data_dir", str(data_dir))
    args = shlex.split(command)[1:]
    result = cli_runner.invoke(llm_cli, args)
    assert result.exit_code == 0
    return result


@then(parsers.parse('the output should contain "{expected}"'))
def output_should_contain(cli_result, expected: str):
    assert expected in cli_result.output
