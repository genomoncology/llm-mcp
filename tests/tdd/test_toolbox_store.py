"""Unit tests for toolbox store functionality."""

from llm_mcp import schema, store


def _sample_cfg():
    return schema.ToolboxConfig(
        name="fs_tools",
        description="Filesystem helpers",
        tools=[
            # Explicitly include the kind field to ensure it's preserved during serialization
            schema.MCPToolRef(
                server="desktop_commander", tool="read_file", kind="mcp"
            )
        ],
    )


def test_roundtrip(tmp_path, monkeypatch):
    # isolate MCP dir
    monkeypatch.setenv("LLM_USER_PATH", str(tmp_path))
    cfg = _sample_cfg()
    store.save_toolbox(cfg)
    loaded = store.load_toolbox("fs_tools")
    assert loaded == cfg
    assert "fs_tools" in store.list_toolboxes()
    assert store.remove_toolbox("fs_tools") is True
    assert store.load_toolbox("fs_tools") is None
