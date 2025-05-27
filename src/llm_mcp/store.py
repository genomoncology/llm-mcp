"""Filesystem persistence for MCP server configurations."""

import json
from pathlib import Path

import llm

from llm_mcp.schema import ServerConfig


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


def list_servers() -> list[str]:
    """List all available server names."""
    return [p.stem for p in mcp_servers_dir().glob("*.json")]
