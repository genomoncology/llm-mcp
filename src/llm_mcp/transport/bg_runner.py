"""
Background event-loop utilities for *llm-mcp*.

Exactly one private asyncio event-loop is started lazily in a separate
thread, so *synchronous* code can obtain the result of an *awaitable*
-even when it is already running inside another event-loop-by calling
:pyfunc:`run_async`.

Key guarantees
--------------
* **Thread-safe singleton** - the background loop and its thread are
  created once and reused by every caller.
* **Transparent teardown** - :pyfunc:`shutdown` stops the loop, joins
  the thread and sets the globals back to *None*.  It is registered with
  ``atexit`` and can also be called explicitly from test fixtures.
* **Dead-simple API** - one public helper (`run_async`) plus the optional
  `shutdown()` for cleanup-sensitive environments such as `pytest -x`.
"""

from __future__ import annotations

import asyncio
import atexit
import concurrent.futures
import threading
from collections.abc import Coroutine
from typing import Any, TypeVar, cast

T = TypeVar("T")

_bg_loop: asyncio.AbstractEventLoop | None = None
_bg_thread: threading.Thread | None = None
_bg_lock = threading.Lock()


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """Execute *coro* and return its result, regardless of loop state.

    * **No running loop** -> just :pyfunc:`asyncio.run`.
    * **Inside a running loop** -> schedule *coro* on the background
      loop returned by :pyfunc:`_ensure_loop` and block the *current*
      thread on :pyfunc:`concurrent.futures.Future.result`.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    loop = _ensure_loop()
    fut: concurrent.futures.Future[Any] = asyncio.run_coroutine_threadsafe(
        coro, loop
    )
    return cast(T, fut.result())


def shutdown(*_exc: object) -> None:
    """Stop the background loop and join its thread (idempotent)."""
    global _bg_loop, _bg_thread
    with _bg_lock:
        if _bg_loop is None:
            return

        # Ask the loop to stop, then wait up to ~2 s for the thread.
        # noinspection PyTypeChecker
        _bg_loop.call_soon_threadsafe(_bg_loop.stop)
        if _bg_thread is not None and _bg_thread.is_alive():
            _bg_thread.join(timeout=2)

        _bg_loop = _bg_thread = None


# Automatically clean up on interpreter shutdown.
atexit.register(shutdown)


def _ensure_loop() -> asyncio.AbstractEventLoop:
    """Return the background loop, creating it on first use (thread-safe)."""
    global _bg_loop, _bg_thread

    # Fast-path: already initialised - no locking necessary.
    if _bg_loop is not None:
        return _bg_loop  # pragma: no cover

    # First caller takes the lock and creates the resources.
    with _bg_lock:
        if _bg_loop is None:
            _bg_loop = asyncio.new_event_loop()

            def _runner() -> None:
                _bg_loop.run_forever()

            _bg_thread = threading.Thread(
                target=_runner,
                name="llm-mcp-bg",
                daemon=True,
            )
            _bg_thread.start()

        return _bg_loop
