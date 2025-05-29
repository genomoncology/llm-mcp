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
import contextlib
import logging
import os
import threading
import warnings
from collections.abc import Coroutine
from typing import Any, TypeVar, cast

# Get configuration from environment variables
TASK_CLEANUP_TIMEOUT = float(
    os.environ.get("LLM_MCP_TASK_CLEANUP_TIMEOUT", "1.0")
)
THREAD_JOIN_TIMEOUT = float(
    os.environ.get("LLM_MCP_THREAD_JOIN_TIMEOUT", "2.0")
)

logger = logging.getLogger(__name__)

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


def _cancel_pending_tasks(loop: asyncio.AbstractEventLoop) -> None:
    """Cancel all pending tasks on the given event loop."""
    # Get all running tasks
    pending_tasks = asyncio.all_tasks(loop)
    if not pending_tasks:
        return

    # Skip the current task that's doing the cancelling
    current_task = asyncio.current_task(loop)
    if current_task is not None:
        pending_tasks.discard(current_task)

    # Cancel all remaining tasks
    for task in pending_tasks:
        task.cancel()

    # Create a task to handle the cancellations
    async def wait_for_cancellations():
        # Wait briefly for tasks to acknowledge cancellation
        # Use contextlib.suppress to ignore expected exceptions
        with contextlib.suppress(TimeoutError, asyncio.CancelledError):
            # Use wait_for with a timeout to avoid hanging if tasks don't respond
            await asyncio.wait_for(
                asyncio.gather(*pending_tasks, return_exceptions=True),
                timeout=TASK_CLEANUP_TIMEOUT,  # Time for tasks to clean up
            )

    # Schedule the cleanup task
    loop.create_task(wait_for_cancellations())


def shutdown(*_exc: object) -> None:
    """Stop the background loop and join its thread (idempotent).

    Cancels all pending tasks before stopping the loop to ensure
    proper cleanup of resources.
    """
    global _bg_loop, _bg_thread
    with _bg_lock:
        if _bg_loop is None:
            return

        # Define a function to cancel all pending tasks and stop the loop
        def cleanup_and_stop():
            # We know _bg_loop can't be None here, but mypy needs explicit check
            loop = _bg_loop
            if loop is None:
                # This should never happen but protects against runtime errors
                raise RuntimeError(
                    "Background loop was unexpectedly None during cleanup"
                )

            # Cancel all tasks first
            _cancel_pending_tasks(loop)

            # Then stop the loop
            loop.stop()

        # Schedule our cleanup function to run in the event loop
        _bg_loop.call_soon_threadsafe(cleanup_and_stop)

        # Wait for thread to complete
        if _bg_thread is not None and _bg_thread.is_alive():
            _bg_thread.join(timeout=THREAD_JOIN_TIMEOUT)

            # Check if thread is still alive after timeout
            if _bg_thread.is_alive():
                warnings.warn(
                    f"Background thread didn't exit within {THREAD_JOIN_TIMEOUT}s timeout. "
                    f"Some tasks may be abandoned. Set LLM_MCP_THREAD_JOIN_TIMEOUT to increase wait time.",
                    stacklevel=2,
                )

        # Reset globals
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
