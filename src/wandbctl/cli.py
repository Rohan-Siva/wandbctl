import click

from wandbctl.commands.sync import sync, status
from wandbctl.commands.usage import usage
from wandbctl.commands.zombies import zombies
from wandbctl.commands.preflight import preflight
from wandbctl.commands.trends import trends
from wandbctl.commands.costs import costs
from wandbctl.commands.compare import compare
from wandbctl.commands.export import export
from wandbctl.commands.top import top
from wandbctl.commands.clean import clean
from wandbctl.commands.health import health
from wandbctl.commands.failures import failures
from wandbctl.commands.projects import projects
from wandbctl.commands.summary import summary


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
cli.add_command(compare)
cli.add_command(export)
cli.add_command(top)
cli.add_command(clean)
cli.add_command(health)
cli.add_command(failures)
cli.add_command(projects)
cli.add_command(summary)


if __name__ == "__main__":
    cli()
