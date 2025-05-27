from pytest_bdd import when

from llm_mcp.schema import ServerConfig


@when(
    "I convert the output to a server config object",
    target_fixture="server_config",
)
def server_config(cli_result) -> ServerConfig:
    return ServerConfig.model_validate_json(cli_result.stdout)
