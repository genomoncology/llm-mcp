import click
import llm

from . import cli as mcp_cli
from . import config


@llm.hookimpl
def register_tools(register):
    tools = config.get_tools()
    for tool in tools:
        register(tool)


@llm.hookimpl
def register_commands(cli: click.Group):
    # noinspection PyTypeChecker
    cli.add_command(mcp_cli.mcp, name="mcp")
