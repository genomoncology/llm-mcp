import click
import llm

from . import cli as mcp_cli
from . import store, transport


@llm.hookimpl
def register_tools(register):
    """Register all tools from all stored MCP servers."""
    server_names = store.list_servers()

    for name in server_names:
        config = store.load_server(name)
        if config:
            for tool in config.tools:
                llm_tool = transport.convert_tool(config, tool)
                register(llm_tool)


@llm.hookimpl
def register_commands(cli: click.Group):
    # noinspection PyTypeChecker
    cli.add_command(mcp_cli.mcp, name="mcp")
