import base64
from datetime import timedelta
from types import SimpleNamespace

import pytest

from llm_mcp.schema import RemoteServerParameters, StdioServerParameters
from llm_mcp.utils import convert_content, generate_server_name, parse_params


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
            "node server.js --format=json --port=8080",
            StdioServerParameters(
                command="node",
                args=["server.js", "--format=json", "--port=8080"],
                env=None,
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
        ("uvx mcp-server-sqlite --db-path test.db", "sqlite_test"),
        ("https://api.example.com/mcp", "example_api"),
        ("java -jar weather-server.jar", "weather"),
        ("docker run -i mcp/perplexity-ask", "perplexity_ask"),
        ("python /path/to/gmail_server.py", "gmail_server"),
        ("node build/index.js", "index"),
        ("https://localhost:8080/sse", "localhost_8080"),
        ("/usr/local/bin/my-mcp-server", "my_mcp_server"),
    ],
)
def test_generate_server_name(param, expected_name):
    params = parse_params(param)
    assert params is not None
    assert generate_server_name(params) == expected_name


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


# noinspection PyTypeChecker
def _b64(data: bytes) -> str:
    """Return a **str** base-64 representation (what the real MCP objects use)."""
    return base64.b64encode(data).decode()


# --------------------------------------------------------------------------- #
# Dummy MCP classes - patched in so isinstance() checks work                  #
# --------------------------------------------------------------------------- #


class DummyImageContent:
    def __init__(self, raw: bytes):
        self.data = _b64(raw)


class DummyTextResourceContents:
    def __init__(self, text: str):
        self.text = text


class DummyBlobResourceContents:
    def __init__(self, blob: bytes):
        self.blob = _b64(blob)


class DummyEmbeddedResource:
    def __init__(self, resource):
        self.resource = resource


@pytest.fixture(autouse=True)
def _patch_mcp_types(monkeypatch: pytest.MonkeyPatch):
    """Monkey-patch `mcp.types` with our dummy classes."""
    import mcp.types as mcp_types

    monkeypatch.setattr(
        mcp_types, "ImageContent", DummyImageContent, raising=False
    )
    monkeypatch.setattr(
        mcp_types, "EmbeddedResource", DummyEmbeddedResource, raising=False
    )
    monkeypatch.setattr(
        mcp_types,
        "TextResourceContents",
        DummyTextResourceContents,
        raising=False,
    )
    monkeypatch.setattr(
        mcp_types,
        "BlobResourceContents",
        DummyBlobResourceContents,
        raising=False,
    )


# --------------------------------------------------------------------------- #
# Tests - plain / JSON text                                                  #
# --------------------------------------------------------------------------- #


def test_json_text():
    part = SimpleNamespace(text='{"answer": 42}')
    assert convert_content(part) == {"answer": 42}


def test_plain_text():
    part = SimpleNamespace(text="hello")
    assert convert_content(part) == "hello"


# --------------------------------------------------------------------------- #
# Tests - binary helpers                                                     #
# --------------------------------------------------------------------------- #


def test_image_content():
    raw = b"img-bytes"
    part = DummyImageContent(raw)
    assert convert_content(part) == raw


def test_embedded_text():
    part = DummyEmbeddedResource(DummyTextResourceContents("hi"))
    assert convert_content(part) == "hi"


def test_embedded_blob():
    raw = b"data-bytes"
    part = DummyEmbeddedResource(DummyBlobResourceContents(raw))
    assert convert_content(part) == raw
