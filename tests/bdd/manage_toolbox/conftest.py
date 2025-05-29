import json
import shlex
from pathlib import Path

import pytest
from llm.cli import cli as llm_cli
from pytest_bdd import given, parsers, then, when

from llm_mcp import store
from llm_mcp.schema import ToolboxConfig


@pytest.fixture(autouse=True)
def clean_toolboxes():
    """Clean up toolboxes before and after tests."""
    # Clean before
    toolboxes_dir = store.toolboxes_dir()
    if toolboxes_dir.exists():
        for file in toolboxes_dir.glob("*.json"):
            file.unlink()

    # Also clear any default toolbox setting
    settings_file = store.mcp_dir() / "settings.json"
    if settings_file.exists():
        settings = {}
        if settings_file.exists() and settings_file.stat().st_size > 0:
            try:
                settings = json.loads(settings_file.read_text())
                if "default_toolbox" in settings:
                    settings.pop("default_toolbox")
                    settings_file.write_text(json.dumps(settings, indent=2))
            except json.JSONDecodeError:
                # If the file is not valid JSON, just recreate it
                settings_file.write_text("{}")

    yield

    # Clean after
    if toolboxes_dir.exists():
        for file in toolboxes_dir.glob("*.json"):
            file.unlink()


# cli_result is provided by the parent conftest.py


@when(
    parsers.parse('I try to run "{command}"'),
    target_fixture="cli_error_result",
)
def cli_error_result(cli_runner, data_dir, command: str):
    """Run a CLI command that is expected to fail."""
    command = command.replace("$data_dir", str(data_dir))
    args = shlex.split(command)[1:]
    result = cli_runner.invoke(llm_cli, args)
    return result


@then(parsers.parse('it should fail with "{error_message}"'))
def check_error_message(cli_error_result, error_message: str):
    assert cli_error_result.exit_code != 0
    assert error_message in cli_error_result.output


@when(
    "I convert the output to a toolbox config object",
    target_fixture="toolbox_config",
)
def toolbox_config(cli_result) -> ToolboxConfig:
    return ToolboxConfig.model_validate_json(cli_result.output)


@then(parsers.parse('the toolbox config has name "{name}"'))
def check_toolbox_name(toolbox_config: ToolboxConfig, name: str):
    assert toolbox_config.name == name


@then(parsers.parse('the toolbox config has description "{description}"'))
def check_toolbox_description(toolbox_config: ToolboxConfig, description: str):
    assert toolbox_config.description == description


@then(parsers.parse("the toolbox config has {tool_count:d} tools"))
def check_toolbox_tool_count(toolbox_config: ToolboxConfig, tool_count: int):
    assert len(toolbox_config.tools) == tool_count


@then(
    parsers.parse(
        'the toolbox has tool "{tool_name}" with description "{description}"'
    )
)
def check_toolbox_tool(
    toolbox_config: ToolboxConfig, tool_name: str, description: str
):
    tool = next(
        (
            t
            for t in toolbox_config.tools
            if (t.name or t.tool_name) == tool_name
        ),
        None,
    )
    assert tool is not None, f"Tool {tool_name} not found"
    assert tool.description == description


@given(
    parsers.parse('a file "{filename}" with content:'),
    target_fixture="test_file",
)
def test_file(data_dir: Path, filename: str, docstring: str) -> Path:
    """Create a test file with the given content."""
    file_path = data_dir / filename
    file_path.write_text(docstring.strip())
    return file_path


@then(parsers.parse('the output should not contain "{text}"'))
def output_should_not_contain(cli_result, text: str):
    assert text not in cli_result.output
