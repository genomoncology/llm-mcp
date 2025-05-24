"""Pydantic schemas (instead of the obviously troublesome name 'models')."""

import re
import shlex
from datetime import timedelta
from typing import Any

from mcp.client.stdio import StdioServerParameters
from pydantic import BaseModel, Field


class RemoteServerParameters(BaseModel):
    url: str = Field(..., description="URL of remote MCP server.")
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Default headers to be provided to MCP server.",
    )
    timeout: int = Field(
        default=30,
        description="Standard HTTP operation timeout in seconds",
    )
    sse_read_timeout: int = Field(
        default=5 * 60,
        description="How long client will wait in seconds for new event.",
    )
    terminate_on_close: bool = Field(
        default=True,
    )

    def as_kwargs(self) -> dict[str, Any]:
        data = self.model_dump(mode="python", exclude={"url"})
        data["timeout"] = timedelta(seconds=data["timeout"])
        data["sse_read_timeout"] = timedelta(seconds=data["sse_read_timeout"])
        return data


ServerParameters = RemoteServerParameters | StdioServerParameters


class ServerConfig(BaseModel):
    name: str
    parameters: ServerParameters


class ToolConfig(BaseModel):
    mcp_server: str = Field(
        ..., description="Name of the upstream MCP server that contains tool."
    )
    mcp_tool: str = Field(
        ..., description="Name tool is known as by the upstream MCP server."
    )
    tool_name: str = Field(
        ..., description="Name by tool is referred to with `llm` ecosystem."
    )
    groups: list[str] = Field(
        default_factory=list,
        description="List of groups that tool is a member of.",
    )
    default_group: bool = Field(
        default=True, description="Whether tool is active by default."
    )

    def is_group(self, group_name: str | None = None) -> bool:
        """
        Determine if this tool belongs to the specified group.

        Args:
            group_name: The group to check membership for, or None for default group

        Returns:
            True if the tool belongs to the specified group
        """
        if group_name is None:
            # For default group, use the default_group flag
            # If the tool doesn't have a default_group property or it's set to True, include it
            return self.default_group
        else:
            # For explicit groups, check membership in the groups list
            return group_name in self.groups


class ConfigFile(BaseModel):
    version: int = Field(
        default=1,
        description="Version of the configuration file structure.",
    )
    servers: list[ServerConfig] = Field(
        default_factory=list,
        description="List of upstream model content protocol (MCP) servers.",
    )
    tools: list[ToolConfig] = Field(
        default_factory=list,
        description="List of exposed tools from upstream MCP servers and "
        "other registered `llm` tools.",
    )

    def get_tools(self, group_name: str | None = None) -> list[ToolConfig]:
        return list(filter(lambda t: t.is_group(group_name), self.tools))

    def get_server(self, server_name: str) -> ServerConfig | None:
        keep: ServerConfig | None = None
        for server in self.servers:
            if server.name == server_name:
                keep = server
                break
        return keep


def parse_params(param_str: str) -> ServerParameters | None:
    """Convert a string param to either Http or Stdio ServerParameters."""
    param_str = param_str.strip()

    # attempt to parse remote parameters

    url_pattern = re.compile(r"https?://")
    if url_pattern.match(param_str):
        return RemoteServerParameters(url=param_str)

    # assumes and returns non-remote as stdio parameters

    env_vars = {}
    parts = shlex.split(param_str)
    cmd_parts: list[str] = []

    for part in parts:
        if "=" in part and not cmd_parts:
            key, val = part.split("=", 1)
            env_vars[key] = val
        else:
            cmd_parts.append(part)

    return (
        StdioServerParameters(
            command=cmd_parts[0],
            args=cmd_parts[1:],
            env=env_vars or None,
        )
        if cmd_parts
        else None
    )
