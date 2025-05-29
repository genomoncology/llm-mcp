import click
import llm

from . import cli as mcp_cli
from . import store, transport
from .toolbox_builder import register_toolbox_tools


@llm.hookimpl
def register_tools(register):
    """Register tools based on configuration."""
    # Check for default toolbox
    default_toolbox_name = store.get_default_toolbox()

    if default_toolbox_name:
        # If a default toolbox is set, register only those tools
        register_toolbox_tools(register)
    else:
        # Current behavior: register all MCP server tools directly
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
