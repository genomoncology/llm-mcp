from llm import Tool, user_dir

from . import schema, wrap_mcp


def load_config() -> schema.ConfigFile:
    path = user_dir() / "mcp.json"
    json_text = path.read_text() if path.exists() else "{}"
    return schema.ConfigFile.model_validate_json(json_text)


def get_tools(group_name: str | None = None) -> list[Tool]:
    config = load_config()
    tool_configs = config.get_tools(group_name=group_name)
    collected = []
    # todo: this is wrong. we need to filter by the tools allowed.
    # strategy should be to get all the unique servers and filter by tools
    # and we need to test this using bdd.
    for tool_config in tool_configs:
        server_config = config.get_server(tool_config.mcp_server)
        if server_config:
            collected.extend(wrap_mcp(server_config.parameters))
    return collected
