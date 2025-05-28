"""Conversion utility files."""

import base64
import json
from typing import Any

from mcp import types

ContentType = types.TextContent | types.ImageContent | types.EmbeddedResource


def convert_content(part: ContentType) -> Any:
    """Best-effort conversion of an MCP *content type* to a Python value."""

    output: Any = None

    if isinstance(part, types.TextContent) or (
        hasattr(part, "text") and isinstance(part.text, str)
    ):
        try:
            output = json.loads(part.text)
        except ValueError:
            output = part.text

    elif isinstance(part, types.ImageContent):
        output = base64.b64decode(part.data)

    elif isinstance(part, types.EmbeddedResource):
        res = part.resource
        if isinstance(res, types.TextResourceContents):
            output = res.text
        else:
            output = base64.b64decode(res.blob)

    return output
