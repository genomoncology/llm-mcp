# llm-mcp

[![Release](https://img.shields.io/github/v/release/imaurer/llm-mcp)](https://img.shields.io/github/v/release/imaurer/llm-mcp)
[![Build status](https://img.shields.io/github/actions/workflow/status/imaurer/llm-mcp/main.yml?branch=main)](https://github.com/imaurer/llm-mcp/actions/workflows/main.yml?query=branch%3Amain)

[LLM](https://llm.datasette.io/) plugin for Model Context Protocol (MCP) support, enabling LLMs to use tools from any MCP server.

## Requirements

- LLM version 0.26 or higher (for tool support)
- Python 3.10+

## Installation

First, install or upgrade LLM to version 0.26+:

```bash
uv tool install llm
# or upgrade if you have it already
uv tool upgrade llm
```

Then install the plugin:

```bash
llm install llm-mcp
```

## Basic Usage

### Adding MCP Servers

Add a remote MCP server:
```bash
llm mcp servers add "https://gitmcp.io/simonw/llm"
✔ added server 'gitmcp_llm' with 4 tools
```

Add a local MCP server via npx:
```bash
llm mcp servers add "npx @wonderwhy-er/desktop-commander"
✔ added server 'desktop_commander' with 18 tools
```

### Managing Servers

List servers:
```bash
llm mcp servers list
```

View server details:
```bash
llm mcp servers view gitmcp_llm
```

Remove a server:
```bash
llm mcp servers remove gitmcp_llm
```

### Using Tools

Once a server is added, its tools become available to use with any LLM model:

```bash
# Use a single tool
llm -T read_file "What is the secret word in secret.txt?"

# Use multiple tools
llm -T search_llm_documentation -T fetch_generic_url_content \
  "Find docs for how to specify a schema in llm project"

# Debug mode to see tool calls
llm -T tool_name "your prompt" --td
```

## Roadmap to v0.1

- ✅ v0.0.2 - Basic MCP server management and tool usage
  - `llm mcp servers` for add, list, view
  - Convert MCP tools to LLM tools
  - Support for stdio and HTTP servers

- 🚧 v0.1.0 - Initial Checklist
  - Remote server authentication (tokens, OAuth)
  - `llm mcp toolboxes` - create and manage tool collections
  - Support vanilla Python functions as tools
  - `llm mcp proxy` - start MCP proxy server for toolboxes
  - Proxy authentication
  - True async support

## Resources

- [Simon Willison's blog post on LLM 0.26 tool support](https://simonwillison.net/2025/May/27/llm-tools/)
- [LLM Tools documentation](https://llm.datasette.io/en/stable/tools.html)
- [Model Context Protocol](https://modelcontextprotocol.io/)

## Safety Warning

⚠️ **Tools can be dangerous!** Be careful about which tools you enable when working with untrusted content. See the [LLM tools documentation](https://llm.datasette.io/en/stable/tools.html#tools-can-be-dangerous) for important security considerations.
