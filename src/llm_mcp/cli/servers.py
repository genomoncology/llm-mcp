import click

from llm_mcp import manager, store

from . import mcp


@mcp.group()
@click.version_option()
def servers():
    """Command for managing MCP servers."""


@servers.command(name="add")
@click.argument("param")
@click.option("--name", type=str)
@click.option("--overwrite", is_flag=True)
@click.option("--exist-ok", is_flag=True)
def add_server(param, name, overwrite: bool, exist_ok: bool):
    """Register an MCP server locally by storing its Server Config."""

    try:
        cfg = manager.add_server(
            param,
            name=name,
            overwrite=overwrite,
            exist_ok=exist_ok,
        )
    except manager.DuplicateServer as e:
        raise click.ClickException(f"Server {name!r} already exists") from e

    click.secho(
        f"✔ added server {cfg.name!r} with {len(cfg.tools)} tools",
        fg="green",
    )


@servers.command(name="list")
def list_servers():
    """View list of available MCP servers."""
    for name in store.list_servers():
        click.secho(name)


@servers.command(name="view")
@click.argument("name")
@click.option("--indent", type=int, default=2)
def view_server(name: str, indent: int):
    """Display as server config as JSON."""

    cfg = store.load_server(name)
    if cfg is None:
        raise click.ClickException(f"Server {name!r} does not exist")

    # display with indent or remove indent completely if indent <= 0
    click.secho(cfg.model_dump_json(indent=indent if indent > 0 else None))


@servers.command(name="remove")
@click.argument("name")
def remove_server(name):
    """Remove an MCP server if it exists, raise exception otherwise."""

    success = store.remove_server(name)

    if success is False:
        raise click.ClickException(f"Server {name!r} does not exist")

    click.secho(f"✔ removed server {name!r}.", fg="green")
