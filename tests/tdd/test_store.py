from llm_mcp import schema, store


def test_load_server(monkeypatch, data_dir):
    monkeypatch.setenv("LLM_MCP_HOME", str(data_dir / "mcp"))
    server_config = store.load_server("gitmcp_llm")
    assert isinstance(server_config, schema.ServerConfig)

    # check fetch_llm_documentation tool which must be "cleaned"
    tool = server_config.get_tool("fetch_llm_documentation")
    assert tool.name == "fetch_llm_documentation"
    assert tool.annotations.model_extra == {}
    assert tool.inputSchema == {}

    # check other tools
    tool = server_config.get_tool("search_llm_documentation")
    assert tool.name == "search_llm_documentation"
    assert tool.annotations is None
    assert tool.inputSchema == {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "additionalProperties": False,
        "properties": {
            "query": {
                "description": "The search query to find relevant "
                "documentation",
                "type": "string",
            }
        },
        "required": ["query"],
        "type": "object",
    }
