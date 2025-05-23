"""
Wrap MCP Servers into `llm` Tool objects.
"""

from collections.abc import Callable, Mapping
from itertools import chain
from typing import Any

from llm.models import Tool as LLMTool
from mcp import types

from . import http, schema, stdio

__all__ = ["wrap_http", "wrap_mcp", "wrap_stdio"]


def wrap_mcp(*params: str | schema.ServerParameters) -> list[LLMTool]:
    """
    Wrap tools from stdio commands or HTTP URLs into flat list of llm.Tools.
    """
    stdio_params: list[schema.StdioServerParameters] = []
    http_params: list[schema.RemoteServerParameters] = []

    for param_input in params:
        if isinstance(param_input, str):
            param_output = schema.parse_params(param_input)
        else:
            param_output = param_input

        if isinstance(param_output, schema.RemoteServerParameters):
            http_params.append(param_output)
        elif isinstance(param_output, schema.StdioServerParameters):
            stdio_params.append(param_output)
        else:
            pass  # todo: logging of invalid parameter strings.

    return wrap_http(*http_params) + wrap_stdio(*stdio_params)


def wrap_stdio(*params: schema.StdioServerParameters) -> list[LLMTool]:
    """Wrap tools exposed by stdio MCP servers as `llm.Tool` objects."""
    return _do_wrap_tools(stdio.list_tools_sync, stdio.call_tool_sync, *params)


def wrap_http(*params: schema.RemoteServerParameters) -> list[LLMTool]:
    """Wrap tools exposed by HTTP MCP servers as `llm.Tool` objects."""
    return _do_wrap_tools(http.list_tools_sync, http.call_tool_sync, *params)


# private functions


def _do_wrap_tools(
    list_tools_sync: Callable[[Any], list[types.Tool]],
    call_tool_sync: Callable[[Any, str, Mapping[str, Any]], Any],
    *params: Any,
) -> list[LLMTool]:
    """Generic wrapper for fetching tools from MCP servers."""
    return list(
        chain.from_iterable(
            _mk_llm_tools(
                list_tools_sync(param),
                caller=lambda name, args, param=param: call_tool_sync(  # type: ignore[misc]
                    param, name, args or {}
                ),
            )
            for param in params
        )
    )


def _mk_llm_tools(
    tool_meta: list[types.Tool],
    *,
    caller: Callable[[str, Mapping[str, Any]], Any],
) -> list[LLMTool]:
    tools: list[LLMTool] = []

    for tool in tool_meta:

        def make_impl(name: str) -> Callable[..., Any]:
            def impl(**kwargs: Any) -> Any:
                return caller(name, kwargs)

            return impl

        input_schema = tool.inputSchema or {}

        # OpenAI rejects {"type": "object"}  → treat as argument-less
        if input_schema.get("type") == "object" and not input_schema.get(
            "properties"
        ):
            input_schema = {}

        tools.append(
            LLMTool(
                name=tool.name,
                description=tool.description or "",
                input_schema=input_schema,
                implementation=make_impl(tool.name),
            )
        )

    return tools
