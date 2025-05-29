import shlex

from ..schema import (
    RemoteServerParameters,
    ServerParameters,
    StdioServerParameters,
)


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
    env_vars, cmd_parts = _parse_command_line(param_str)

    if not cmd_parts:
        return None

    return StdioServerParameters(
        command=cmd_parts[0],
        args=cmd_parts[1:] if len(cmd_parts) > 1 else [],
        env=env_vars or None,
    )


# private functions


def _parse_command_line(line: str) -> tuple[dict[str, str], list[str]]:
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
        # Exclude both short flags (-f=val) and long flags (--format=json)
        if (
            "=" in token
            and not token.startswith("-")
            and not token.startswith("--")
        ):
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
