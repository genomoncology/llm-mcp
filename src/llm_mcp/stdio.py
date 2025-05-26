"""
STDIO transport - synchronous wrapper around *stdio* MCP servers.
"""

from collections.abc import Mapping
from typing import Any

from mcp import types
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

from . import run_async, schema, utils

__all__ = [
    "call_tool_sync",
    "list_tools_sync",
]

# list_tools


async def list_tools(params: schema.StdioServerParameters) -> list[types.Tool]:
    async with (
        stdio_client(params) as (reader, writer),
        ClientSession(reader, writer) as session,
    ):
        await session.initialize()
        result: types.ListToolsResult = await session.list_tools()
        return result.tools


def list_tools_sync(params: schema.StdioServerParameters) -> list[types.Tool]:
    """Blocking helper - fetch tool metadata from *params*."""
    return run_async(list_tools(params))


# call_tool


async def call_tool(
    params: schema.StdioServerParameters,
    tool_name: str,
    arguments: Mapping[str, Any] | None = None,
) -> Any:
    async with (
        stdio_client(params) as (reader, writer),
        ClientSession(reader, writer) as session,
    ):
        await session.initialize()
        call: types.CallToolResult = await session.call_tool(
            tool_name, dict(arguments or {})
        )
        parts = [utils.convert_content(p) for p in call.content]
        return parts[0] if len(parts) == 1 else parts


def call_tool_sync(
    params: schema.StdioServerParameters,
    tool_name: str,
    arguments: Mapping[str, Any] | None = None,
) -> Any:
    """Blocking helper - call *tool_name* with *arguments*."""
    return run_async(call_tool(params, tool_name, arguments))
