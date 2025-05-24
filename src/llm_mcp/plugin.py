import click
import llm

from . import cli as mcp_cli


@llm.hookimpl
def register_tools(register):
    # todo: replace with loading the 'default" tool group
    tools: list[llm.Tool] = []
    for tool in tools:
        register(tool)


@llm.hookimpl
def register_commands(cli: click.Group):
    # noinspection PyTypeChecker
    cli.add_command(mcp_cli.mcp, name="mcp")
