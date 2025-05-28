"""Tests for manifest normalization in the manager module."""

import json
import os
import tempfile
from unittest import TestCase

from llm_mcp.manager import _create_config_from_manifest


class TestManifestNormalization(TestCase):
    """Test the manifest normalization in manager.py."""

    def test_hyphenated_name(self):
        """Test that hyphenated server names are accepted."""
        manifest_str = """{"name": "test-server", "tools": []}"""
        cfg, name = _create_config_from_manifest(manifest_str)

        self.assertEqual(name, "test-server")
        self.assertEqual(cfg.name, "test-server")

    def test_parameters_to_inputschema_conversion(self):
        """Test that 'parameters' is converted to 'inputSchema'."""
        manifest_str = """
        {
            "name": "test-server",
            "tools": [
                {
                    "name": "test-tool",
                    "description": "Test tool",
                    "parameters": {"type": "object"}
                }
            ]
        }
        """
        cfg, name = _create_config_from_manifest(manifest_str)

        self.assertEqual(len(cfg.tools), 1)
        self.assertEqual(cfg.tools[0].name, "test-tool")
        self.assertEqual(cfg.tools[0].description, "Test tool")
        # Verify that parameters was converted to inputSchema
        self.assertEqual(cfg.tools[0].inputSchema, {"type": "object"})
        # Verify that the original 'parameters' key is not present
        tool_dict = cfg.tools[0].model_dump()
        self.assertNotIn("parameters", tool_dict)

    def test_missing_description_defaults(self):
        """Test that missing description is defaulted to empty string."""
        manifest_str = """
        {
            "name": "test-server",
            "tools": [
                {
                    "name": "test-tool",
                    "parameters": {}
                }
            ]
        }
        """
        cfg, name = _create_config_from_manifest(manifest_str)

        self.assertEqual(len(cfg.tools), 1)
        self.assertEqual(cfg.tools[0].name, "test-tool")
        # Verify that description was defaulted to empty string
        self.assertEqual(cfg.tools[0].description, "")

    def test_complete_manifest_normalization(self):
        """Test a complete manifest normalization with all features."""
        manifest_data = {
            "name": "test-hyphenated-server",
            "tools": [
                {
                    "name": "tool-with-parameters",
                    "parameters": {"type": "object", "properties": {}},
                    "annotations": {"some": "annotation"},
                },
                {"name": "tool-without-description", "parameters": {}},
            ],
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(manifest_data, f)
            temp_file = f.name

        try:
            # Test loading directly from file
            cfg, name = _create_config_from_manifest(temp_file)

            self.assertEqual(name, "test-hyphenated-server")
            self.assertEqual(len(cfg.tools), 2)

            # First tool should have inputSchema and no annotations
            self.assertEqual(cfg.tools[0].name, "tool-with-parameters")
            self.assertEqual(
                cfg.tools[0].inputSchema, {"type": "object", "properties": {}}
            )
            tool_dict = cfg.tools[0].model_dump()
            self.assertNotIn("parameters", tool_dict)
            # Instead of checking that annotations is not present, check that it's None
            self.assertIsNone(tool_dict.get("annotations"))

            # Second tool should have default description
            self.assertEqual(cfg.tools[1].name, "tool-without-description")
            self.assertEqual(cfg.tools[1].description, "")
            self.assertEqual(cfg.tools[1].inputSchema, {})

        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file):
                os.unlink(temp_file)
