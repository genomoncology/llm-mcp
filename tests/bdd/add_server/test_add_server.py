import json
import shlex
from pathlib import Path

import pytest
from click.testing import CliRunner
from pytest_bdd import given, parsers, scenarios, then, when

from llm_mcp.cli.main import mcp
from llm_mcp.schema import ServerConfig

scenarios("./add_server/add_server.feature")

runner = CliRunner()

# We'll record the initial probe to https://gitmcp.io/… exactly once
pytestmark = pytest.mark.vcr(record_mode="once")


@given("an empty MCP config directory", target_fixture="mcp_dir")
def mcp_dir(tmp_path, monkeypatch) -> Path:
    """Provide an isolated $LLM_MCP_HOME so the CLI writes into tmp space."""
    home = tmp_path / "mcp_home"
    home.mkdir()
    monkeypatch.setenv("LLM_MCP_HOME", str(home))
    return home


@when(parsers.parse('I run "{command}"'), target_fixture="cli_result")
def cli_result(mcp_dir, command: str):
    """Run the CLI command with Click's CliRunner."""
    args = shlex.split(command)
    if args[0] == "llm_mcp":
        args = args[1:]

    # noinspection PyTypeChecker
    result = runner.invoke(mcp, args)
    assert result.exit_code == 0, f"CLI failed: {result.output}"
    return result


@when(
    parsers.parse('load the output server manifest should be "{tool_file}"'),
    target_fixture="server_config",
)
def server_config(mcp_dir: Path, tool_file: str) -> ServerConfig:
    tool_file_path = mcp_dir / "servers" / tool_file
    assert tool_file_path.exists(), f"Tool file not found: {tool_file_path}"
    data = json.loads(tool_file_path.read_text())
    return ServerConfig.model_validate(data)


@then(parsers.parse('the output should contain "{expected}"'))
def output_should_contain(cli_result, expected: str):
    assert expected.lower() in cli_result.stdout.lower()


@then(parsers.parse('the manifest lists the tool "{tool_name}"'))
def manifest_contains_tool(tool_name: str):
    path: Path = pytest.manifest_path  # type: ignore[attr-defined]
    data = json.loads(path.read_text())
    tool_names = {t["name"] for t in data.get("tools", [])}
    assert tool_name in tool_names, (
        f"{tool_name!r} not found in manifest tools: {tool_names}"
    )


@then('"fetch_llm_documentation" lacks annotations or input schema')
def check_fetch_llm_documentation(server_config: ServerConfig):
    tool = server_config.get_tool("fetch_llm_documentation")
    assert tool.inputSchema == {}
    assert tool.annotations.model_extra == {}


@then('"search_llm_documentation" has "query" as a required parameter')
def check_search_llm_documentation(server_config: ServerConfig):
    tool = server_config.get_tool("search_llm_documentation")
    assert "query" in tool.inputSchema.get("required", [])
    assert tool.inputSchema.get("properties", {}).get("query")
