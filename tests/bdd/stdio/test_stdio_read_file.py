from pathlib import Path

import pytest
from llm import get_model
from pytest_bdd import given, scenarios, then, when

from llm_mcp import stdio, wrap_stdio

scenarios("./stdio/stdio_read_file.feature")

pytestmark = pytest.mark.vcr(record_mode="new_episodes")

ROOT_DIR = Path(__file__).resolve().parents[3]
SECRET_FILE = ROOT_DIR / "secret.txt"


@given(
    "the desktop-commander is available with directory access",
    target_fixture="tools",
)
def tools():
    """Start desktop-commander with --allow pointing at the feature dir."""
    params = stdio.ServerParameters(
        command="npx", args=["-y", "@wonderwhy-er/desktop-commander"]
    )
    return wrap_stdio(params)


# ── Scenario: directory listing ──────────────────────────────────────────── #


@when(
    "the assistant is prompted to list the current directory",
    target_fixture="listing_response",
)
def listing_response(tools):
    model = get_model("gpt-4.1-mini")
    return model.chain(
        f"List the files in: {ROOT_DIR}",
        tools=tools,
    ).text()


@then('the listing response contains "secret.txt"')
def check_listing(listing_response):
    assert "secret.txt" in listing_response.lower()


# ── Scenario: read file ─────────────────────────────────────────────────── #


@when(
    "the assistant is asked to read the secret.txt file",
    target_fixture="response",
)
def response(tools):
    model = get_model("gpt-4.1-mini")
    return model.chain(
        f"Read the secret.txt found here in {ROOT_DIR}.",
        tools=tools,
    ).text()


@then("the assistant reply contains the secret text")
def check_secret(response):
    assert SECRET_FILE.is_file()
    expected = SECRET_FILE.read_text().strip().strip('"').lower()
    assert expected in response.lower()
