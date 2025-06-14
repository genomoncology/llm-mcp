# Simon Willison Blog Announcement

LLM 0.26a0 adds support for tools! It's only an alpha so I'm not going to
promote this extensively yet, but my LLM project just grew a feature I've been
working towards for nearly two years now: tool support!

I'm presenting a workshop about Building software on top of Large Language
Models at PyCon US tomorrow and this was the one feature I really needed to
pull everything else together.

Tools can be used from the command-line like this (inspired by sqlite-utils
--functions):

llm --functions '
def multiply(x: int, y: int) -> int:
"""Multiply two numbers."""
return x * y
' 'what is 34234 * 213345' -m o4-mini
You can add --tools-debug (shortcut: --td) to have it show exactly what tools
are being executed and what came back. More documentation here.

It's also available in the Python library:

import llm

def multiply(x: int, y: int) -> int:
"""Multiply two numbers."""
return x * y

model = llm.get_model("gpt-4.1-mini")
response = model.chain(
"What is 34234 * 213345?",
tools=[multiply]
)
print(response.text())
There's also a new plugin hook so plugins can register tools that can then be
referenced by name using llm --tool name_of_tool "prompt".

There's still a bunch I want to do before including this in a stable release,
most notably adding support for Python asyncio. It's a pretty exciting start
though!

llm-anthropic 0.16a0 and llm-gemini 0.20a0 add tool support for Anthropic and
Gemini models, depending on the new LLM alpha.
"""

## Example Tests (simonw/llm)

```python
import llm
from llm.migrations import migrate
import os
import pytest
import sqlite_utils


API_KEY = os.environ.get("PYTEST_OPENAI_API_KEY", None) or "badkey"


@pytest.mark.vcr
def test_tool_use_basic(vcr):
    model = llm.get_model("gpt-4o-mini")

    def multiply(a: int, b: int) -> int:
        """Multiply two numbers."""
        return a * b

    chain_response = model.chain("What is 1231 * 2331?", tools=[multiply], key=API_KEY)

    output = "".join(chain_response)

    assert output == "The result of \\( 1231 \\times 2331 \\) is \\( 2,869,461 \\)."

    first, second = chain_response._responses

    assert first.prompt.prompt == "What is 1231 * 2331?"
    assert first.prompt.tools[0].name == "multiply"

    assert len(second.prompt.tool_results) == 1
    assert second.prompt.tool_results[0].name == "multiply"
    assert second.prompt.tool_results[0].output == "2869461"

    # Test writing to the database
    db = sqlite_utils.Database(memory=True)
    migrate(db)
    chain_response.log_to_db(db)
    assert set(db.table_names()).issuperset(
        {"tools", "tool_responses", "tool_calls", "tool_results"}
    )

    responses = list(db["responses"].rows)
    assert len(responses) == 2
    first_response, second_response = responses

    tools = list(db["tools"].rows)
    assert len(tools) == 1
    assert tools[0]["name"] == "multiply"
    assert tools[0]["description"] == "Multiply two numbers."

    tool_results = list(db["tool_results"].rows)
    tool_calls = list(db["tool_calls"].rows)

    assert len(tool_calls) == 1
    assert tool_calls[0]["response_id"] == first_response["id"]
    assert tool_calls[0]["name"] == "multiply"
    assert tool_calls[0]["arguments"] == '{"a": 1231, "b": 2331}'

    assert len(tool_results) == 1
    assert tool_results[0]["response_id"] == second_response["id"]
    assert tool_results[0]["output"] == "2869461"
    assert tool_results[0]["tool_call_id"] == tool_calls[0]["tool_call_id"]


@pytest.mark.vcr
def test_tool_use_chain_of_two_calls(vcr):
    model = llm.get_model("gpt-4o-mini")

    def lookup_population(country: str) -> int:
        "Returns the current population of the specified fictional country"
        return 123124

    def can_have_dragons(population: int) -> bool:
        "Returns True if the specified population can have dragons, False otherwise"
        return population > 10000

    chain_response = model.chain(
        "Can the country of Crumpet have dragons? Answer with only YES or NO",
        tools=[lookup_population, can_have_dragons],
        stream=False,
        key=API_KEY,
    )

    output = chain_response.text()
    assert output == "YES"
    assert len(chain_response._responses) == 3

    first, second, third = chain_response._responses
    assert first.tool_calls()[0].arguments == {"country": "Crumpet"}
    assert first.prompt.tool_results == []
    assert second.prompt.tool_results[0].output == "123124"
    assert second.tool_calls()[0].arguments == {"population": 123124}
    assert third.prompt.tool_results[0].output == "true"
    assert third.tool_calls() == []
```

## Example Tests (simonw/llm-gemini)

```python
from click.testing import CliRunner
import llm
from llm.cli import cli
import nest_asyncio
import json
import os
import pytest
import pydantic
from llm_gemini import cleanup_schema

@pytest.mark.vcr
def test_tools():
    model = llm.get_model("gemini-2.0-flash")
    names = ["Charles", "Sammy"]
    chain_response = model.chain("Two names for a pet pelican",
        tools=[llm.Tool.function(lambda: names.pop(0), name="pelican_name_generator")],
        key=GEMINI_API_KEY,
    )
    text = chain_response.text()
    assert text == "Okay, here are two names for a pet pelican: Charles and Sammy.\n"

    assert len(chain_response._responses) == 3
    first, second, third = chain_response._responses
    assert len(first.tool_calls()) == 1
    assert first.tool_calls()[0].name == "pelican_name_generator"
    assert len(second.tool_calls()) == 1
    assert second.tool_calls()[0].name == "pelican_name_generator"
    assert second.prompt.tool_results[0].output == "Charles"
    assert third.prompt.tool_results[0].output == "Sammy"
```
