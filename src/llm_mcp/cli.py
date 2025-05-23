import click
from click_default_group import DefaultGroup
from llm import cli as llm_cli


@click.group(
    cls=DefaultGroup,
    default="serve",
    default_if_no_args=True,
)
@click.version_option()
def mcp():
    """
    Model Context Protocol (MCP) plugin for LLM.

    Plugin Repository: https://github.com/genomoncology/llm-mcp
    `llm` Documentation: https://llm.datasette.io/
    """


@mcp.command(name="serve")
@click.argument("group_name", required=False)
def serve(group_name: str):
    click.echo(f"MCP serve called: {group_name}")


# add option to `prompt` command

llm_cli.prompt.params.append(
    click.Option(
        ("--greeting", "-g"),
        is_flag=True,
        help="Say hello before running the real command",
        expose_value=True,
    ),
)

original_callback = llm_cli.prompt.callback


@click.pass_context
def new_callback(ctx, *args, greeting, **kwargs):
    if greeting:
        click.echo("👋  Hi from wrapper")
    return ctx.invoke(original_callback, *args, **kwargs)


llm_cli.prompt.callback = new_callback
