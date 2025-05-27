"""Convert MCP tools to LLM tools with transport-agnostic implementation."""

from typing import Any

from llm import Tool as LLMTool
from mcp import types as mcp_types

from .. import schema
from . import http, stdio


def convert_tool(
    server_config: schema.ServerConfig,
    mcp_tool: mcp_types.Tool,
) -> LLMTool:
    """
    Convert an MCP tool to an LLM tool with proper implementation.

    Args:
        server_config: The server configuration containing connection parameters
        mcp_tool: The MCP tool definition to convert

    Returns:
        An LLM Tool that can be registered and used
    """
    # Create the implementation function based on transport type
    if isinstance(server_config.parameters, schema.RemoteServerParameters):
        implementation = _create_http_implementation(
            server_config.parameters, mcp_tool.name
        )
    else:  # StdioServerParameters
        implementation = _create_stdio_implementation(
            server_config.parameters, mcp_tool.name
        )

    # Create and return the LLM tool
    return LLMTool(
        name=mcp_tool.name,
        description=mcp_tool.description or "",
        input_schema=mcp_tool.inputSchema or {},
        implementation=implementation,
        plugin="llm_mcp",
    )


def _create_http_implementation(
    params: schema.RemoteServerParameters,
    tool_name: str,
) -> Any:
    """Create an implementation function for HTTP-based MCP tools."""

    def impl(**kwargs: Any) -> Any:
        return http.call_tool_sync(params, tool_name, kwargs or {})

    # Set a meaningful name for debugging
    impl.__name__ = f"http_tool_{tool_name}"
    return impl


def _create_stdio_implementation(
    params: schema.StdioServerParameters,
    tool_name: str,
) -> Any:
    """Create an implementation function for stdio-based MCP tools."""

    def impl(**kwargs: Any) -> Any:
        return stdio.call_tool_sync(params, tool_name, kwargs or {})

    # Set a meaningful name for debugging
    impl.__name__ = f"stdio_tool_{tool_name}"
    return impl
