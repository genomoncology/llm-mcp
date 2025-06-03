import re
from pathlib import Path
from urllib.parse import urlparse

from ..schema import (
    RemoteServerParameters,
    ServerParameters,
    StdioServerParameters,
)


def generate_server_name(params: ServerParameters) -> str:
    """Generate a unique, user-friendly name for a server.

    Examples:
        - npx @modelcontextprotocol/server-filesystem -> "filesystem"
        - uvx mcp-server-sqlite --db-path test.db -> "sqlite_test"
        - https://api.example.com/mcp -> "example_api"
        - java -jar weather-server.jar -> "weather_server"
    """
    if isinstance(params, RemoteServerParameters):
        return _generate_remote_server_name(params)
    else:
        return _generate_stdio_server_name(params)


# private functions


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

        # For subdomains like api.example, format as example_api
        if len(parts) >= 2 and parts[0] not in ("www", "app", "localhost"):
            # Reverse subdomain and domain for better readability
            main_domain = parts[-1]
            subdomain = parts[0]
            host = f"{main_domain}_{subdomain}"
        else:
            # Just use the main part
            host = parts[-1] if parts else host

    # Add path context if meaningful
    path_parts = [p for p in parsed.path.strip("/").split("/") if p]
    if path_parts and path_parts[-1] not in ("mcp", "sse", "api"):
        return to_snake_case(f"{host}_{path_parts[-1]}")

    # Add port if non-standard
    if parsed.port and parsed.port not in (80, 443):
        return to_snake_case(f"{host}_{parsed.port}")

    return to_snake_case(host)


def _extract_npx_name(args: list[str]) -> str:
    """Return a readable, vendor-agnostic name for an **npx** package."""

    # Skip the auto-approve flag `-y` if present
    pkg = args[0] if args[0] != "-y" else (args[1] if len(args) > 1 else "")

    # Remove a trailing version suffix  (e.g. "@latest", "@1.2.3")
    if "@" in pkg[1:]:
        pkg, _ = pkg.rsplit("@", 1)

    # ── Scoped packages ────────────────────────────────────────────────────
    if pkg.startswith("@"):
        scope, _, raw_name = pkg[1:].partition("/")  # "@scope/name"
        raw_name = raw_name or scope  # handle "@foo"

        clean_name = (
            raw_name.replace("server-", "").replace("mcp-", "")
        ) or "mcp"

        # Heuristic: prepend the scope **only** when the name is a single
        # short token - this avoids “wonderwhy_er_desktop_commander” while
        # still giving us “playwright_mcp”.
        include_scope = "_" not in clean_name and len(clean_name) <= 5
        if include_scope:
            return to_snake_case(f"{scope}_{clean_name}")
        return to_snake_case(clean_name)

    # ── Un-scoped packages ────────────────────────────────────────────────
    return to_snake_case(pkg.replace("server-", "").replace("mcp-", ""))


def _extract_uvx_name(args: list[str]) -> str:
    """Extract name from uvx command."""
    name = args[0].replace("mcp-server-", "").replace("mcp-", "")

    # Add context from key arguments
    for i, arg in enumerate(args):
        if arg in ("--db-path", "--database") and i + 1 < len(args):
            db_name = Path(args[i + 1]).stem
            return to_snake_case(f"{name}_{db_name}")

    return to_snake_case(name)


def _extract_java_name(args: list[str]) -> str | None:
    """Extract name from java -jar command."""
    if "-jar" in args:
        jar_idx = args.index("-jar")
        if jar_idx + 1 < len(args):
            jar_name = Path(args[jar_idx + 1]).stem
            cleaned = jar_name.replace("-server", "").replace("_server", "")
            return to_snake_case(cleaned)
    return None


def _extract_docker_name(args: list[str]) -> str | None:
    """Extract name from docker run command."""
    if "run" in args:
        for arg in args:
            if not arg.startswith("-") and arg != "run":
                name = arg.split("/")[-1].replace("mcp-", "")
                return to_snake_case(name)
    return None


def _extract_script_name(command: str, args: list[str]) -> str | None:
    """Extract name from script commands (python, node, etc)."""
    if command in ("python", "python3", "node"):
        for arg in args:
            if arg.endswith((".py", ".js")) and not arg.startswith("-"):
                return to_snake_case(Path(arg).stem)
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
    return to_snake_case(Path(command).stem)


def to_snake_case(text: str) -> str:
    """Convert text to snake_case."""
    # Strip any stray '@' (shouldn't exist, but keeps the helper generic)
    text = text.replace("@", "")
    # Replace hyphens and spaces with underscores
    text = text.replace("-", "_").replace(" ", "_")
    # Handle camelCase and PascalCase
    text = re.sub("([a-z0-9])([A-Z])", r"\1_\2", text)
    # Clean up multiple underscores and convert to lowercase
    text = re.sub("_+", "_", text).lower()
    # Remove leading/trailing underscores
    return text.strip("_")
