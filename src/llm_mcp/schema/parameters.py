"""Pydantic schemas for MCP server parameters."""

from datetime import timedelta
from typing import Any
from urllib.parse import urlparse

from mcp.client.stdio import StdioServerParameters as _StdioServerParameters
from pydantic import BaseModel, Field, field_validator


class RemoteServerParameters(BaseModel):
    url: str = Field(..., description="URL of remote MCP server.")
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Default headers to be provided to MCP server.",
    )
    timeout: int = Field(
        default=30,
        description="Standard HTTP operation timeout in seconds",
        ge=1,
        le=3600,
    )
    sse_read_timeout: int = Field(
        default=5 * 60,
        description="How long client will wait in seconds for new event.",
        ge=1,
        le=3600,
    )
    terminate_on_close: bool = Field(
        default=True,
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        try:
            result = urlparse(v)
            cls._validate_url_parts(result)
        except Exception as e:
            raise ValueError(f"Invalid URL: {e}") from e
        return v

    @staticmethod
    def _validate_url_parts(result) -> None:
        """Validate URL components."""
        if not all([result.scheme, result.netloc]):
            raise ValueError("Invalid URL format")
        if result.scheme not in ("http", "https"):
            raise ValueError("URL must use http or https scheme")

    def as_kwargs(self) -> dict[str, Any]:
        data = self.model_dump(mode="python", exclude={"url"})
        data["timeout"] = timedelta(seconds=data["timeout"])
        data["sse_read_timeout"] = timedelta(seconds=data["sse_read_timeout"])
        return data


class StdioServerParameters(_StdioServerParameters):
    """Extended StdioServerParameters with additional validation."""

    @field_validator("command")
    @classmethod
    def validate_command(cls, v: str) -> str:
        """Basic command validation."""
        if not v or not v.strip():
            raise ValueError("Command cannot be empty")
        return v


ServerParameters = RemoteServerParameters | StdioServerParameters
