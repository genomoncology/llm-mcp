"""Tests for the toolbox_builder module."""

import asyncio
import sys
from unittest import TestCase, mock

from llm_mcp.toolbox_builder import (
    _cleanup_dynamic_module,
    _create_wrapper_method,
    _parse_mcp_reference,
    _validate_function_code,
)


class TestCreateWrapperMethod(TestCase):
    """Test the _create_wrapper_method function."""

    def test_sync_function_wrapper(self):
        """Test creating a wrapper for a synchronous function."""

        # Define a simple synchronous function
        def test_func(x=1, y=2):
            return x + y

        # Create a wrapper
        wrapper = _create_wrapper_method(test_func)

        # Check the wrapper is not async
        self.assertFalse(asyncio.iscoroutinefunction(wrapper))

        # Test the wrapper with a mock self
        mock_self = mock.Mock()
        result = wrapper(mock_self, x=5, y=10)
        self.assertEqual(result, 15)

    def test_async_function_wrapper(self):
        """Test creating a wrapper for an asynchronous function."""

        # Define a simple asynchronous function
        async def test_async_func(x=1, y=2):
            await asyncio.sleep(0.01)  # Short sleep to simulate async work
            return x + y

        # Create a wrapper
        wrapper = _create_wrapper_method(test_async_func)

        # The wrapper should now be synchronous (not a coroutine function)
        # because it uses the background runner to execute the async function
        self.assertFalse(asyncio.iscoroutinefunction(wrapper))

        # Test the wrapper with a mock self - it should run synchronously now
        mock_self = mock.Mock()
        result = wrapper(mock_self, x=5, y=10)
        self.assertEqual(result, 15)


class TestCleanupDynamicModule(TestCase):
    """Test the _cleanup_dynamic_module function."""

    def test_cleanup_removes_module(self):
        """Test that _cleanup_dynamic_module removes a module from sys.modules."""
        # Create a temporary module
        module_name = "_test_temp_module"
        sys.modules[module_name] = mock.Mock()

        # Verify it exists
        self.assertIn(module_name, sys.modules)

        # Clean it up
        _cleanup_dynamic_module(module_name)

        # Verify it's gone
        self.assertNotIn(module_name, sys.modules)

    def test_cleanup_nonexistent_module(self):
        """Test that _cleanup_dynamic_module handles non-existent modules gracefully."""
        module_name = "_nonexistent_module"

        # Ensure it doesn't exist
        if module_name in sys.modules:
            del sys.modules[module_name]

        # This should not raise an exception
        _cleanup_dynamic_module(module_name)


class TestValidateFunctionCode(TestCase):
    """Test the _validate_function_code function."""

    def test_valid_code(self):
        """Test that valid code passes validation."""
        code = "def test_func(x, y):\n    return x + y"
        issues = _validate_function_code(code)
        self.assertEqual(issues, [])

    def test_missing_function(self):
        """Test validation when no function is defined."""
        code = "x = 1 + 2"
        issues = _validate_function_code(code)
        self.assertTrue(
            any("No function definitions" in issue for issue in issues)
        )

    def test_syntax_error(self):
        """Test validation with syntax error."""
        code = "def broken_func():\n    return x ++"
        issues = _validate_function_code(code)
        self.assertTrue(any("Syntax error" in issue for issue in issues))

    def test_function_name_mismatch(self):
        """Test validation when specified function name doesn't exist."""
        code = "def test_func(x, y):\n    return x + y"
        issues = _validate_function_code(code, function_name="other_func")
        self.assertTrue(
            any(
                "not found" in issue and "test_func" in issue
                for issue in issues
            )
        )


class TestParseMCPReference(TestCase):
    """Test the _parse_mcp_reference function."""

    def test_valid_reference(self):
        """Test parsing a valid MCP reference."""
        server_name, tool_name = _parse_mcp_reference("server_name/tool_name")
        self.assertEqual(server_name, "server_name")
        self.assertEqual(tool_name, "tool_name")

    def test_hyphenated_names(self):
        """Test parsing an MCP reference with hyphens in the names."""
        server_name, tool_name = _parse_mcp_reference("test-server/test-tool")
        self.assertEqual(server_name, "test-server")
        self.assertEqual(tool_name, "test-tool")

    def test_invalid_reference(self):
        """Test handling of invalid MCP references."""
        with self.assertRaises(ValueError):
            _parse_mcp_reference("invalid_reference")

        with self.assertRaises(ValueError):
            _parse_mcp_reference("too/many/parts")

        with self.assertRaises(ValueError):
            _parse_mcp_reference(
                "UPPERCASE/tool"
            )  # Server name must be lowercase
