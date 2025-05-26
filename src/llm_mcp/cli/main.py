import click
from click_default_group import DefaultGroup

from llm_mcp import manager


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


@mcp.command()
@click.argument("param")
@click.option("--name", type=str)
@click.option("--overwrite", is_flag=True)
def add(param, name, overwrite):
    """Register an MCP server locally and cache its tool list."""

    cfg = manager.add_server(param, name=name, overwrite=overwrite)
    click.secho(
        f"✔ added server {cfg.name!r} with {len(cfg.tools)} tools",
        fg="green",
    )
