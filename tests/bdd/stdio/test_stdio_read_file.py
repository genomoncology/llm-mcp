# import pytest
# from llm.cli import cli as llm_cli
# from pytest_bdd import given, parsers, scenarios, then
#
# scenarios("./stdio/stdio_read_file.feature")
#
# pytestmark = pytest.mark.vcr(record_mode="new_episodes")
#
# # runner = CliRunner()
#
#
# # @given("an empty MCP config directory", target_fixture="mcp_dir")
# # def mcp_dir(tmp_path, monkeypatch) -> Path:
# #     """Provide an isolated $LLM_MCP_HOME so the CLI writes into tmp space."""
# #     home = tmp_path / "mcp_home"
# #     home.mkdir()
# #     monkeypatch.setenv("LLM_MCP_HOME", str(home))
# #     return home
# #
#
#
# @given(
#     "the desktop-commander server is registered",
#     target_fixture="server_registered",
# )
# def server_registered(runner, mcp_dir, data_dir):
#     """Register the desktop-commander server using the CLI."""
#     # Build the command to add the server
#     cmd = "npx -y @wonderwhy-er/desktop-commander"
#
#     # Run the add command with proper cwd
#     # noinspection PyTypeChecker
#     result = runner.invoke(
#         llm_cli,
#         ["mcp", "add", cmd, "--name", "desktop_commander"],
#     )
#
#     assert result.exit_code == 0, f"Failed to add server: {result.output}"
#     assert "added server 'desktop_commander'" in result.output
#     return True
#
#
# #
# # @when(parsers.parse('I run "{command}"'), target_fixture="cli_result")
# # def cli_result(mcp_dir, data_dir, command: str):
# #     """Run the CLI command with Click's CliRunner."""
# #     command = command.replace("$data_dir", str(data_dir))
# #     args = shlex.split(command)[1:]
# #     result = runner.invoke(llm_cli, args)
# #     return result
#
#
# @then(parsers.parse('the output contains "{expected}"'))
# def check_listing(expected, cli_result):
#     assert expected in cli_result.output.lower()
#
#
# @then("the output contains the secret text")
# def check_secret(cli_result, data_dir):
#     secret_file = data_dir / "secret.txt"
#     assert secret_file.is_file()
#     expected = secret_file.read_text().strip().strip('"').lower()
#     assert expected in cli_result.output.lower()
