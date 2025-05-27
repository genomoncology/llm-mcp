"""Business logic for managing MCP servers."""

from . import store, transport, utils
from .schema import ServerConfig


class DuplicateServer(Exception):
    pass


def add_server(
    param_str: str,
    *,
    name: str | None = None,
    overwrite: bool = False,
) -> ServerConfig:
    """
    Parse *param_str*, contact the server, persist its manifest, and return it.

    Args:
        param_str: URL or command line that identifies an MCP server.
        name: Name to use for the server config file.
        overwrite: Replace an existing manifest with the same name if True.
    """
    # parse parameters
    params = utils.parse_params(param_str)
    if params is None:
        raise ValueError(f"Invalid server parameters: {param_str!r}")

    # choose name if not provided
    if name is None:
        name = utils.generate_server_name(params)

    # check name if not overwriting
    if overwrite is False and name in store.list_servers():
        raise DuplicateServer(f"Server {name!r} already exists")

    # pull tool list
    tools = transport.list_tools_sync(params)

    # build & persist manifest
    cfg = ServerConfig(name=name, parameters=params, tools=tools)
    store.save_server(cfg)
    return cfg
