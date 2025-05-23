"""HTTP transport - synchronous wrapper streamable HTTP MCP servers."""

from collections.abc import Mapping
from typing import Any

from mcp import types
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from . import convert_content, run_async, schema

__all__ = [
    "call_tool_sync",
    "list_tools_sync",
]


# list_tools


def list_tools_sync(
    params: schema.RemoteServerParameters,
) -> list[types.Tool]:
    return run_async(list_tools(params=params))


async def list_tools(
    params: schema.RemoteServerParameters,
) -> list[types.Tool]:
    kw = params.as_kwargs()
    async with (
        streamablehttp_client(params.url, **kw) as (reader, writer, _),
        ClientSession(reader, writer) as session,
    ):
        await session.initialize()
        result = await session.list_tools()
        return result.tools


# call_tool


def call_tool_sync(
    params: schema.RemoteServerParameters,
    tool_name: str,
    arguments: Mapping[str, Any] | None = None,
) -> Any:
    return run_async(call_tool(params, tool_name, arguments))


async def call_tool(
    params: schema.RemoteServerParameters,
    tool_name: str,
    arguments: Mapping[str, Any] | None = None,
) -> Any:
    arguments = dict(arguments or {})

    kw = params.as_kwargs()
    async with (
        streamablehttp_client(params.url, **kw) as (reader, writer, _),
        ClientSession(reader, writer) as session,
    ):
        await session.initialize()
        call = await session.call_tool(tool_name, arguments)
        parts = [convert_content(p) for p in call.content]
        return parts[0] if len(parts) == 1 else parts
