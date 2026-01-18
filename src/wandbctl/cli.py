import click

from wandbctl.commands.sync import sync, status
from wandbctl.commands.usage import usage
from wandbctl.commands.zombies import zombies
from wandbctl.commands.preflight import preflight
from wandbctl.commands.trends import trends
from wandbctl.commands.costs import costs


@click.group()
@click.version_option(package_name="wandbctl")
def cli():
    pass


cli.add_command(sync)
cli.add_command(status)
cli.add_command(usage)
cli.add_command(zombies)
cli.add_command(preflight)
cli.add_command(trends)
cli.add_command(costs)


if __name__ == "__main__":
    cli()
