# llm-mcp Client Architecture

> **Goal:** Provide Python applications with a simple, robust, and
> native-feeling interface to communicate with Model-Context-Protocol (MCP)
> servers, regardless of whether the caller is synchronous (CLI scripts, Django)
> or asynchronous (FastAPI, Jupyter).

---

## 1. Design Principles

Our client architecture follows these guiding principles:

* **Minimal complexity:** Keep the API surface small and intuitive.
* **Consistency:** Provide a unified API for different transports (HTTP, stdio,
  etc.).
* **Safe concurrency:** Ensure that synchronous callers can safely interact
  with async MCP servers without risk of deadlocks.
* **Testability:** Facilitate simple and fast unit tests without external
  dependencies.

---

## 2. High-Level Overview

The client implementation comprises a few focused modules:

| Layer                    | Purpose                                                                  | Key Symbols                                 |
|--------------------------|--------------------------------------------------------------------------|---------------------------------------------|
| **transport adapters**   | Simple wrappers that abstract MCP server transports                      | `stdio.py`, `http.py`                       |
| **background loop**      | Single background event-loop to safely run async code from sync contexts | `run_async()`                               |
| **conversion utilities** | Transform raw MCP data to native Python objects                          | `convert_content()`                         |
| **tool wrappers**        | Wrap MCP server tools for easy integration with the `llm` library        | `wrap_stdio()`, `wrap_http()`, `wrap_mcp()` |

This clear separation of concerns makes it easy to add new transports or
enhance functionality with minimal changes.

---

## 3. Solving the Async-to-Sync Problem

### Why is this necessary?

Python codebases often have mixed contexts:

* **Async contexts:** FastAPI, Starlette, Jupyter, or asyncio-based scripts
  already run their own event loops.
* **Sync contexts:** CLI scripts, Django views, or other traditional blocking
  codebases cannot directly run async code.

Running `asyncio.run()` within an existing loop raises errors, and alternatives
like global monkey-patching (`nest_asyncio`) introduce unpredictability and
complexity.

### Our solution: Single Background Loop

We address this by creating a small utility (`bg_runner.run_async()`) that:

* **Checks** if an event loop is already running.
* **Uses** a singleton background thread with its own event loop, safely
  running async tasks from any sync context.
* **Ensures safe cleanup** with `atexit` handlers, avoiding resource leaks.

This design choice is critical for robustness, simplicity, and maintaining
compatibility with various hosting environments (CLI, Jupyter, web apps).

---

## 4. Transport Adapters

We offer straightforward modules for connecting to MCP servers:

### `stdio.py`

* Creates a new stdio connection per call, ideal for CLI apps or short-lived
  processes.
* Internally leverages our background event loop to handle async operations
  transparently.

### `http.py`

* Provides synchronous interfaces to HTTP-based MCP servers.
* Converts user-friendly parameters to MCP-compatible structures seamlessly.

Both adapters use `convert_content()` to automatically translate MCP-specific
data formats into plain Python types, simplifying client-side processing.

---

## 5. Tool Wrappers for the `llm` Library

`wrap.py` bridges MCP servers to Simon Willison's `llm` library by:

* Fetching tool metadata from MCP servers.
* Dynamically generating Python-callable tools that match `llm.Tool`
  signatures, ready for immediate use.

Example usage:

```python
from llm_mcp import wrap_mcp, wrap_stdio, wrap_http

# Wrap tools from both stdio and HTTP servers
tools = wrap_mcp(
    "https://gitmcp.io/simonw/llm",
    "npx -y @wonderwhy-er/desktop-commander",
)

# Or individually:
stdio_tools = wrap_stdio(stdio_params)
http_tools = wrap_http(http_params)
```

This approach makes MCP server tools feel native within the `llm` ecosystem,
greatly simplifying integration.

---

## 6. Error Handling Philosophy

We transparently propagate errors without hiding them behind custom wrappers or
vague exceptions:

* Authentication or server errors (`401`, network issues) raise immediately
  clear exceptions.
* Misconfigured servers (e.g., lacking expected permissions) surface their
  issues directly at call-time, simplifying debugging.

---

## 7. Testing Strategy

* **Unit tests:** Mock transport layers with simple async fixtures. No network
  or subprocesses required.
* **BDD integration tests:** Optionally test real MCP servers (like
  `desktop-commander`) through behavior-driven scenarios, ensuring integration
  correctness without compromising fast iteration.
* Background loop cleanup is always automated, ensuring tests remain isolated,
  repeatable, and resource-clean.

---

## 8. Extensibility

Designed from the start for easy extensibility:

| Feature                | Extension Point                              |
|------------------------|----------------------------------------------|
| **New transports**     | Create simple adapters similar to `stdio.py` |
| **OAuth/auth flows**   | Integrate easily into existing HTTP adapters |
| **New MCP data types** | Extend `convert_content()`                   |
| **Custom caching**     | Wrap existing `call_tool_sync()` safely      |

---

## 9. Key Takeaways

* **Unified and Safe:** One background event loop for both sync and async
  contexts, eliminating complexity and potential runtime errors.
* **Transport-Agnostic:** Simple adapters make it trivial to add support for
  new MCP server transports.
* **Minimal Magic:** Straightforward Python code makes debugging, testing, and
  contributing easy.

Our architecture prioritizes simplicity, clarity, and robustness, enabling
smooth integration of MCP functionality into Python projects of any type.
