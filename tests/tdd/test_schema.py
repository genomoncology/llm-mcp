from llm_mcp import schema


def test_clean_server_config(data_dir):
    # load file
    file = data_dir / "gitmcp_llm.json"
    assert file.is_file()
    server_config = schema.ServerConfig.model_validate_json(file.read_text())

    # check before cleaning
    tool = server_config.get_tool("fetch_llm_documentation")
    assert tool.annotations.model_extra != {}
    assert tool.inputSchema != {}

    # clean server config
    server_config.clean()

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
