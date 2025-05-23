import click
import llm


@llm.hookimpl
def register_commands(cli: click.Group):
    @cli.command(name="hello")
    @click.option("--shout/--no-shout", default=False)
    def hello(shout):
        """
        Say hello from a plugin.
        """
        msg = "Hello from a plugin!"
        click.echo(msg.upper() if shout else msg)
