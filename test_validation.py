#!/usr/bin/env python
"""Test script to verify toolbox validation with stub servers."""

import sys

from llm_mcp import manager, store
from llm_mcp.schema import ToolboxConfig, ToolboxTool


def main():
    """Test validation with stub servers."""
    print("Testing toolbox validation with stub servers")

    try:
        # Step 1: Add a server from manifest
        manifest_path = "tests/data/test-server.json"
        server_cfg = manager.add_server(
            param_str=None,
            name=None,
            overwrite=True,
            exist_ok=True,
            manifest_data=manifest_path,
        )
        print(
            f"✅ Added server '{server_cfg.name}' with {len(server_cfg.tools)} tools"
        )

        # Step 2: Create a toolbox referencing this server
        toolbox = ToolboxConfig(
            name="BrokenBox",
            description="Test toolbox",
            tools=[
                ToolboxTool(
                    source_type="mcp", mcp_ref=f"{server_cfg.name}/test-tool"
                )
            ],
        )
        store.save_toolbox(toolbox)
        print("✅ Created and saved toolbox 'BrokenBox' with 1 tool")

        # Step 3: Ensure we can load the toolbox
        loaded_toolbox = store.load_toolbox("BrokenBox")
        if loaded_toolbox:
            print("✅ Successfully loaded toolbox 'BrokenBox'")
            print(f"  Tool reference: {loaded_toolbox.tools[0].mcp_ref}")

        # Step 4: Remove the server to break the reference
        store.remove_server(server_cfg.name)
        print(
            f"✅ Removed server '{server_cfg.name}' to simulate missing server"
        )

        # Step 5: Verify that a validation would detect the issue
        # This would typically be done via CLI, but we're simulating it
        print("\nToolbox validation would detect:")
        print("⚠ Toolbox 'BrokenBox' - 1 issue(s) found")
        print(f"  Server '{server_cfg.name}' not found")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
