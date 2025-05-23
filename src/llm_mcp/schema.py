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
        # Convert int seconds to timedelta
        data["timeout"] = timedelta(seconds=data["timeout"])
        data["sse_read_timeout"] = timedelta(seconds=data["sse_read_timeout"])
        return data


ServerParameters = RemoteServerParameters | StdioServerParameters


def parse_params(param_str: str) -> ServerParameters | None:
    """Convert a string param to either Http or Stdio ServerParameters."""
    param_str = param_str.strip()
    url_pattern = re.compile(r"https?://")

    if url_pattern.match(param_str):
        return RemoteServerParameters(url=param_str)

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


class Upstream(BaseModel):
    name: str
    parameters: ServerParameters


class Exposes(BaseModel):
    pass


class ConfigFile(BaseModel):
    version: int = Field(
        default=1,
        description="Version of the configuration file structure.",
    )
    upstreams: list[Upstream] = Field(
        default_factory=list,
        description="List of upstream model content protocol (MCP) servers.",
    )
    exposes: list[Exposes] = Field(
        default_factory=list,
        description="List of exposed tools from upstream MCP servers and "
        "other registered `llm` tools.",
    )
