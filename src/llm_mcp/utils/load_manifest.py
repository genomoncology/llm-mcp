"""Utility for loading server manifests from JSON files or strings."""

import json
import os
from typing import Any, cast


def load_manifest(manifest_arg: str) -> dict[str, Any]:
    """
    Load a server manifest from a file path or JSON string.

    Args:
        manifest_arg: Either a path to a JSON file or a JSON string literal.

    Returns:
        Parsed JSON data as a dictionary

    Raises:
        ValueError: If the manifest cannot be parsed or is invalid.
    """
    # Check if this is a path to an existing file
    if os.path.exists(manifest_arg) and os.path.isfile(manifest_arg):
        try:
            with open(manifest_arg) as f:
                return cast(dict[str, Any], json.load(f))
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse manifest file: {e}") from e
        except Exception as e:
            raise ValueError(f"Failed to read manifest file: {e}") from e

    # Otherwise, treat it as a JSON string
    try:
        # Verify it looks like JSON (starts with { or [)
        if not (
            manifest_arg.strip().startswith("{")
            or manifest_arg.strip().startswith("[")
        ):
            raise ValueError(
                "Manifest string does not appear to be valid JSON (should start with '{' or '[')"
            )

        return cast(dict[str, Any], json.loads(manifest_arg))
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse manifest JSON string: {e}") from e
