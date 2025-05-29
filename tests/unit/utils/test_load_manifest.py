"""Tests for the load_manifest utility function."""

import json
import os
import tempfile
from unittest import TestCase

from llm_mcp.utils import load_manifest


class TestLoadManifest(TestCase):
    """Test the load_manifest utility function."""

    def test_load_from_string(self):
        """Test loading manifest from a JSON string."""
        manifest_str = """{"name": "test-server", "tools": [{"name": "test-tool", "description": "Test tool", "parameters": {}}]}"""
        manifest = load_manifest(manifest_str)

        self.assertEqual(manifest["name"], "test-server")
        self.assertEqual(len(manifest["tools"]), 1)
        self.assertEqual(manifest["tools"][0]["name"], "test-tool")
        self.assertEqual(manifest["tools"][0]["description"], "Test tool")

    def test_load_from_file(self):
        """Test loading manifest from a JSON file."""
        manifest_data = {
            "name": "test-server-file",
            "tools": [
                {
                    "name": "test-tool-file",
                    "description": "Test tool from file",
                    "parameters": {},
                }
            ],
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(manifest_data, f)
            temp_file = f.name

        try:
            manifest = load_manifest(temp_file)

            self.assertEqual(manifest["name"], "test-server-file")
            self.assertEqual(len(manifest["tools"]), 1)
            self.assertEqual(manifest["tools"][0]["name"], "test-tool-file")
            self.assertEqual(
                manifest["tools"][0]["description"], "Test tool from file"
            )
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_invalid_string(self):
        """Test error handling for invalid JSON string."""
        with self.assertRaises(ValueError):
            load_manifest('{"invalid": "json"')

        # Not JSON-like string
        with self.assertRaises(ValueError):
            load_manifest("not a json string")

    def test_nonexistent_file(self):
        """Test handling of a non-existent file path that looks like JSON."""
        # This should be treated as a JSON string, not a file path
        manifest_str = '{"name": "not-a-file", "tools": []}'
        manifest = load_manifest(manifest_str)

        self.assertEqual(manifest["name"], "not-a-file")
        self.assertEqual(manifest["tools"], [])
