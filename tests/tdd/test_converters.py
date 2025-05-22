from __future__ import annotations

import base64
from types import SimpleNamespace

import pytest

from llm_mcp.converters import convert_content

# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


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
