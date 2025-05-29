# ruff: noqa: I001
from .parameters import (
    ServerParameters,
    StdioServerParameters,
    RemoteServerParameters,
)
from .servers import (
    ServerConfig,
    MCPTool,
)
from .toolboxes import (
    ToolboxConfig,
    ToolRef,
    MCPToolRef,
    PythonToolRef,
    ToolboxMethodRef,
)

# Temporary compatibility layer for code that still imports ToolboxTool
# This will be removed in a later task when all code is migrated
from pydantic import BaseModel, Field
from typing import Literal


class ToolboxTool(BaseModel):
    """Temporary compatibility class for old toolbox tool references."""

    source_type: Literal["mcp", "function", "toolbox_class"] = Field(
        ..., description="Type of tool source"
    )
    mcp_ref: str | None = None
    code: str | None = None
    function_name: str | None = None
    name: str | None = None
    description: str | None = None

    @property
    def server_name(self) -> str | None:
        """Extract server name from mcp_ref."""
        if self.mcp_ref:
            return self.mcp_ref.split("/")[0]
        return None

    @property
    def tool_name(self) -> str | None:
        """Extract tool name from mcp_ref."""
        if self.mcp_ref:
            return self.mcp_ref.split("/")[1]
        return None


__all__ = [
    "MCPTool",
    "MCPToolRef",
    "PythonToolRef",
    "RemoteServerParameters",
    "ServerConfig",
    "ServerParameters",
    "StdioServerParameters",
    "ToolRef",
    "ToolboxConfig",
    "ToolboxMethodRef",
    "ToolboxTool",  # For backward compatibility
]
