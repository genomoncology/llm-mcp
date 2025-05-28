from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolboxTool(BaseModel):
    """A tool reference within a toolbox."""

    # Source identification
    source_type: Literal["mcp", "function", "toolbox_class"] = Field(
        ..., description="Type of tool source"
    )

    # For MCP tools: "server_name/tool_name" format
    mcp_ref: str | None = Field(
        None,
        description="MCP tool reference as 'server_name/tool_name'",
        pattern="^[a-z0-9_]+/[a-zA-Z0-9_]+$",
    )

    # For Python functions/classes
    code: str | None = Field(
        None, description="Python code (inline or file path)"
    )
    function_name: str | None = Field(
        None, description="Function/class name to extract from code"
    )

    # Optional overrides
    name: str | None = Field(
        None, description="Override tool name", pattern="^[a-zA-Z0-9_]+$"
    )
    description: str | None = Field(
        None, description="Override tool description"
    )

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


class ToolboxConfig(BaseModel):
    """Configuration for a custom toolbox."""

    name: str = Field(
        ...,
        description="Toolbox name",
        pattern="^[A-Z][a-zA-Z0-9_]*$",  # Capital first letter for Toolbox convention
    )
    description: str | None = Field(None, description="Toolbox description")
    tools: list[ToolboxTool] = Field(
        default_factory=list, description="Tools included in this toolbox"
    )
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration passed to toolbox __init__",
    )
