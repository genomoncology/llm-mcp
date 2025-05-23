import pytest

from llm_mcp import http, stdio, wrap, wrap_http, wrap_mcp, wrap_stdio


@pytest.mark.parametrize(
    "param, expected",
    [
        (
            "https://example.com/api",
            http.ServerParameters(base_url="https://example.com/api"),
        ),
        (
            "VAR1=value1 VAR2=value2 command --arg1 --arg2",
            stdio.ServerParameters(
                command="command",
                args=["--arg1", "--arg2"],
                env={"VAR1": "value1", "VAR2": "value2"},
            ),
        ),
        (
            "npx cmd --flag",
            stdio.ServerParameters(
                command="npx", args=["cmd", "--flag"], env=None
            ),
        ),
        (
            "",
            None,
        ),
    ],
)
def test_convert(param, expected):
    assert wrap._convert(param) == expected


def test_wrap_stdio(mocker):
    mock_list = mocker.patch("llm_mcp.stdio.list_tools_sync", return_value=[])
    params = [
        stdio.ServerParameters(command="npx", args=["tool1"]),
        stdio.ServerParameters(command="npx", args=["tool2"]),
    ]
    result = wrap_stdio(*params)
    assert result == []
    assert mock_list.call_count == 2
    mock_list.assert_any_call(params[0])
    mock_list.assert_any_call(params[1])


def test_wrap_http(mocker):
    mock_list = mocker.patch("llm_mcp.http.list_tools_sync", return_value=[])
    params = [
        http.ServerParameters(base_url="https://api1.com"),
        http.ServerParameters(base_url="https://api2.com"),
    ]
    result = wrap_http(*params)
    assert result == []
    assert mock_list.call_count == 2
    mock_list.assert_any_call(params[0])
    mock_list.assert_any_call(params[1])


http_params = http.ServerParameters(base_url="https://example.com/api")
stdio_params = stdio.ServerParameters(
    command="npx", args=["tool"], env={"ENV": "value"}
)


def test_wrap_mcp_empties(mocker):
    assert wrap_mcp("") == []
    assert wrap_mcp() == []


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
