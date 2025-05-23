import os

import pytest
from llm import get_model
from pytest_bdd import given, scenarios, then, when

from llm_mcp import schema, wrap_mcp

scenarios("./stdio/stdio_read_file.feature")

pytestmark = pytest.mark.vcr(record_mode="new_episodes")
API_KEY = os.environ.get("OPENAI_API_KEY", None) or "gm-..."


@given(
    "the desktop-commander is available with directory access",
    target_fixture="tools",
)
def tools(data_dir):
    """Start desktop-commander with --allow pointing at the feature dir."""
    params = schema.StdioServerParameters(
        command="npx",
        args=["-y", "@wonderwhy-er/desktop-commander"],
        cwd=data_dir,
    )
    return wrap_mcp(params)


@when(
    "the assistant is prompted to list the current directory",
    target_fixture="listing_response",
)
def listing_response(tools):
    model = get_model("gpt-4.1-mini")
    return model.chain(
        "List the files in current working directory.",
        tools=tools,
        key=API_KEY,
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
        "Read the secret.txt found here in current directory.",
        tools=tools,
    ).text()


@then("the assistant reply contains the secret text")
def check_secret(response, data_dir):
    secret_file = data_dir / "secret.txt"
    assert secret_file.is_file()
    expected = secret_file.read_text().strip().strip('"').lower()
    assert expected in response.lower()
