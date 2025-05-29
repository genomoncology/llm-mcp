"""Filesystem persistence for MCP server configurations and toolboxes."""

import json
from pathlib import Path

import llm

from llm_mcp.schema import ServerConfig, ToolboxConfig


def mcp_dir() -> Path:
    """Get the mcp home directory."""
    user_dir: Path = llm.user_dir()
    mcp_dir_path: Path = user_dir / "mcp"
    mcp_dir_path.mkdir(parents=True, exist_ok=True)
    return mcp_dir_path


def mcp_servers_dir() -> Path:
    """Get the directory where server manifests are stored."""
    servers = mcp_dir() / "servers"
    servers.mkdir(parents=True, exist_ok=True)
    return servers


def get_server_path(name: str) -> Path:
    return mcp_servers_dir() / f"{name}.json"


def save_server(config: ServerConfig) -> Path:
    """Save a server configuration to disk."""
    # remove any invalid tool input schema or annotations
    config.clean()

    # generate json string
    as_data = config.model_dump(
        exclude_none=True,
        exclude_unset=True,
        exclude_defaults=True,
    )
    as_json = json.dumps(as_data, indent=2)

    # write to file and return path
    target_path = mcp_servers_dir() / f"{config.name}.json"
    target_path.write_text(as_json)
    return target_path


def load_server(name: str) -> ServerConfig | None:
    """Load a server configuration from disk."""
    path = mcp_servers_dir() / f"{name}.json"
    server_config = None
    if path.is_file():
        server_config = ServerConfig.model_validate_json(path.read_text())
        server_config.clean()
    return server_config


def remove_server(name: str) -> bool:
    """Load a server configuration from disk."""
    path = mcp_servers_dir() / f"{name}.json"

    try:
        path.unlink()
        success = True
    except FileNotFoundError:
        success = False

    return success


def list_servers() -> list[str]:
    """List all available server names."""
    return [p.stem for p in mcp_servers_dir().glob("*.json")]


def toolboxes_dir() -> Path:
    """Get the directory where toolbox configs are stored."""
    path = mcp_dir() / "toolboxes"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _toolbox_path(name: str) -> Path:
    return toolboxes_dir() / f"{name}.json"


def save_toolbox(config: ToolboxConfig) -> Path:
    """Save a toolbox configuration to disk."""
    path = _toolbox_path(config.name)
    # `exclude_unset` drops the discriminator when only default fields
    # are set, so we must NOT use it here.
    cfg_json = config.model_dump_json(
        indent=2,
        exclude_none=True,
        exclude_defaults=False,  # keep "kind"
        by_alias=True,
    )
    path.write_text(cfg_json)
    return path


def load_toolbox(name: str) -> ToolboxConfig | None:
    """Load a toolbox configuration from disk."""
    path = _toolbox_path(name)
    if not path.exists():
        return None
    return ToolboxConfig.model_validate_json(path.read_text())


def remove_toolbox(name: str) -> bool:
    """Remove a toolbox configuration from disk."""
    try:
        _toolbox_path(name).unlink()
    except FileNotFoundError:
        return False
    else:
        return True


def list_toolboxes() -> list[str]:
    """List all available toolbox names."""
    return [p.stem for p in toolboxes_dir().glob("*.json")]


def get_default_toolbox() -> str | None:
    """Get the name of the default toolbox."""
    settings_file = mcp_dir() / "settings.json"
    if settings_file.exists():
        settings = json.loads(settings_file.read_text())
        default = settings.get("default_toolbox")
        # Explicitly cast to ensure we return the right type
        return str(default) if default is not None else None
    return None


def set_default_toolbox(name: str | None):
    """Set or clear the default toolbox."""
    settings_file = mcp_dir() / "settings.json"
    settings = {}
    if settings_file.exists():
        settings = json.loads(settings_file.read_text())

    if name:
        settings["default_toolbox"] = name
    else:
        settings.pop("default_toolbox", None)

    settings_file.write_text(json.dumps(settings, indent=2))
