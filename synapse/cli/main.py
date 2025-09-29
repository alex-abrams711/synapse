"""Main CLI entry point for Synapse agent workflow system."""

import click

from synapse.cli.init import init_command


@click.group()
@click.version_option(version="1.0.0", prog_name="synapse")
def cli() -> None:
    """Synapse Agent Workflow System - Claude Code agent orchestration."""
    pass


@cli.command()
@click.option(
    "--project-name",
    help="Override detected project name",
    type=str
)
@click.option(
    "--workflow-dir",
    default=".synapse",
    help="Custom workflow directory (default: .synapse)",
    type=str
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing configuration"
)
def init(project_name: str | None, workflow_dir: str, force: bool) -> None:
    """Initialize project with Synapse workflow and Claude Code integration."""
    init_command(project_name, workflow_dir, force)


if __name__ == "__main__":
    cli()
