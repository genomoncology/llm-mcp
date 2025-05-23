from llm_mcp import schema, wrap_http, wrap_mcp, wrap_stdio


def test_wrap_stdio(mocker):
    mock_list = mocker.patch("llm_mcp.stdio.list_tools_sync", return_value=[])
    params = [
        schema.StdioServerParameters(command="npx", args=["tool1"]),
        schema.StdioServerParameters(command="npx", args=["tool2"]),
    ]
    result = wrap_stdio(*params)
    assert result == []
    assert mock_list.call_count == 2
    mock_list.assert_any_call(params[0])
    mock_list.assert_any_call(params[1])


def test_wrap_http(mocker):
    mock_list = mocker.patch("llm_mcp.http.list_tools_sync", return_value=[])
    params = [
        schema.RemoteServerParameters(url="https://api1.com"),
        schema.RemoteServerParameters(url="https://api2.com"),
    ]
    result = wrap_http(*params)
    assert result == []
    assert mock_list.call_count == 2
    mock_list.assert_any_call(params[0])
    mock_list.assert_any_call(params[1])


def test_wrap_mcp_empties(mocker):
    assert wrap_mcp("") == []
    assert wrap_mcp() == []


http_params = schema.RemoteServerParameters(
    url="https://example.com/api",
)

stdio_params = schema.StdioServerParameters(
    command="npx", args=["tool"], env={"ENV": "value"}
)


def test_wrap_strings(mocker):
    mock_stdio = mocker.patch("llm_mcp.stdio.list_tools_sync", return_value=[])
    mock_http = mocker.patch("llm_mcp.http.list_tools_sync", return_value=[])

    params = [
        "ENV=value npx tool",
        "https://example.com/api",
    ]
    result = wrap_mcp(*params)
    assert result == []
    mock_stdio.assert_called_once_with(stdio_params)
    mock_http.assert_called_once_with(http_params)


def test_wrap_existing_params(mocker):
    mock_stdio = mocker.patch("llm_mcp.stdio.list_tools_sync", return_value=[])
    mock_http = mocker.patch("llm_mcp.http.list_tools_sync", return_value=[])

    result = wrap_mcp(http_params, stdio_params)
    assert result == []
    mock_stdio.assert_called_once_with(stdio_params)
    mock_http.assert_called_once_with(http_params)
