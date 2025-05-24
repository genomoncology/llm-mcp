"""Pydantic schemas for MCP server parameters."""

import shlex
from datetime import timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from mcp.client.stdio import StdioServerParameters as _StdioServerParameters
from pydantic import BaseModel, Field, field_validator


class RemoteServerParameters(BaseModel):
    url: str = Field(..., description="URL of remote MCP server.")
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Default headers to be provided to MCP server.",
    )
    timeout: int = Field(
        default=30,
        description="Standard HTTP operation timeout in seconds",
        ge=1,
        le=3600,
    )
    sse_read_timeout: int = Field(
        default=5 * 60,
        description="How long client will wait in seconds for new event.",
        ge=1,
        le=3600,
    )
    terminate_on_close: bool = Field(
        default=True,
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        try:
            result = urlparse(v)
            cls._validate_url_parts(result)
        except Exception as e:
            raise ValueError(f"Invalid URL: {e}") from e
        return v

    @staticmethod
    def _validate_url_parts(result) -> None:
        """Validate URL components."""
        if not all([result.scheme, result.netloc]):
            raise ValueError("Invalid URL format")
        if result.scheme not in ("http", "https"):
            raise ValueError("URL must use http or https scheme")

    def as_kwargs(self) -> dict[str, Any]:
        data = self.model_dump(mode="python", exclude={"url"})
        data["timeout"] = timedelta(seconds=data["timeout"])
        data["sse_read_timeout"] = timedelta(seconds=data["sse_read_timeout"])
        return data


class StdioServerParameters(_StdioServerParameters):
    """Extended StdioServerParameters with additional validation."""

    @field_validator("command")
    @classmethod
    def validate_command(cls, v: str) -> str:
        """Basic command validation."""
        if not v or not v.strip():
            raise ValueError("Command cannot be empty")
        return v


ServerParameters = RemoteServerParameters | StdioServerParameters


def parse_command_line(line: str) -> tuple[dict[str, str], list[str]]:
    """Parse a command line, extracting environment variables and command parts.

    Handles various formats:
    - ENV=val command args
    - command args ENV=val
    - command "arg with spaces"
    """
    env_vars = {}
    parts = []

    # Use shlex for proper quote handling
    try:
        tokens = shlex.split(line)
    except ValueError:
        # Fallback for malformed quotes
        tokens = line.split()

    # First pass: separate env vars from command parts
    i = 0
    while i < len(tokens):
        token = tokens[i]

        # Check if this looks like an env var (KEY=VALUE pattern)
        if "=" in token and not token.startswith("-"):
            # But only treat as env var if key looks valid
            key, val = token.split("=", 1)
            if key and key.replace("_", "").isalnum():
                env_vars[key] = val
                i += 1
                continue

        # Everything else is part of the command
        parts.extend(tokens[i:])
        break

    return env_vars, parts


def parse_params(param_str: str) -> ServerParameters | None:
    """Convert a string param to either Http or Stdio ServerParameters.

    Examples:
        >>> parse_params("https://example.com/api")
        RemoteServerParameters(url='https://example.com/api', ...)

        >>> parse_params("npx -y @modelcontextprotocol/server-filesystem /path")
        StdioServerParameters(command='npx', args=['-y', '@modelcontextprotocol/server-filesystem', '/path'])

        >>> parse_params("API_KEY=123 uvx mcp-server")
        StdioServerParameters(command='uvx', args=['mcp-server'], env={'API_KEY': '123'})
    """
    param_str = param_str.strip()

    if not param_str:
        return None

    # Check if it's a URL
    if param_str.startswith(("http://", "https://")):
        # Extract headers if present (simple format: url --header Key=Value)
        parts = param_str.split()
        url = parts[0]
        headers = {}

        i = 1
        while i < len(parts):
            if parts[i] == "--header" and i + 1 < len(parts):
                key_val = parts[i + 1]
                if "=" in key_val:
                    key, val = key_val.split("=", 1)
                    headers[key] = val
                i += 2
            else:
                i += 1

        return RemoteServerParameters(url=url, headers=headers or {})

    # Parse as stdio command
    env_vars, cmd_parts = parse_command_line(param_str)

    if not cmd_parts:
        return None

    return StdioServerParameters(
        command=cmd_parts[0],
        args=cmd_parts[1:] if len(cmd_parts) > 1 else [],
        env=env_vars or None,
    )


def _generate_remote_server_name(params: RemoteServerParameters) -> str:
    """Generate name for remote server."""
    parsed = urlparse(params.url)
    host = parsed.hostname or "remote"

    # Handle subdomains
    parts = host.split(".")
    if len(parts) >= 2:
        # Remove common TLDs and 'www'
        if parts[-1] in ("com", "org", "net", "io", "dev", "ai"):
            parts = parts[:-1]
        if parts[0] == "www":
            parts = parts[1:]

        # For subdomains like api.example, format as example-api
        if len(parts) >= 2 and parts[0] not in ("www", "app", "localhost"):
            # Reverse subdomain and domain for better readability
            main_domain = parts[-1]
            subdomain = parts[0]
            host = f"{main_domain}-{subdomain}"
        else:
            # Just use the main part
            host = parts[-1] if parts else host

    # Add path context if meaningful
    path_parts = [p for p in parsed.path.strip("/").split("/") if p]
    if path_parts and path_parts[-1] not in ("mcp", "sse", "api"):
        return f"{host}-{path_parts[-1]}"

    # Add port if non-standard
    if parsed.port and parsed.port not in (80, 443):
        return f"{host}-{parsed.port}"

    return host


def _extract_npx_name(args: list[str]) -> str:
    """Extract name from npx command."""
    pkg = args[0] if args[0] != "-y" else (args[1] if len(args) > 1 else "")
    if pkg.startswith("@"):
        # @modelcontextprotocol/server-filesystem -> filesystem
        name = pkg.split("/")[-1].replace("server-", "").replace("mcp-", "")
        return name
    return pkg


def _extract_uvx_name(args: list[str]) -> str:
    """Extract name from uvx command."""
    name = args[0].replace("mcp-server-", "").replace("mcp-", "")

    # Add context from key arguments
    for i, arg in enumerate(args):
        if arg in ("--db-path", "--database") and i + 1 < len(args):
            db_name = Path(args[i + 1]).stem
            return f"{name}-{db_name}"

    return name


def _extract_java_name(args: list[str]) -> str | None:
    """Extract name from java -jar command."""
    if "-jar" in args:
        jar_idx = args.index("-jar")
        if jar_idx + 1 < len(args):
            jar_name = Path(args[jar_idx + 1]).stem
            return jar_name.replace("-server", "").replace("_server", "")
    return None


def _extract_docker_name(args: list[str]) -> str | None:
    """Extract name from docker run command."""
    if "run" in args:
        for arg in args:
            if not arg.startswith("-") and arg != "run":
                return arg.split("/")[-1].replace("mcp-", "")
    return None


def _extract_script_name(command: str, args: list[str]) -> str | None:
    """Extract name from script commands (python, node, etc)."""
    if command in ("python", "python3", "node"):
        for arg in args:
            if arg.endswith((".py", ".js")) and not arg.startswith("-"):
                return Path(arg).stem
    return None


def _generate_stdio_server_name(params: StdioServerParameters) -> str:
    """Generate name for stdio server."""
    command = params.command
    args = params.args or []

    # Try various extraction methods
    if command == "npx" and args:
        return _extract_npx_name(args)

    if command == "uvx" and args:
        return _extract_uvx_name(args)

    java_name = _extract_java_name(args)
    if java_name:
        return java_name

    docker_name = _extract_docker_name(args)
    if docker_name:
        return docker_name

    script_name = _extract_script_name(command, args)
    if script_name:
        return script_name

    # Fallback: use command name
    return Path(command).stem


def generate_server_name(params: ServerParameters) -> str:
    """Generate a unique, user-friendly name for a server.

    Examples:
        - npx @modelcontextprotocol/server-filesystem -> "filesystem"
        - uvx mcp-server-sqlite --db-path test.db -> "sqlite-test"
        - https://api.example.com/mcp -> "example-api"
        - java -jar weather-server.jar -> "weather-server"
    """
    if isinstance(params, RemoteServerParameters):
        return _generate_remote_server_name(params)
    else:
        return _generate_stdio_server_name(params)


def ensure_unique_name(base_name: str, existing_names: set[str]) -> str:
    """Ensure the generated name is unique by appending a number if needed."""
    if base_name not in existing_names:
        return base_name

    counter = 2
    while f"{base_name}-{counter}" in existing_names:
        counter += 1

    return f"{base_name}-{counter}"
