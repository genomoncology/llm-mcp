# llm-mcp

[![Release](https://img.shields.io/github/v/release/imaurer/llm-mcp)](https://img.shields.io/github/v/release/imaurer/llm-mcp)
[![Build status](https://img.shields.io/github/actions/workflow/status/imaurer/llm-mcp/main.yml?branch=main)](https://github.com/imaurer/llm-mcp/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/imaurer/llm-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/imaurer/llm-mcp)
[![MIT License](https://img.shields.io/github/license/imaurer/llm-mcp)](https://img.shields.io/github/license/imaurer/llm-mcp)

[`llm`](https://llm.datasette.io/) [plugin](https://llm.datasette.io/en/stable/plugins/directory.html) for creating MCP clients and servers.

## Installation

```bash
pip install llm-mcp
```

## MCP Servers

This package provides a bridge between MCP servers and the `llm` package, allowing you to use MCP tools with LLM models. The bridge supports both stdio and HTTP-based MCP servers and provides a synchronous interface that's safe to use in any context, including Jupyter notebooks, FastAPI applications, and more.

### Command Line Usage

You can use MCP tools directly from the command line with the `llm` CLI:

```bash
llm --model gpt-4o-mini \
    --tool list_directory "What files are here?"
```

### Programmatic Usage

For programmatic usage, you can wrap MCP tools as `llm.Tool` objects:

```python
from llm.models import Model
from mcp.client.stdio import StdioServerParameters
from llm_mcp import wrap_tools_from_stdio

# Connect to an MCP server
server_params = StdioServerParameters(
    command="npx",
    args=["-y", "@wonderwhy-er/desktop-commander"],
)

# Wrap the MCP tools for use with llm
tools = wrap_tools_from_stdio(server_params)

# Use the tools with a model
model = Model.from_string("gpt-3.5-turbo")
response = model.chain("List the files in this directory", tools=tools)
print(response.text)
```

### HTTP Servers

For HTTP-based MCP servers, use the HTTP bridge instead:

```python
from mcp.client.streamable_http import StreamableHttpServerParameters
from llm_mcp import wrap_tools_from_http

server_params = StreamableHttpServerParameters(
    base_url="http://localhost:3000",
)

tools = wrap_tools_from_http(server_params)
```

### Sync Bridge Guarantees

The sync bridge provides the following guarantees:

- Safe to use in any context, including Jupyter notebooks and FastAPI applications
- Automatically reuses connections for better performance
- Properly handles asyncio event loops in all contexts
- Converts MCP results to Python objects
