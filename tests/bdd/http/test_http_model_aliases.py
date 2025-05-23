import os

import pytest
from llm import get_model
from pydantic import BaseModel
from pytest_bdd import given, parsers, scenarios, then, when

from llm_mcp import schema, wrap_mcp

scenarios("./http/http_model_aliases.feature")

pytestmark = pytest.mark.vcr(record_mode="new_episodes")
API_KEY = os.environ.get("OPENAI_API_KEY", None) or "gm-..."


@given(
    "the HTTP tools for the simonw/llm repository are available",
    target_fixture="tools",
)
def tools():
    params = schema.RemoteServerParameters(url="https://gitmcp.io/simonw/llm")
    return wrap_mcp(params)


class AliasSchema(BaseModel):
    aliases: list[str]


# --------------------------------------------------------------------------- #
# Steps                                                                       #
# --------------------------------------------------------------------------- #


@when(
    parsers.parse('the assistant is asked for the aliases of "{model_name}"'),
    target_fixture="aliases",
)
def aliases(tools, model_name) -> set[str]:
    """
    Ask for aliases, expect a JSON string we validate using Pydantic.
    Some models ignore the `schema=` hint-so we parse manually.
    """
    model = get_model("gpt-4.1")
    response = model.chain(
        (
            "According to the `llm`, what are the aliases for the model "
            f"named '{model_name}'? Respond **only** with JSON formatted as "
            '{"aliases": ["alias1", "alias2", ...]}.'
        ),
        tools=tools,
        stream=False,
        key=API_KEY,
    )
    validated = AliasSchema.model_validate_json(response.text())
    return set(validated.aliases)


@then('the assistant returns aliases including "chatgpt-16k" and "3.5-16k"')
def check_aliases(aliases: set[str]):
    assert {"chatgpt-16k", "3.5-16k"} <= aliases
