import click

from llm_mcp import manager, store

from . import mcp


@mcp.group()
@click.version_option()
def servers():
    """Command for managing MCP servers."""


@servers.command(name="add")
@click.argument("param", required=False)
@click.option("--name", type=str)
@click.option("--overwrite", is_flag=True)
@click.option("--exist-ok", is_flag=True)
@click.option(
    "--manifest",
    type=str,
    help="Path to a JSON manifest file or a JSON string for offline/stub server registration",
)
def add_server(
    param, name, overwrite: bool, exist_ok: bool, manifest: str | None = None
):
    """Register an MCP server locally by storing its Server Config.

    If --manifest is provided, the server will be registered offline without
    attempting to connect to a live MCP server. The manifest can be a path to a
    JSON file or a JSON string literal.

    When using --manifest, 'parameters' is accepted as an alias for 'inputSchema' in tool definitions,
    and hyphens are allowed in server names.
    """
    if param is None and manifest is None:
        raise click.ClickException(
            "Either a server parameter or --manifest must be provided"
        )

    if param is not None and manifest is not None:
        raise click.ClickException(
            "Cannot provide both a server parameter and --manifest"
        )

    try:
        cfg = manager.add_server(
            param if manifest is None else None,
            name=name,
            overwrite=overwrite,
            exist_ok=exist_ok,
            manifest_data=manifest,
        )
    except manager.DuplicateServer as e:
        raise click.ClickException(f"Server {name!r} already exists") from e
    except ValueError as e:
        raise click.ClickException(str(e)) from e

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
