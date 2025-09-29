"""Main CLI entry point for Synapse agent workflow system."""

import click

from synapse.cli.commands import register_commands_group
from synapse.cli.init import init_command
from synapse.cli.template import register_template_group


@click.group()
@click.version_option(version="1.0.0", prog_name="synapse")
def cli() -> None:
    """Synapse Agent Workflow System - Claude Code agent orchestration."""
    pass


@cli.command()
@click.option("--project-name", help="Override detected project name", type=str)
@click.option(
    "--workflow-dir",
    default=".synapse",
    help="Custom workflow directory (default: .synapse)",
    type=str,
)
@click.option("--force", is_flag=True, help="Overwrite existing configuration")
@click.option(
    "--template-integration/--no-template-integration",
    default=True,
    help="Enable template-based CLAUDE.md integration (default: enabled)",
)
@click.option(
    "--preserve-content/--no-preserve-content",
    default=True,
    help="Preserve existing user content during integration (default: enabled)",
)
@click.option(
    "--detect-conflicts/--no-detect-conflicts",
    default=True,
    help="Detect and handle command conflicts (default: enabled)",
)
def init(
    project_name: str | None,
    workflow_dir: str,
    force: bool,
    template_integration: bool,
    preserve_content: bool,
    detect_conflicts: bool,
) -> None:
    """Initialize project with Synapse workflow and Claude Code integration."""
    init_command(
        project_name, workflow_dir, force, template_integration, preserve_content, detect_conflicts
    )


# Register command management group
register_commands_group(cli)

# Register template management group
register_template_group(cli)


if __name__ == "__main__":
    cli()
