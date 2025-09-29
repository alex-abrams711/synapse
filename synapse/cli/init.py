"""Init command implementation for Synapse CLI."""

from datetime import datetime
from pathlib import Path

import click

from synapse.models.project import InitResult, ProjectConfig
from synapse.services.scaffolder import ProjectScaffolder


def init_command(
    project_name: str | None,
    workflow_dir: str,
    force: bool,
    template_integration: bool = True,
    preserve_content: bool = True,
    detect_conflicts: bool = True,
) -> None:
    """Implementation logic for the synapse init command.

    Args:
        project_name: Name of project, auto-detected if not provided
        workflow_dir: Directory for synapse workflow files
        force: Overwrite existing files if they exist
        template_integration: Enable template-based CLAUDE.md integration
        preserve_content: Preserve existing user content during integration
        detect_conflicts: Detect and handle command conflicts
    """
    project_path = Path.cwd()
    scaffolder = ProjectScaffolder()

    # Check if already initialized
    if scaffolder.is_project_initialized(project_path, workflow_dir) and not force:
        click.echo(
            click.style(
                f"Project already initialized in {project_path / workflow_dir}. "
                "Use --force to overwrite.",
                fg="yellow",
            )
        )
        raise click.Abort()

    # Detect or use provided project name
    if not project_name:
        project_name = scaffolder.detect_project_name(project_path)

    # Create project configuration with template integration settings
    config = ProjectConfig(
        project_name=project_name,
        synapse_version="1.0.0",
        workflow_dir=workflow_dir,
        task_log_path="task_log.json",
        created_at=datetime.now(),
        last_updated=datetime.now(),
        # Template integration settings
        template_integration_enabled=template_integration,
        claude_md_template_version="1.0.0",
        preserve_user_content=preserve_content,
        auto_detect_conflicts=detect_conflicts,
        backup_on_integration=True,
    )

    # Create project structure
    try:
        click.echo(f"Initializing Synapse workflow for '{project_name}'...")

        # Template integration and conflict detection are now handled by the enhanced scaffolder

        # Create project structure using enhanced scaffolder
        result = scaffolder.create_project_structure(
            project_path,
            config,
            force=force,
            template_integration=template_integration,
            preserve_content=preserve_content,
            detect_conflicts=detect_conflicts,
        )

        if result.success:
            # Template integration is now handled by enhanced scaffolder
            _display_success_message(result, result.claude_md_backup_created)
        else:
            _display_error_message(result)
            raise click.Abort()

    except Exception as e:
        click.echo(click.style(f"✗ Error during initialization: {e}", fg="red"))
        raise click.Abort() from e


def _display_success_message(result: InitResult, backup_file: str | None = None) -> None:
    """Display success message and summary."""
    click.echo(click.style("✓ Project initialized successfully!", fg="green"))

    # Display summary
    click.echo(f"\nProject: {result.project_name}")
    click.echo(f"Workflow Directory: {result.workflow_dir}")

    if result.agents_created:
        click.echo(f"\nAgents Created ({len(result.agents_created)}):")
        for agent in result.agents_created:
            click.echo(f"  • {agent.upper()} agent")

    if result.commands_created:
        click.echo(f"\nCommands Created ({len(result.commands_created)}):")
        for command in result.commands_created:
            click.echo(f"  • /{command}")

    click.echo(f"\nFiles Created ({len(result.files_created)}):")
    for file_path in sorted(result.files_created):
        click.echo(f"  • {file_path}")

    # Display template integration results
    if result.template_integration_performed:
        click.echo(click.style("\n🔄 Template Integration:", fg="blue"))
        click.echo("  ✓ CLAUDE.md integrated with Synapse template")
        if result.template_config_created:
            click.echo("  ✓ Template configuration created")

    if backup_file:
        click.echo(click.style("\n💾 Backup Created:", fg="blue"))
        click.echo(f"  • Original CLAUDE.md backed up to: {backup_file}")

    # Display conflicts detected
    if result.conflicts_detected:
        conflict_count = len(result.conflicts_detected)
        click.echo(click.style(f"\n⚠ Command Conflicts ({conflict_count}):", fg="yellow"))
        for conflict in result.conflicts_detected:
            click.echo(click.style(f"  • {conflict}", fg="yellow"))

    if result.warnings:
        click.echo(click.style(f"\nWarnings ({len(result.warnings)}):", fg="yellow"))
        for warning in result.warnings:
            click.echo(click.style(f"  ⚠ {warning}", fg="yellow"))

    # Next steps
    click.echo(click.style("\n📋 Next Steps:", fg="blue", bold=True))
    click.echo("1. Open this project in Claude Code")
    click.echo("2. Try the /status command to check workflow status")
    click.echo("3. Use /workflow, /validate, and /agent commands as needed")
    click.echo("4. Start describing tasks to the DISPATCHER agent")

    # Quick check suggestions
    click.echo(click.style("\n🔍 Quick Check:", fg="blue"))
    click.echo(f"  • Workflow: ls {result.workflow_dir}/")
    click.echo("  • Agents: ls .claude/agents/")
    click.echo("  • Commands: ls .claude/commands/")


def _display_error_message(result: InitResult) -> None:
    """Display error message and details."""
    click.echo(click.style("✗ Project initialization failed!", fg="red"))
    if result.warnings:
        for warning in result.warnings:
            click.echo(click.style(f"  Error: {warning}", fg="red"))
