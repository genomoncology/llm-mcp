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
    exist_ok: bool = False,
) -> ServerConfig:
    """
    Parse *param_str*, contact the server, persist its manifest, and return it.

    Args:
        param_str: URL or command line that identifies an MCP server.
        name: Name to use for the server config file.
        overwrite: Replace an existing manifest with the same name if True.
        exist_ok: Silently ignore if a server with name already exists if True.
    """
    # parse parameters
    params = utils.parse_params(param_str)
    if params is None:
        raise ValueError(f"Invalid server parameters: {param_str!r}")

    # generate name
    if name is None:
        name = utils.generate_server_name(params)

    # check if server already exists
    file_exists = name in store.list_servers()

    # overwrite > exist_ok > duplicate error
    cfg: ServerConfig | None = None
    if file_exists and not overwrite:
        if exist_ok:
            cfg = store.load_server(name)
        else:
            raise DuplicateServer(f"Server {name!r} already exists")

    # fetch and rewrite if config is not loaded
    if cfg is None:
        tools = transport.list_tools_sync(params)
        cfg = ServerConfig(name=name, parameters=params, tools=tools)
        store.save_server(cfg)

    return cfg
