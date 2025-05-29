# LLM Tools

(tools)=

# Tools

Many Large Language Models have been trained to execute tools as part of
responding to a prompt. LLM supports tool usage with both the command-line
interface and the Python API.

Exposing tools to LLMs **carries risks**! Be sure to read the {ref}
`warning below <tools-warning>`.

(tools-how-they-work)=

## How tools work

A tool is effectively a function that the model can request to be executed.
Here's how that works:

1. The initial prompt to the model includes a list of available tools,
   containing their names, descriptions and parameters.
2. The model can choose to call one (or sometimes more than one) of those
   tools, returning a request for the tool to execute.
3. The code that calls the model - in this case LLM itself - then executes the
   specified tool with the provided arguments.
4. LLM prompts the model a second time, this time including the output of the
   tool execution.
5. The model can then use that output to generate its next response.

This sequence can run several times in a loop, allowing the LLM to access data,
act on that data and then pass that data off to other tools for further
processing.

:::{admonition} Tools can be dangerous
:class: danger

(tools-warning)=

## Warning: Tools can be dangerous

Applications built on top of LLMs suffer from a class of attacks
called [prompt injection](https://simonwillison.net/tags/prompt-injection/)
attacks. These occur when a malicious third party injects content into the LLM
which causes it to take tool-based actions that act against the interests of
the user of that application.

Be very careful about which tools you enable when you potentially might be
exposed to untrusted sources of content - web pages, GitHub issues posted by
other people, email and messages that have been sent to you that could come
from an attacker.

Watch out for the **lethal trifecta** of prompt injection exfiltration attacks.
If your tool-enabled LLM has the following:

- access to private data
- exposure to malicious instructions
- the ability to exfiltrate information

Anyone who can feed malicious instructions into your LLM - by leaving them on a
web page it visits, or sending an email to an inbox that it monitors - could be
able to trick your LLM into using other tools to access your private
information and then exfiltrate (pass out) that data to somewhere the attacker
can see it.
:::

(tools-trying-out)=

## Trying out tools

LLM comes with a default tool installed, called `llm_version`. You can try that
out like this:

```bash
llm --tool llm_version "What version of LLM is this?" --td
```

You can also use `-T llm_version` as a shortcut for `--tool llm_version`.

The output should look like this:

```
Tool call: llm_version({})
  0.26a0

The installed version of the LLM is 0.26a0.
```

Further tools can be installed using plugins, or you can use the
`llm --functions` option to pass tools implemented as PYthon functions
directly, as {ref}`described here <usage-tools>`.

(tools-implementation)=

## LLM's implementation of tools

In LLM every tool is a defined as a Python function. The function can take any
number of arguments and can return a string or an object that can be converted
to a string.

Tool functions should include a docstring that describes what the function
does. This docstring will become the description that is passed to the model.

Tools can also be defined as {ref}`toolbox classes <python-api-toolbox>`, a
subclass of `llm.Toolbox` that allows multiple related tools to be bundled
together. Toolbox classes can be be configured when they are instantiated, and
can also maintain state in between multiple tool calls.

The Python API can accept functions directly. The command-line interface has
two ways for tools to be defined: via plugins that implement the {ref}
`register_tools() plugin hook <plugin-hooks-register-tools>`, or directly on
the command-line using the `--functions` argument to specify a block of Python
code defining one or more functions - or a path to a Python file containing the
same.

You can use tools {ref}`with the LLM command-line tool <usage-tools>` or {ref}
`with the Python API <python-api-tools>`.

(tools-default)=

## Default tools

LLM includes some default tools for you to try out:

- `llm_version()` returns the current version of LLM
- `llm_time()` returns the current local and UTC time

Try them like this:

```bash
llm -T llm_version -T llm_time 'Give me the current time and LLM version' --td
```

(tools-tips)=

## Tips for implementing tools

Consult the {ref}`register_tools() plugin hook <plugin-hooks-register-tools>`
documentation for examples of how to implement tools in plugins.

If your plugin needs access to API secrets I recommend storing those using
`llm keys set api-name` and then reading them using the {ref}
`plugin-utilities-get-key` utility function. This avoids secrets being logged
to the database as part of tool calls.

# Simon Willison Blog Announcement (1)

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
import asyncio
from click.testing import CliRunner
from importlib.metadata import version
import json
import llm
from llm import cli
from llm.migrations import migrate
from llm.tools import llm_time
import os
import pytest
import sqlite_utils
import time


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
    assert tools[0]["plugin"] is None

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


def test_tool_use_async_tool_function():
    async def hello():
        return "world"

    model = llm.get_model("echo")
    chain_response = model.chain(
        json.dumps({"tool_calls": [{"name": "hello"}]}), tools=[hello]
    )
    output = chain_response.text()
    # That's two JSON objects separated by '\n}{\n'
    bits = output.split("\n}{\n")
    assert len(bits) == 2
    objects = [json.loads(bits[0] + "}"), json.loads("{" + bits[1])]
    assert objects == [
        {"prompt": "", "system": "", "attachments": [], "stream": True, "previous": []},
        {
            "prompt": "",
            "system": "",
            "attachments": [],
            "stream": True,
            "previous": [{"prompt": '{"tool_calls": [{"name": "hello"}]}'}],
            "tool_results": [
                {"name": "hello", "output": "world", "tool_call_id": None}
            ],
        },
    ]


@pytest.mark.asyncio
async def test_async_tools_run_tools_in_parallel():
    start_timestamps = []

    start_ns = time.monotonic_ns()

    async def hello():
        start_timestamps.append(("hello", time.monotonic_ns() - start_ns))
        await asyncio.sleep(0.2)
        return "world"

    async def hello2():
        start_timestamps.append(("hello2", time.monotonic_ns() - start_ns))
        await asyncio.sleep(0.2)
        return "world2"

    model = llm.get_async_model("echo")
    chain_response = model.chain(
        json.dumps({"tool_calls": [{"name": "hello"}, {"name": "hello2"}]}),
        tools=[hello, hello2],
    )
    output = await chain_response.text()
    # That's two JSON objects separated by '\n}{\n'
    bits = output.split("\n}{\n")
    assert len(bits) == 2
    objects = [json.loads(bits[0] + "}"), json.loads("{" + bits[1])]
    assert objects == [
        {"prompt": "", "system": "", "attachments": [], "stream": True, "previous": []},
        {
            "prompt": "",
            "system": "",
            "attachments": [],
            "stream": True,
            "previous": [
                {"prompt": '{"tool_calls": [{"name": "hello"}, {"name": "hello2"}]}'}
            ],
            "tool_results": [
                {"name": "hello", "output": "world", "tool_call_id": None},
                {"name": "hello2", "output": "world2", "tool_call_id": None},
            ],
        },
    ]
    delta_ns = start_timestamps[1][1] - start_timestamps[0][1]
    # They should have run in parallel so it should be less than 0.02s difference
    assert delta_ns < (100_000_000 * 0.2)


@pytest.mark.asyncio
async def test_async_toolbox():
    class Tools(llm.Toolbox):
        async def go(self):
            return "This was async"

    model = llm.get_async_model("echo")
    chain_response = model.chain(
        json.dumps({"tool_calls": [{"name": "Tools_go"}]}),
        tools=[Tools()],
    )
    output = await chain_response.text()
    assert '"output": "This was async"' in output


@pytest.mark.vcr
def test_conversation_with_tools(vcr):
    import llm

    def add(a: int, b: int) -> int:
        return a + b

    def multiply(a: int, b: int) -> int:
        return a * b

    model = llm.get_model("echo")
    conversation = model.conversation(tools=[add, multiply])

    output1 = conversation.chain(
        json.dumps(
            {"tool_calls": [{"name": "multiply", "arguments": {"a": 5324, "b": 23233}}]}
        )
    ).text()
    assert "123692492" in output1
    output2 = conversation.chain(
        json.dumps(
            {
                "tool_calls": [
                    {"name": "add", "arguments": {"a": 841758375, "b": 123123}}
                ]
            }
        )
    ).text()
    assert "841881498" in output2


def test_default_tool_llm_version():
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        [
            "-m",
            "echo",
            "-T",
            "llm_version",
            json.dumps({"tool_calls": [{"name": "llm_version"}]}),
        ],
    )
    assert result.exit_code == 0
    assert '"output": "{}"'.format(version("llm")) in result.output


def test_functions_tool_locals():
    # https://github.com/simonw/llm/issues/1107
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        [
            "-m",
            "echo",
            "--functions",
            "my_locals = locals",
            "-T",
            "llm_version",
            json.dumps({"tool_calls": [{"name": "locals"}]}),
        ],
    )
    assert result.exit_code == 0


def test_default_tool_llm_time():
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        [
            "-m",
            "echo",
            "-T",
            "llm_time",
            json.dumps({"tool_calls": [{"name": "llm_time"}]}),
        ],
    )
    assert result.exit_code == 0
    assert "timezone_offset" in result.output

    # Test it by calling it directly
    info = llm_time()
    assert set(info.keys()) == {
        "timezone_offset",
        "utc_time_iso",
        "local_time",
        "local_timezone",
        "utc_time",
        "is_dst",
    }


def test_incorrect_tool_usage():
    model = llm.get_model("echo")

    def simple(name: str):
        return name

    chain_response = model.chain(
        json.dumps({"tool_calls": [{"name": "bad_tool"}]}),
        tools=[simple],
    )
    output = chain_response.text()
    assert 'Error: tool \\"bad_tool\\" does not exist' in output
```
