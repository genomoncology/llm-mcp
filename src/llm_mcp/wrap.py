"""
Simpler module-based wrap.py - sync only, but cleaner design.
"""

from types import ModuleType
from typing import Any

from llm.models import Tool as LLMTool
from mcp import types

from . import http, schema, stdio, utils

__all__ = ["wrap_mcp"]


def wrap_mcp(*params: str | schema.ServerParameters) -> list[LLMTool]:
    llm_tools = []

    for param in params:
        llm_tools.extend(server_to_llm_tools(param))

    return llm_tools


def server_to_llm_tools(
    in_param: str | schema.ServerParameters,
) -> list[LLMTool]:
    """
    Expects the module to have:
    - list_tools_sync(params) -> list[types.Tool]
    - call_tool_sync(params, tool_name, arguments) -> Any
    """
    param: schema.ServerParameters | None
    if isinstance(in_param, str):
        param = utils.parse_params(in_param)
        if param is None:
            return []
    else:
        param = in_param

    transport = _TRANSPORT[type(param)]
    key = (_key(param), transport)

    if key not in _CACHE:
        _CACHE[key] = [
            _construct_tool(meta, param, transport)
            for meta in transport.list_tools_sync(param)
        ]

    # return a shallow copy (small cost, no surprises)
    return list(_CACHE[key])


# private functions

_TRANSPORT: dict[type[schema.ServerParameters], ModuleType] = {
    schema.RemoteServerParameters: http,
    schema.StdioServerParameters: stdio,
}

_CACHE: dict[tuple[str, ModuleType], list[LLMTool]] = {}


def _key(p: schema.ServerParameters) -> str:
    return p.model_dump_json(
        exclude_defaults=True,
        exclude_unset=True,
        exclude_none=True,
    )


def _construct_tool(
    mcp_tool: types.Tool,
    params: schema.ServerParameters,
    transport: ModuleType,
) -> LLMTool:
    def tool_impl(**kw: Any) -> Any:
        return transport.call_tool_sync(params, mcp_tool.name, kw or {})

    schema_in = mcp_tool.inputSchema or {}
    if schema_in.get("type") == "object" and not schema_in.get("properties"):
        schema_in = {}

    return LLMTool(
        name=mcp_tool.name,
        description=mcp_tool.description or "",
        input_schema=schema_in,
        implementation=tool_impl,
    )
