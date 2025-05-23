import click
import llm
from llm.cli import prompt


@llm.hookimpl
def register_tools(register):
    pass


@llm.hookimpl
def register_commands(cli: click.Group):
    @cli.command(name="mcp")
    @click.option("--shout/--no-shout", default=False)
    def mcp(shout):
        """
        llm-mcp root cli command.
        """
        msg = "Hello from a plugin!"
        click.echo(msg.upper() if shout else msg)


# add option to `prompt` command

extra_opt = click.Option(
    ("--greeting", "-g"),
    is_flag=True,
    help="Say hello before running the real command",
    expose_value=True,
)
prompt.params.insert(0, extra_opt)

original_callback = prompt.callback


@click.pass_context
def new_callback(ctx, *args, greeting, **kwargs):
    if greeting:
        click.echo("👋  Hi from wrapper")
    return ctx.invoke(original_callback, *args, **kwargs)


prompt.callback = new_callback
