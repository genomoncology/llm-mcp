from typing import Any

from pydantic import BaseModel, Field

from .parameters import ServerParameters


class ToolAnnotations(BaseModel):
    title: str | None = None
    readOnlyHint: bool | None = None
    destructiveHint: bool | None = None
    idempotentHint: bool | None = None
    openWorldHint: bool | None = None


class ServerTool(BaseModel):
    """Raw MCP tool definition"""

    name: str = Field(
        ...,
        description="Name of the tool per the upstream server.",
    )
    description: str | None = Field(
        default=None,
        description="Description of the tool per the upstream server.",
    )
    inputSchema: dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema for the tool's parameters",
    )
    annotations: ToolAnnotations | None = Field(
        default=None,
        description="Additional annotations provided by the server.",
    )


class ServerConfig(BaseModel):
    name: str = Field(..., description="Name of the server")
    parameters: ServerParameters = Field(
        ...,
        description="Parameters used to start or connect to the MCP server.",
    )
    tools: list[ServerTool] = Field(
        default_factory=list,
        description="List of tools provided by the server.",
    )
