import asyncio
from collections.abc import Generator
from typing import Any

import pytest

from llm_mcp import bg_runner


async def _add(a: int, b: int) -> int:  # helper coroutine
    return a + b


def test_run_async_outside_loop() -> None:
    """Calling from sync code should just work."""
    assert bg_runner.run_async(_add(1, 2)) == 3


def test_run_async_inside_loop() -> None:
    """Calling from *within* an event-loop should also work."""

    async def _inner() -> int:
        return bg_runner.run_async(_add(2, 3))

    assert asyncio.run(_inner()) == 5


def test_background_loop_singleton() -> None:
    """Multiple calls share the same background loop & thread."""
    # First call - initialises the loop/thread.
    bg_runner.run_async(_add(0, 0))
    loop1 = bg_runner._bg_loop  # type: ignore[attr-defined]
    thread1 = bg_runner._bg_thread  # type: ignore[attr-defined]

    # Second call - should reuse the same resources.
    bg_runner.run_async(_add(1, 1))
    assert bg_runner._bg_loop is loop1  # type: ignore[attr-defined]
    assert bg_runner._bg_thread is thread1  # type: ignore[attr-defined]


def test_shutdown_resets_globals() -> None:
    bg_runner.shutdown()
    assert bg_runner._bg_loop is None  # type: ignore[attr-defined]
    assert bg_runner._bg_thread is None  # type: ignore[attr-defined]

    # It should be possible to use run_async() again afterwards.
    assert bg_runner.run_async(_add(4, 5)) == 9

    # Clean up once more so we leave no dangling threads for other tests.
    bg_runner.shutdown()


@pytest.fixture(scope="session", autouse=True)
def _bg_cleanup() -> Generator[None, Any, None]:
    """Ensure the background loop is gone at the end of the test session."""
    yield
    bg_runner.shutdown()
