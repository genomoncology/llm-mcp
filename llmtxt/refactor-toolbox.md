Below is a **churn-aware roadmap**—eight concrete tasks that move the repo from
today’s state to fully-functioning **Toolboxes**. For each task I call out how
it *should* affect the green CI bar, so the developer knows when a failure is
expected vs. a red flag.

---

## 🗺️ High-level task list (8 steps)

| #     | Task                                                                                                                                            | Main folders touched                                | Expected CI colour 🟢/🟡/🔴                       | Notes on test churn                                                      |
|-------|-------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------|---------------------------------------------------|--------------------------------------------------------------------------|
| **1** | **Schema + Store groundwork**<br>• land `schema/toolboxes.py` (new models)<br>• add persistence helpers in `store.py`<br>• unit-tests only      | `src/llm_mcp/schema/`, `store.py`, `tests/tdd/`     | 🟢 should stay green                              | nothing in production path → no existing tests break                     |
| **2** | **Manager CRUD**<br>• `manager.toolboxes.*` funcs for create/read/update/delete<br>• raise typed errors (`DuplicateToolbox`, `ToolboxNotFound`) | `manager.py`, `tests/tdd/`                          | 🟢                                                | only new tests added                                                     |
| **3** | **CLI subgroup** (`llm mcp toolboxes …`) implementing CRUD                                                                                      | `cli/toolboxes.py`, `tests/bdd/toolboxes/`          | 🟡 (BDD features will **fail** until implemented) | mark new BDD features `@xfail` in the same PR—flip to green in this task |
| **4** | **Activation engine**<br>• persist “active” list in `store`<br>• add `activate/deactivate` manager + CLI commands                               | `store.py`, `manager.py`, `cli/toolboxes.py`        | 🟡                                                | add new BDD that is xfailed until plugin hookup                          |
| **5** | **Plugin hookup** – during `register_tools` merge active toolbox tools with server tools                                                        | `plugin.py`, `transport/convert_tool.py` (resolver) | 🔴 until it all wires up, then back to 🟢         | existing suite *must* pass again here—if not, something regressed        |
| **6** | **Name-collision protection** <br>conflicting tool names across servers/toolboxes trigger clear error                                           | `manager.py` & helpers                              | 🟢                                                | only new negative tests                                                  |
| **7** | **Reference validation layer** <br>manager refuses to save a toolbox if any `ToolRef` can’t resolve                                             | `transport/dispatch.py`, `manager.py`, unit tests   | 🟢                                                | relies on existing dispatch code; no behavioural change for happy path   |
| **8** | **Docs + DX polish** <br>update architecture doc, CLI help, examples                                                                            | `docs/`, `README.md`, `Makefile`                    | 🟢                                                | doc-only; CI should stay green                                           |

> **Legend**
> 🟢 – CI should stay green. Any red == real bug.
> 🟡 – Temporary yellow: new tests are added *failing or xfailed* and turn green
> in the *same* task.
> 🔴 – Acceptable to break the build briefly on feature branches but **must end
green before merge to main**.

---

## 🎯 Task 1 — **Schema & Store groundwork**

**Goal:** Land the data structures + persistence API for toolboxes without
touching any runtime behaviour.

### 1-A  Schema

1. **Add file** `src/llm_mcp/schema/toolboxes.py` — use the model we agreed
   on (already committed as `new_toolbox.py`; rename & import).
2. **Export symbols**

   ```python
   # src/llm_mcp/schema/__init__.py
   from .toolboxes import ToolboxConfig, ToolRef  # + keep existing exports
   __all__.extend(["ToolboxConfig", "ToolRef"])
   ```

### 1-B  Store helpers

```python
# src/llm_mcp/store.py  (add at bottom)

# --- DIRECTORY HELPERS ---------------------------------------------------- #

def toolboxes_dir() -> Path:
    path = mcp_dir() / "toolboxes"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _toolbox_path(name: str) -> Path:
    return toolboxes_dir() / f"{name}.json"


# --- CRUD API ------------------------------------------------------------- #

def save_toolbox(cfg: schema.ToolboxConfig) -> Path:
    cfg_json = cfg.model_dump_json(indent=2, exclude_defaults=True)
    path = _toolbox_path(cfg.name)
    path.write_text(cfg_json)
    return path


def load_toolbox(name: str) -> schema.ToolboxConfig | None:
    path = _toolbox_path(name)
    if not path.exists():
        return None
    return schema.ToolboxConfig.model_validate_json(path.read_text())


def remove_toolbox(name: str) -> bool:
    try:
        _toolbox_path(name).unlink()
        return True
    except FileNotFoundError:
        return False


def list_toolboxes() -> list[str]:
    return [p.stem for p in toolboxes_dir().glob("*.json")]
```

*No changes to existing server helpers → zero risk of regressions.*

### 1-C  Unit tests (`tests/tdd/test_toolbox_store.py`)

```python
from llm_mcp import schema, store


def _sample_cfg():
    return schema.ToolboxConfig(
        name="fs_tools",
        description="Filesystem helpers",
        tools=[
            schema.MCPToolRef(server="desktop_commander", tool="read_file")
        ],
    )


def test_roundtrip(tmp_path, monkeypatch):
    # isolate MCP dir
    monkeypatch.setenv("LLM_USER_PATH", str(tmp_path))
    cfg = _sample_cfg()
    store.save_toolbox(cfg)
    loaded = store.load_toolbox("fs_tools")
    assert loaded == cfg
    assert "fs_tools" in store.list_toolboxes()
    assert store.remove_toolbox("fs_tools") is True
    assert store.load_toolbox("fs_tools") is None
```

### 1-D  Mypy & Ruff

* Add `schema/toolboxes.py` to `tool.mypy.files` glob (already `src/**` so
  nothing to do).
* Run `make check`; fix any lint.

### 1-E  CI expectation

*All existing tests plus the new one must pass.*
If CI turns red here, it’s a real break—stop and fix.

---

### Deliverable recap for Task 1

* [ ] `schema/toolboxes.py` with final models
* [ ] `store.py` CRUD helpers & directory utils
* [ ] Unit-test file with round-trip coverage
* [ ] Updated `schema/__init__.py`, green Ruff + mypy

Once this lands on `main`, downstream tasks can build new features without
touching these contracts—**minimising cascading test churn**.
