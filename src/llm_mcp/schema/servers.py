from mcp.types import Tool as MCPTool
from pydantic import BaseModel, Field

from .parameters import ServerParameters


class ServerConfig(BaseModel):
    name: str = Field(
        ...,
        description="Name of the server which maps to server file name.",
        pattern="^[a-z0-9_]+$",
    )
    parameters: ServerParameters = Field(
        ...,
        description="Parameters used to start or connect to the MCP server.",
    )
    tools: list[MCPTool] = Field(
        default_factory=list,
        description="List of tools provided by the server.",
    )

    def get_tool(self, name: str) -> MCPTool:
        for tool in self.tools:
            if tool.name == name:
                return tool
        raise ValueError(f"Tool {name!r} not found in server {self.name!r}")

    def clean(self):
        for tool in self.tools:
            # set inputSchema to {} if not properties
            schema_type = tool.inputSchema.get("type")
            schema_properties = tool.inputSchema.get("properties")
            if schema_type == "object" and not schema_properties:
                tool.inputSchema = {}

            # clear all extras
            if tool.annotations and tool.annotations.model_extra:
                tool.annotations.model_extra.clear()
