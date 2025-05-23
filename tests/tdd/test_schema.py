from datetime import timedelta

import pytest

from llm_mcp.schema import (
    ConfigFile,
    RemoteServerParameters,
    StdioServerParameters,
    Upstream,
    parse_params,
)


def test_defaults():
    config = ConfigFile(
        upstreams=[
            Upstream(
                name="gitmcp_simonw_llm",
                parameters=parse_params("https://gitmcp.io/simonw/llm"),
            ),
            Upstream(
                name="desktop_commander",
                parameters=parse_params(
                    "npx -y @wonderwhy-er/desktop-commander"
                ),
            ),
        ],
    )

    # Validate

    assert config.model_dump() == {
        "version": 1,
        "upstreams": [
            {
                "name": "gitmcp_simonw_llm",
                "parameters": {
                    "headers": {},
                    "sse_read_timeout": 300,
                    "terminate_on_close": True,
                    "timeout": 30,
                    "url": "https://gitmcp.io/simonw/llm",
                },
            },
            {
                "name": "desktop_commander",
                "parameters": {
                    "args": ["-y", "@wonderwhy-er/desktop-commander"],
                    "command": "npx",
                    "cwd": None,
                    "encoding": "utf-8",
                    "encoding_error_handler": "strict",
                    "env": None,
                },
            },
        ],
        "exposes": [],
    }


def test_as_kwargs_timedelta_conversion():
    params = RemoteServerParameters(url="https://example.com")
    kwargs = params.as_kwargs()

    assert kwargs == {
        "headers": {},
        "timeout": timedelta(seconds=30),
        "sse_read_timeout": timedelta(seconds=300),
        "terminate_on_close": True,
    }

    # Verify they are actual timedelta objects
    assert isinstance(kwargs["timeout"], timedelta)
    assert isinstance(kwargs["sse_read_timeout"], timedelta)


@pytest.mark.parametrize(
    "param, expected",
    [
        (
            "https://example.com/api",
            RemoteServerParameters(url="https://example.com/api"),
        ),
        (
            "VAR1=value1 VAR2=value2 command --arg1 --arg2",
            StdioServerParameters(
                command="command",
                args=["--arg1", "--arg2"],
                env={"VAR1": "value1", "VAR2": "value2"},
            ),
        ),
        (
            "npx cmd --flag",
            StdioServerParameters(
                command="npx", args=["cmd", "--flag"], env=None
            ),
        ),
        (
            "",
            None,
        ),
    ],
)
def test_convert(param, expected):
    assert parse_params(param) == expected
