"""Utilities for handling MCP references."""

import re


def parse_mcp_reference(mcp_ref: str) -> tuple[str, str]:
    """Parse an MCP reference into server and tool names.

    The mcp_ref should follow the pattern: ^[a-z0-9_-]+/[a-zA-Z0-9_-]+$
    - Server name: lowercase letters, numbers, underscores, and hyphens
    - Tool name: letters (any case), numbers, underscores, and hyphens

    Args:
        mcp_ref: The MCP reference string in the format 'server_name/tool_name'

    Returns:
        A tuple containing (server_name, tool_name)

    Raises:
        ValueError: If the reference format is invalid
    """
    # This pattern should match the one defined in schema/toolboxes.py
    pattern = r"^([a-z0-9_-]+)/([a-zA-Z0-9_-]+)$"
    match = re.match(pattern, mcp_ref)

    if not match:
        raise ValueError(
            f"Invalid MCP reference: {mcp_ref}. Expected format: server_name/tool_name\n"
            "Server name can contain lowercase letters, numbers, underscores, and hyphens.\n"
            "Tool name can contain letters (any case), numbers, underscores, and hyphens."
        )

    return match.group(1), match.group(2)
