# llm-mcp

[![Release](https://img.shields.io/github/v/release/imaurer/llm-mcp)](https://img.shields.io/github/v/release/imaurer/llm-mcp)
[![Build status](https://img.shields.io/github/actions/workflow/status/imaurer/llm-mcp/main.yml?branch=main)](https://github.com/imaurer/llm-mcp/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/imaurer/llm-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/imaurer/llm-mcp)
[![MIT License](https://img.shields.io/github/license/imaurer/llm-mcp)](https://img.shields.io/github/license/imaurer/llm-mcp)

[
`llm`](https://llm.datasette.io/) [plugin](https://llm.datasette.io/en/stable/plugins/directory.html)
for creating MCP clients and servers.

## Installation

```bash
pip install llm-mcp
```

## MCP Servers

This package provides a bridge between MCP servers and the `llm` package,
allowing you to use MCP tools with LLM models. The bridge supports both stdio
and HTTP-based MCP servers and provides a synchronous interface that's safe to
use in any context, including Jupyter notebooks, FastAPI applications, and
more.

### Command Line Usage

(todo)

### Programmatic Usage

For programmatic usage, you can wrap MCP tools as `llm.Tool` objects:

```python
import os

from llm import get_model
from llm_mcp import wrap_stdio, stdio

# convert stdio tool to llm tools
tools = wrap_stdio(stdio.ServerParameters(
    command="npx",
    args=["-y", "@wonderwhy-er/desktop-commander"],
))

# wrap_mcp(command string) equivalent to wrap_stdio(stdio.ServerParameters)
# from llm_mcp import wrap_mcp
# tools = wrap_mcp("npx -y @wonderwhy-er/desktop-commander")

# Use the tools with a model
model = get_model("gpt-4.1-nano")
response = model.chain(
    f"Display the text found in the secret.txt file in {os.getcwd()}",
    tools=tools,
)
print(response.text())
```

**Output:**
> The text found in the secret.txt file is: "Why don't pelicans like to tip
> waiters?"

### HTTP Servers

For HTTP-based MCP servers, use the HTTP bridge instead:

```python
from llm import get_model

from llm_mcp import wrap_http, http

tools = wrap_http(http.ServerParameters("https://gitmcp.io/simonw/llm"))

# wrap_mcp(url) is equivalent to wrap_http(http.ServerParameters)
# from llm_mcp import wrap_mcp
# tools = wrap_mcp("https://gitmcp.io/simonw/llm")

model = get_model("gpt-4.1-nano")

response = model.chain(
    "Search llm github for CHANGELOG and display 1 sentence summary of the latest entry.",
    tools=tools,
)
print(response.text())
```

**Output:**
> The latest entry in the changelog (version 0.26a0, dated 2025-05-13)
> introduces alpha support for tools in LLM, allowing models with tool
> capability (including the default OpenAI models) to execute Python functions
> as
> part of responding to a prompt, with usage available in both the command-line
> interface and Python API, and support for defining new tools via plugin
> hooks.
