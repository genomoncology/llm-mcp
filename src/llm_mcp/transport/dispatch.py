"""Business logic for managing MCP servers."""

from ..schema import (
    MCPTool,
    RemoteServerParameters,
    ServerParameters,
)
from . import http, run_async, stdio


async def list_tools(params: ServerParameters) -> list[MCPTool]:
    """Return the remote tool list for *params* (blocking)."""
    tools: list[MCPTool]

    if isinstance(params, RemoteServerParameters):
        tools = await http.list_tools(params)
    else:
        tools = await stdio.list_tools(params)

    return tools


def list_tools_sync(params: ServerParameters) -> list[MCPTool]:
    return run_async(list_tools(params=params))
