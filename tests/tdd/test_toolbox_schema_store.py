"""Unit tests for the new toolbox schema and store implementation."""

import pytest

from llm_mcp.schema.toolboxes import (
    MCPToolRef,
    PythonToolRef,
    ToolboxConfig,
    ToolboxMethodRef,
)
from llm_mcp.store import (
    _toolbox_path,
    list_toolboxes,
    load_toolbox,
    remove_toolbox,
    save_toolbox,
)


def _sample_cfg():
    """Create a sample toolbox config for testing."""
    return ToolboxConfig(
        name="fs_tools",
        description="Filesystem helpers",
        tools=[
            MCPToolRef(
                server="desktop_commander", tool="read_file", kind="mcp"
            )
        ],
    )


def test_toolbox_schema():
    """Test the schema models work as expected."""
    # Test MCPToolRef
    mcp_ref = MCPToolRef(server="server1", tool="tool1")
    assert mcp_ref.kind == "mcp"
    assert mcp_ref.server == "server1"
    assert mcp_ref.tool == "tool1"

    # Test PythonToolRef
    py_ref = PythonToolRef(module="my.module", attr="function_name")
    assert py_ref.kind == "python"
    assert py_ref.module == "my.module"
    assert py_ref.attr == "function_name"

    # Test ToolboxMethodRef
    tb_ref = ToolboxMethodRef(toolbox="my_toolbox", method="method_name")
    assert tb_ref.kind == "toolbox"
    assert tb_ref.toolbox == "my_toolbox"
    assert tb_ref.method == "method_name"

    # Test ToolboxConfig
    config = ToolboxConfig(
        name="test_toolbox",
        description="Test toolbox",
        tools=[mcp_ref, py_ref, tb_ref],
        config={"key": "value"},
    )
    assert config.name == "test_toolbox"
    assert config.description == "Test toolbox"
    assert len(config.tools) == 3
    assert config.config == {"key": "value"}


def test_toolbox_name_collision():
    """Test that duplicate tool names are detected."""
    with pytest.raises(ValueError, match="Duplicate tool name"):
        ToolboxConfig(
            name="duplicate_tools",
            tools=[
                MCPToolRef(server="server1", tool="same_name"),
                PythonToolRef(module="module", attr="attr", name="same_name"),
            ],
        )


def test_roundtrip_direct(tmp_path):
    """Test direct JSON serialization and deserialization."""
    cfg = _sample_cfg()

    # Serialize to JSON with discriminator fields preserved
    json_data = cfg.model_dump_json(
        indent=2,
        exclude_none=True,
        exclude_unset=True,
        exclude_defaults=False,  # keep discriminator fields
    )

    # Write to file directly
    tmp_file = tmp_path / "test.json"
    tmp_file.write_text(json_data)

    # Read back and deserialize
    loaded_json = tmp_file.read_text()
    loaded_cfg = ToolboxConfig.model_validate_json(loaded_json)

    # Compare
    assert loaded_cfg == cfg


def test_store_functions(tmp_path, monkeypatch):
    """Test the store functions for toolbox persistence."""
    # Set up a test environment
    mcp_test_dir = tmp_path / "mcp"
    monkeypatch.setattr("llm_mcp.store.mcp_dir", lambda: mcp_test_dir)

    # Create a sample config
    cfg = _sample_cfg()

    # Test saving
    path = save_toolbox(cfg)
    assert path == mcp_test_dir / "toolboxes" / "fs_tools.json"
    assert path.exists()

    # Test listing
    toolboxes = list_toolboxes()
    assert "fs_tools" in toolboxes

    # Test loading
    loaded_cfg = load_toolbox("fs_tools")
    assert loaded_cfg == cfg

    # Test non-existent toolbox
    assert load_toolbox("nonexistent") is None

    # Test removing
    assert remove_toolbox("fs_tools") is True
    assert not _toolbox_path("fs_tools").exists()
    assert remove_toolbox("nonexistent") is False
