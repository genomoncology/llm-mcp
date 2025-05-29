## 1 · Guiding Philosophy

* **Strict layering.**  Every concern (CLI, business logic, transport, persistence, etc.) sits in a single, well-named package.
* **Lean surface area.**  Only the essentials are public; helpers live in `utils` or stay private.
* **Async-from-sync safety.**  A single background event-loop solves the “I’m already inside `asyncio`” problem without leaking coroutines.
* **Statically typed.**  All data objects are Pydantic models; mypy & ruff run on every commit.
* **Predictable I/O.**  Only one module writes to disk (`store.py`); only one module runs network or subprocess calls (`transport/*`).

---

## 2 · Layer-by-Layer Walk-through

### 2.1 CLI (“Ports”)

* **Module:** `src/llm_mcp/cli/*`
* **Tech:** Click 8.x.
* One command group – `llm mcp` – with a single sub-namespace **servers** (`add`, `list`, `view`, `remove`).
* Absolutely *no* business rules inside handlers; they delegate to `manager`.
* Error translation (`ValueError` → `click.ClickException`) is the only logic here.

### 2.2 Plugin Integration Layer

* **Module:** `plugin.py`

* Implements two `llm` entry-point hooks:

  * `register_tools`: converts stored MCP tools into in-memory `llm.Tool` objects.
  * `register_commands`: injects the Click group into LLM’s global CLI.

* This keeps project-specific plumbing out of core logic.

### 2.3 Manager (“Application Service” Layer)

* **Module:** `manager.py`
* Pure business orchestration:

  * Parses parameter strings (`utils.parse_params`).
  * Generates canonical server names (`utils.generate_server_name`).
  * Calls **Transport** to probe a server for tools.
  * Persists the resulting manifest through **Store**.
* Handles duplication rules (`overwrite` vs `exist_ok`).
* Raises a single domain-specific exception (`DuplicateServer`).

### 2.4 Transport Layer

* **Package:** `transport/`

* **Sub-components:**

  * `http.py` – streamable HTTP client built on the official MCP SDK.
  * `stdio.py` – equivalent wrapper for subprocess-style servers.
  * `convert_tool.py` – bridges MCP `Tool` → `llm.Tool`.
  * `dispatch.py` – facade that abstracts away which concrete transport is needed.
  * `bg_runner.py` – **critical utility**: a daemon thread with its own event-loop.

    * Guarantees sync code can await coroutines regardless of existing loops.
    * Registered with `atexit` for guaranteed clean-up.

* Public API is always **blocking** (`*_sync`) so callers never juggle `await`.

### 2.5 Store Layer

* **Module:** `store.py`

* Owns **all** filesystem concerns:

  * `mcp_dir()/servers/…` resolution
  * JSON serialisation via `ServerConfig.model_dump()`
  * Post-load sanitation (`ServerConfig.clean()`)

* Exposes CRUD helpers (`save_server`, `load_server`, `remove_server`, `list_servers`).

* Never performs network I/O or spawns processes – persistence only.

### 2.6 Schema Layer

* **Package:** `schema/`
* Pydantic v2 models wrap every external data contract:

  * `ServerConfig` – server manifest plus helper methods (`get_tool`, `clean`).
  * `RemoteServerParameters` and `StdioServerParameters` – strict validation & helper `.as_kwargs()` conversion.
* Regex patterns and value ranges captured declaratively (e.g. name must match `^[a-z0-9_]+$`).
* This guarantees invalid state cannot propagate past the boundary.

### 2.7 Utils

* **Package:** `utils/` – small, side-effect-free helpers:

  * `parse_params` – string-to-`ServerParameters` parser (supports env-var prefixes, quotes, URLs, etc.).
  * `generate_server_name` – deterministic, human-friendly naming rules.
  * `convert_content` – converts wire-level MCP `Content` objects to plain Python.

* Zero external imports beyond stdlib & Pydantic.

### 2.8 Tests & Tooling

* **Behavioural specs** (pytest-bdd) prove end-to-end flows for both local and remote servers.
* **TDD unit tests** exercise critical utilities (`bg_runner`, schemas, utils).
* **Makefile** provides one-liner targets for `check`, `test`, `cov`, ensuring the same ritual in CI and locally.
* **uv** manages virtualenv + dependency locking, keeping the project reproducible.

## 3 · Why This Structure Works

1. **Separation of concerns is crystal clear.**
   * Changing filesystem layout (e.g., put manifests in SQLite) only touches `store.py`.
   * Adding WebSocket transport touches only `transport/` and `convert_tool`.

2. **Single source of truth for domain rules.**
   `manager` is the authoritative place for “what does it mean to register a server” – no logic duplication in CLI or tests.

3. **Safe sync/async bridging.**
   The background loop eliminates an entire class of “RuntimeError: asyncio.run() cannot be called” bugs while remaining invisible to 90 % of the codebase.

4. **Statically validated data.**
   Pydantic guarantees manifests are sane before they hit disk; `ServerConfig.clean()` enforces further contract tweaks (e.g. stripping unused `annotations`).

5. **Extensibility by composition.**
   New transports, auth schemes, caching layers or CLI namespaces bolt on without ripple effects.

6. **Test friendliness.**
   * Background loop has deterministic startup/teardown (`shutdown()`).

7. **Minimal hidden state.**
   Global singletons (`_bg_loop`) are confined to one module and carefully reset in tests; everywhere else uses pure functions.

---

## 4 · Recommended Conventions (codified in current code)

* **One public function per responsibility.**
* **Never mix concerns inside a module.**
* **Errors bubble up unchanged** until CLI converts them to user-friendly messages.
* **No silent magic.** Explicitly named tool wrappers (`http_tool_<name>`).
* **Tests read like documentation.**

---

## 5 · Conclusion

This pre-toolbox architecture achieves a clean, layered balance:

* **Developer ergonomics** (clear API, predictable layout)
* **Runtime safety** (validated models, background loop)
* **Extensibility** (transport-agnostic, plugin hooks)

Maintaining these principles ensures a robust, maintainable codebase long-term.
