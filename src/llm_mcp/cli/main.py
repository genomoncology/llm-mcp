import click


@click.group()
@click.version_option()
def mcp():
    """
    Model Context Protocol (MCP) plugin for LLM.

    Plugin Repository: https://github.com/genomoncology/llm-mcp
    `llm` Documentation: https://llm.datasette.io/
    """
