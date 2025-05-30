from __future__ import annotations

import builtins

from .. import store
from ..schema.toolboxes import MCPToolRef, ToolboxConfig, ToolRef
from . import errors as err

_DEFAULT_PATH = store.mcp_dir() / "default_toolbox.txt"


def _write_default(name: str | None) -> None:
    if name is None:
        _DEFAULT_PATH.unlink(missing_ok=True)
    else:
        _DEFAULT_PATH.write_text(name)


def _read_default() -> str | None:
    try:
        return _DEFAULT_PATH.read_text().strip()
    except FileNotFoundError:
        return None


# ───────── CRUD ────────────────────────────────────────────────────
def create(name: str, *, description: str | None = None) -> ToolboxConfig:
    if store.load_toolbox(name):
        raise err.ToolboxExists(f"Toolbox '{name}' already exists")
    cfg = ToolboxConfig(name=name, description=description)
    store.save_toolbox(cfg)
    return cfg


def remove(name: str) -> None:
    if not store.remove_toolbox(name):
        raise err.ToolboxNotFound(f"Toolbox '{name}' not found")
    # clear default if it pointed to this one
    if _read_default() == name:
        _write_default(None)


# `list` shadows the builtin - give it a clear name
def list_toolboxes() -> builtins.list[str]:
    return store.list_toolboxes()


def get_toolbox(name: str) -> ToolboxConfig:
    cfg = store.load_toolbox(name)
    if cfg is None:
        raise err.ToolboxNotFound(f"Toolbox '{name}' not found")
    return cfg


# ───────── Tools inside a toolbox ──────────────────────────────────
def add_tool(tb_name: str, tool: ToolRef) -> ToolboxConfig:
    cfg = get_toolbox(tb_name)
    public_name = (
        tool.name
        or getattr(tool, "tool", None)
        or getattr(tool, "attr", None)
        or getattr(tool, "method", None)
    )
    if public_name is None:
        raise ValueError("Cannot determine public name for tool")
    if any(
        (
            public_name
            == (
                t.name
                or getattr(t, "tool", None)
                or getattr(t, "attr", None)
                or getattr(t, "method", None)
            )
        )
        for t in cfg.tools
    ):
        raise err.ToolExists(
            f"Tool '{public_name}' already exists in '{tb_name}'"
        )
    cfg.tools.append(tool)
    store.save_toolbox(cfg)
    return cfg


def remove_tool(tb_name: str, public_name: str) -> ToolboxConfig:
    cfg = get_toolbox(tb_name)
    new_tools = [
        t
        for t in cfg.tools
        if public_name
        != (
            t.name
            or getattr(t, "tool", None)
            or getattr(t, "attr", None)
            or getattr(t, "method", None)
        )
    ]
    if len(new_tools) == len(cfg.tools):
        raise err.ToolNotFound(
            f"Tool '{public_name}' not found in '{tb_name}'"
        )
    cfg.tools = new_tools
    store.save_toolbox(cfg)
    return cfg


# ───────── Default toolbox helpers ─────────────────────────────────
def set_default(tb_name: str) -> None:
    get_toolbox(tb_name)  # ensure it exists
    _write_default(tb_name)


def clear_default() -> None:
    _write_default(None)


def get_default() -> str | None:
    return _read_default()


# ───────── Validation ─────────────────────────────────────────────
def validate(tb_name: str) -> builtins.list[str]:
    cfg = get_toolbox(tb_name)
    problems: builtins.list[str] = []

    # 1. duplicate names inside toolbox (should not happen, schema prevents)
    seen: set[str] = set()
    for t in cfg.tools:
        n = (
            t.name
            or getattr(t, "tool", None)
            or getattr(t, "attr", None)
            or getattr(t, "method", None)
        )
        if n is None:
            continue
        if n in seen:
            problems.append(f"Duplicate tool name '{n}'")
        seen.add(n)  # n is guaranteed to be str at this point

    # 2. referenced server exists
    from .. import store as _s

    servers = set(_s.list_servers())
    for t in cfg.tools:
        if isinstance(t, MCPToolRef) and t.server not in servers:
            problems.append(f"Server '{t.server}' not found")

    return problems
