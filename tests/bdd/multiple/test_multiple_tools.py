# import os
#
# import pytest
# from llm import get_model
# from pytest_bdd import given, parsers, scenarios, then, when
#
# from llm_mcp import wrap_mcp
#
# scenarios("./multiple/multiple_tools.feature")
#
# pytestmark = pytest.mark.vcr(record_mode="new_episodes")
# API_KEY = os.environ.get("OPENAI_API_KEY", None) or "gm-..."
#
#
# @given(
#     "the desktop-commander and simon/llm tools are loaded",
#     target_fixture="tools",
# )
# def tools():
#     tools = wrap_mcp(
#         "https://gitmcp.io/simonw/llm",
#         "npx -y @wonderwhy-er/desktop-commander",
#     )
#     return tools
#
#
# @when(
#     "I collect the input-schemas of every wrapped tool",
#     target_fixture="schemas",
# )
# def schemas(tools) -> dict[str, dict]:
#     schemas = {t.name: t.input_schema for t in tools}
#     return schemas
#
#
# @then(
#     parsers.parse('the "{tool_name}" tool has a required "{param}" parameter')
# )
# def then_schema_contains(schemas, tool_name: str, param: str):
#     schema = schemas.get(tool_name)
#     assert schema, f"No schema found for {tool_name!r}"
#     required = set(schema.get("required", []))
#     assert (
#         param in required
#     ), f"{param!r} not in required={required} for {tool_name!r}"
#
#
# @when(
#     "the assistant reads the secret joke and finds its punchline",
#     target_fixture="punchline",
# )
# @pytest.mark.vcr()
# def punchline(tools, data_dir):
#     model = get_model("gpt-4.1-mini")
#
#     prompt = f"""
#     Do the following steps exactly:
#     - Use the "read_file" tool to read "secret.txt" found here in {data_dir}.
#     - If you can't read that file, stop immediately and just say "WALRUS!".
#     - Use "search_llm_code" with the secret joke as the query.
#     - From the search results, obtain the URL of the document.
#     - If you cannot find a GitHub URL of the search result just say "MUPPET!".
#     - Use "fetch_generic_url_content" passing it the search result URL.
#     - Say the punchline of the joke exactly without intro, outro or modification.
#     """
#
#     response = model.chain(prompt, tools=tools, stream=False)
#     punchline = response.text().strip()
#     return punchline
#
#
# @then('the punchline is exactly "Because they always have a big bill!"')
# def verify_punchline(punchline):
#     assert "Because they always have a big bill!" in punchline
