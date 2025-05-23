import click
import llm


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
