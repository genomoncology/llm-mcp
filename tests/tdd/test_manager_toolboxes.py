"""Unit tests for the toolbox manager layer."""

import os
import tempfile
from pathlib import Path

import pytest

from llm_mcp.manager import toolboxes as mgr
from llm_mcp.manager.errors import (
    ToolboxExists,
    ToolboxNotFound,
    ToolExists,
    ToolNotFound,
)
from llm_mcp.schema.toolboxes import MCPToolRef


@pytest.fixture
def temp_mcp_dir():
    """Create a temporary directory for MCP files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        old_path = os.environ.get("LLM_USER_PATH")
        os.environ["LLM_USER_PATH"] = tmpdir
        yield Path(tmpdir)
        if old_path:
            os.environ["LLM_USER_PATH"] = old_path
        else:
            del os.environ["LLM_USER_PATH"]


def test_create_and_get(temp_mcp_dir):
    """Test creating and retrieving a toolbox."""
    # Create a toolbox
    name = "test_box"
    description = "Test toolbox"
    config = mgr.create(name, description=description)

    # Verify the config
    assert config.name == name
    assert config.description == description

    # Get the toolbox and verify
    retrieved = mgr.get_toolbox(name)
    assert retrieved.name == name
    assert retrieved.description == description


def test_create_duplicate(temp_mcp_dir):
    """Test creating a duplicate toolbox raises ToolboxExists."""
    name = "test_box"
    mgr.create(name)

    # Try to create again
    with pytest.raises(ToolboxExists):
        mgr.create(name)


def test_add_tool_duplicate(temp_mcp_dir):
    """Test adding a duplicate tool raises ToolExists."""
    # Create a toolbox
    tb_name = "test_box"
    mgr.create(tb_name)

    # Add a tool
    tool = MCPToolRef(server="test_server", tool="test_tool")
    mgr.add_tool(tb_name, tool)

    # Try to add the same tool again
    with pytest.raises(ToolExists):
        mgr.add_tool(tb_name, tool)


def test_remove_tool_missing(temp_mcp_dir):
    """Test removing a missing tool raises ToolNotFound."""
    # Create a toolbox
    tb_name = "test_box"
    mgr.create(tb_name)

    # Try to remove a non-existent tool
    with pytest.raises(ToolNotFound):
        mgr.remove_tool(tb_name, "non_existent_tool")


def test_default_toolbox_roundtrip(temp_mcp_dir):
    """Test setting and getting the default toolbox."""
    # Create a toolbox
    tb_name = "test_box"
    mgr.create(tb_name)

    # Set as default
    mgr.set_default(tb_name)

    # Get default and verify
    default = mgr.get_default()
    assert default == tb_name

    # Clear default
    mgr.clear_default()
    assert mgr.get_default() is None


def test_validate_missing_server(temp_mcp_dir):
    """Test validation with a missing server."""
    # Create a toolbox
    tb_name = "test_box"
    mgr.create(tb_name)

    # Add a tool with a non-existent server
    tool = MCPToolRef(server="non_existent_server", tool="test_tool")
    mgr.add_tool(tb_name, tool)

    # Validate and check for problems
    problems = mgr.validate(tb_name)
    assert len(problems) == 1
    assert "Server 'non_existent_server' not found" in problems[0]


def test_list_toolboxes(temp_mcp_dir):
    """Test listing toolboxes."""
    # Create some toolboxes
    mgr.create("box1")
    mgr.create("box2")
    mgr.create("box3")

    # List and verify
    boxes = mgr.list_toolboxes()
    assert len(boxes) == 3
    assert set(boxes) == {"box1", "box2", "box3"}


def test_remove_toolbox(temp_mcp_dir):
    """Test removing a toolbox."""
    # Create a toolbox
    tb_name = "test_box"
    mgr.create(tb_name)

    # Verify it exists
    assert tb_name in mgr.list_toolboxes()

    # Remove it
    mgr.remove(tb_name)

    # Verify it's gone
    assert tb_name not in mgr.list_toolboxes()

    # Try to remove again
    with pytest.raises(ToolboxNotFound):
        mgr.remove(tb_name)


def test_remove_default_toolbox(temp_mcp_dir):
    """Test removing the default toolbox clears the default."""
    # Create a toolbox and set as default
    tb_name = "test_box"
    mgr.create(tb_name)
    mgr.set_default(tb_name)

    # Verify it's the default
    assert mgr.get_default() == tb_name

    # Remove it
    mgr.remove(tb_name)

    # Verify default is cleared
    assert mgr.get_default() is None
