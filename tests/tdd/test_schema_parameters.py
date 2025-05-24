from datetime import timedelta

import pytest

from llm_mcp.schema import (
    RemoteServerParameters,
    StdioServerParameters,
    ensure_unique_name,
    generate_server_name,
    parse_params,
)


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


@pytest.mark.parametrize(
    "param, expected_name",
    [
        ("npx -y @modelcontextprotocol/server-filesystem /home", "filesystem"),
        ("uvx mcp-server-sqlite --db-path test.db", "sqlite-test"),
        ("https://api.example.com/mcp", "example-api"),
        ("java -jar weather-server.jar", "weather"),
        ("docker run -i mcp/perplexity-ask", "perplexity-ask"),
        ("python /path/to/gmail_server.py", "gmail_server"),
        ("node build/index.js", "index"),
        ("https://localhost:8080/sse", "localhost-8080"),
        ("/usr/local/bin/my-mcp-server", "my-mcp-server"),
    ],
)
def test_generate_server_name(param, expected_name):
    params = parse_params(param)
    assert params is not None
    assert generate_server_name(params) == expected_name


def test_ensure_unique_names():
    existing = {"sqlite", "sqlite-2", "filesystem"}
    assert ensure_unique_name("postgres", existing) == "postgres"
    assert ensure_unique_name("sqlite", existing) == "sqlite-3"
    assert ensure_unique_name("filesystem", existing) == "filesystem-2"
