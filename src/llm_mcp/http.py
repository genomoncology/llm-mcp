"""HTTP transport - synchronous wrapper streamable HTTP MCP servers."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from mcp import types
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from . import convert_content, run_async

__all__ = [
    "ServerParameters",
    "call_tool_sync",
    "list_tools_sync",
]


@dataclass(slots=True, frozen=True)
class ServerParameters:
    base_url: str
    headers: Mapping[str, str] | None = None
    timeout: timedelta | None = None
    sse_read_timeout: timedelta | None = None
    terminate_on_close: bool = True

    def to_client_args(self) -> tuple[Sequence[Any], Mapping[str, Any]]:
        pos: Sequence[Any] = (self.base_url,)
        kw: dict[str, Any] = {
            "headers": self.headers,
            "timeout": self.timeout or timedelta(seconds=30),
            "sse_read_timeout": self.sse_read_timeout or timedelta(minutes=5),
            "terminate_on_close": self.terminate_on_close,
        }
        return pos, kw


# list_tools


def list_tools_sync(params: ServerParameters) -> list[types.Tool]:
    return run_async(list_tools(params=params))


async def list_tools(params: ServerParameters) -> list[types.Tool]:
    pos, kw = params.to_client_args()

    async with (
        streamablehttp_client(*pos, **kw) as (reader, writer, _),
        ClientSession(reader, writer) as session,
    ):
        await session.initialize()
        result = await session.list_tools()
        return result.tools


# call_tool


def call_tool_sync(
    params: ServerParameters,
    tool_name: str,
    arguments: Mapping[str, Any] | None = None,
) -> Any:
    return run_async(call_tool(params, tool_name, arguments))


async def call_tool(
    params: ServerParameters,
    tool_name: str,
    arguments: Mapping[str, Any] | None = None,
) -> Any:
    pos, kw = params.to_client_args()
    arguments = dict(arguments or {})

    async with (
        streamablehttp_client(*pos, **kw) as (reader, writer, _),
        ClientSession(reader, writer) as session,
    ):
        await session.initialize()
        call = await session.call_tool(tool_name, arguments)
        parts = [convert_content(p) for p in call.content]
        return parts[0] if len(parts) == 1 else parts
