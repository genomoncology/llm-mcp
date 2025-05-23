from llm_mcp import schema, wrap_mcp


def test_wrap_mcp(mocker):
    http_mock = mocker.patch("llm_mcp.http.list_tools_sync", return_value=[])
    stdio_mock = mocker.patch("llm_mcp.stdio.list_tools_sync", return_value=[])
    params = [
        schema.RemoteServerParameters(url="https://api1.com"),
        schema.StdioServerParameters(command="npx", args=["tool1"]),
        "ENV=value npx tool",
        "https://example.com/api",
    ]
    result = wrap_mcp(*params)
    assert result == []
    assert http_mock.call_count == 2
    http_mock.assert_any_call(params[0])
    http_mock.assert_any_call(
        schema.RemoteServerParameters(
            url="https://example.com/api",
        )
    )

    assert stdio_mock.call_count == 2
    stdio_mock.assert_any_call(params[1])
    stdio_mock.assert_any_call(
        schema.StdioServerParameters(
            command="npx", args=["tool"], env={"ENV": "value"}
        )
    )


def test_wrap_mcp_empties(mocker):
    assert wrap_mcp("") == []
    assert wrap_mcp() == []
