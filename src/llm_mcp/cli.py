import click
from click_default_group import DefaultGroup


@click.group(
    cls=DefaultGroup,
    default="serve",
    default_if_no_args=True,
)
@click.version_option()
def mcp():
    """
    Model Context Protocol (MCP) plugin for LLM.

    Plugin Repository: https://github.com/genomoncology/llm-mcp
    `llm` Documentation: https://llm.datasette.io/
    """


@mcp.command(name="serve")
@click.argument("group_name", required=False)
def serve(group_name: str):
    click.echo(f"MCP serve called: {group_name}")
