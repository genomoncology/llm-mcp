"""Business logic for managing MCP servers."""

from . import store, transport, utils
from .schema import ServerConfig, StdioServerParameters


class DuplicateServer(Exception):
    pass


def _create_config_from_manifest(
    manifest_data: str, name: str | None = None
) -> tuple[ServerConfig, str]:
    """Create a ServerConfig from a manifest file or JSON string."""
    # Load and parse the manifest
    manifest = utils.load_manifest(manifest_data)

    # Extract server name from manifest if not provided
    manifest_name = manifest.get("name")
    if name is None and manifest_name:
        name = manifest_name
    elif name is None:
        # Generate a placeholder name if not in manifest
        from datetime import datetime

        name = f"stub-server-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # Ensure tools list exists with defensive defaults
    tools = manifest.get("tools", [])

    # Normalize each tool entry to satisfy mcp.types.Tool
    for tool in tools:
        # Convert 'parameters' to 'inputSchema' if present
        tool.setdefault("inputSchema", tool.pop("parameters", {}))
        # Clean up annotations if present
        tool.pop("annotations", None)
        # Ensure description has a default
        tool.setdefault("description", "")

    # Create a stub parameters object or extract from manifest
    parameters = manifest.get("parameters", None)
    if parameters is None:
        # Create stub parameters
        parameters = StdioServerParameters(command="stub", args=[])

    # Create ServerConfig
    try:
        # Remove parameters from manifest to avoid conflicts
        if "parameters" in manifest:
            del manifest["parameters"]

        # Use a clean manifest dict for other properties
        manifest_copy = {
            k: v
            for k, v in manifest.items()
            if k not in {"name", "parameters"}
        }
        # Ensure the normalized tools are used
        manifest_copy["tools"] = tools

        cfg = ServerConfig(name=name, parameters=parameters, **manifest_copy)
    except Exception as e:
        raise ValueError(f"Invalid server manifest: {e}") from e
    else:
        return cfg, name


def _create_config_from_live_server(
    param_str: str, name: str | None = None
) -> tuple[ServerConfig | None, str]:
    """Create a ServerConfig by connecting to a live server."""
    # Parse parameters
    params = utils.parse_params(param_str)
    if params is None:
        raise ValueError(f"Invalid server parameters: {param_str!r}")

    # Generate name if not provided
    if name is None:
        name = utils.generate_server_name(params)

    # For now, just return the name - we'll fetch tools later if needed
    return None, name


def _handle_existing_server(
    name: str, exist_ok: bool, overwrite: bool, is_manifest_mode: bool
) -> ServerConfig | None:
    """Handle cases where a server with the given name already exists."""
    file_exists = name in store.list_servers()

    if not file_exists or overwrite:
        return None  # Need to create/overwrite the server

    if exist_ok:
        existing_cfg = store.load_server(name)
        if not is_manifest_mode:  # For live server mode
            return existing_cfg
        return None  # For manifest mode, continue and save the new config

    # Not exist_ok, not overwrite, but file exists
    raise DuplicateServer(f"Server {name!r} already exists")


def add_server(
    param_str: str | None = None,
    *,
    name: str | None = None,
    overwrite: bool = False,
    exist_ok: bool = False,
    manifest_data: str | None = None,
) -> ServerConfig:
    """
    Register an MCP server by contacting a live server or using a manifest.

    There are two modes of operation:
    1. Live server: Parse *param_str*, contact the server, fetch tools, and persist the manifest.
    2. Offline/stub server: Load a manifest from a file or JSON string, validate it, and persist it.

    Args:
        param_str: URL or command line that identifies an MCP server. Required if manifest_data is None.
        name: Name to use for the server config file. If None, derived from manifest or parameters.
        overwrite: Replace an existing manifest with the same name if True.
        exist_ok: Silently ignore if a server with name already exists if True.
        manifest_data: Path to a JSON file or a JSON string containing a server manifest. If provided, no server
                      connection is attempted.
    """
    # Type annotation for the configuration variable
    cfg: ServerConfig | None = None

    # Validate inputs
    if param_str is None and manifest_data is None:
        raise ValueError("Either param_str or manifest_data must be provided")

    if param_str is not None and manifest_data is not None:
        raise ValueError("Cannot provide both param_str and manifest_data")

    # Determine the mode and create initial config
    is_manifest_mode = manifest_data is not None

    if is_manifest_mode:
        # We've already validated that manifest_data is not None in this branch
        assert manifest_data is not None
        cfg, name = _create_config_from_manifest(manifest_data, name)
    else:
        # We've already validated that param_str is not None in this branch
        assert param_str is not None
        cfg, name = _create_config_from_live_server(param_str, name)

    # Check for existing server with this name
    existing_cfg = _handle_existing_server(
        name, exist_ok, overwrite, is_manifest_mode
    )
    if existing_cfg is not None:
        return existing_cfg

    # If we're in live server mode and haven't created the config yet, fetch tools
    if not is_manifest_mode and cfg is None:
        assert param_str is not None
        params = utils.parse_params(param_str)  # We validated this earlier
        # We should have already validated params is not None earlier
        assert params is not None, "Server parameters must be valid"
        tools = transport.list_tools_sync(params)
        cfg = ServerConfig(name=name, parameters=params, tools=tools)

    # Ensure cfg is not None at this point
    assert cfg is not None, "ServerConfig must be created before saving"

    # Save the config
    store.save_server(cfg)
    return cfg
