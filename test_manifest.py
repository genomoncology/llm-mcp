#!/usr/bin/env python
"""Test script to verify manifest normalization works correctly."""

import sys

from llm_mcp import manager, store


def main():
    """Test the manifest normalization functionality."""
    manifest_path = "tests/data/test-server.json"
    print(f"Testing manifest normalization with file: {manifest_path}")

    try:
        # Try to add the server with the manifest
        cfg = manager.add_server(
            param_str=None,
            name=None,
            overwrite=True,
            exist_ok=True,
            manifest_data=manifest_path,
        )
        print(
            f"✅ Successfully added server '{cfg.name}' with {len(cfg.tools)} tools"
        )

        # Verify the tools were normalized correctly
        print("\nTool details:")
        for i, tool in enumerate(cfg.tools):
            print(f"  Tool {i + 1}: {tool.name}")
            print(f"    Description: {tool.description}")
            print(f"    Input Schema: {tool.inputSchema}")

        # Verify we can load the server again
        loaded_cfg = store.load_server(cfg.name)
        if loaded_cfg:
            print(
                f"\n✅ Successfully loaded server '{loaded_cfg.name}' from store"
            )
        else:
            print("\n❌ Failed to load server from store")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
