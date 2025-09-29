"""CLI commands for managing Synapse slash commands."""

from pathlib import Path

import click

from synapse.models.command import AgentType, SlashCommand
from synapse.services.command_registry import CommandRegistry


@click.group()
def commands() -> None:
    """Manage Synapse slash commands and command registry."""
    pass


@commands.command(name="list")
@click.option(
    "--command-dir",
    default=".claude/commands",
    help="Directory containing command files (default: .claude/commands)",
    type=str,
)
def list_commands(command_dir: str) -> None:
    """List all registered slash commands."""
    registry = CommandRegistry()

    # Scan and update registry first
    commands_found = registry.scan_and_update_registry(command_dir)
    if commands_found > 0:
        click.echo(f"Found and registered {commands_found} new commands")

    commands_list = registry.list_commands()

    if not commands_list:
        click.echo("No commands registered")
        return

    click.echo(f"\nRegistered Commands ({len(commands_list)}):")
    click.echo("=" * 50)

    for cmd in sorted(commands_list, key=lambda x: x.name):
        status = "✓" if Path(cmd.file_path).exists() else "✗"
        managed = "Synapse" if cmd.is_synapse_managed else "User"

        click.echo(f"{status} {cmd.name}")
        click.echo(f"  Agent: {cmd.agent_target}")
        click.echo(f"  Type: {managed}")
        click.echo(f"  File: {cmd.file_path}")
        if cmd.installation_date:
            click.echo(f"  Installed: {cmd.installation_date.strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo()


@commands.command()
@click.argument("name")
@click.argument("description")
@click.option(
    "--agent",
    type=click.Choice(["DEV", "AUDITOR", "DISPATCHER"]),
    default="DEV",
    help="Target agent for the command",
)
@click.option("--template", help="Custom command template content", type=str)
@click.option(
    "--command-dir",
    default=".claude/commands",
    help="Directory for command files (default: .claude/commands)",
    type=str,
)
def register(
    name: str, description: str, agent: str, template: str | None, command_dir: str
) -> None:
    """Register a new slash command.

    NAME: Command name (will be prefixed with /synapse: automatically)
    DESCRIPTION: Brief description of what the command does
    """
    # Ensure name starts with proper prefix
    if not name.startswith("/"):
        name = f"/synapse:{name}"
    elif name.startswith("/") and not name.startswith("/synapse:"):
        name = f"/synapse:{name[1:]}"

    # Create SlashCommand object
    slash_command = SlashCommand(
        name=name,
        description=description,
        agent_target=AgentType(agent),
        command_template=template or f"Default template for {name}",
        is_synapse_managed=True,
    )

    # Register command
    registry = CommandRegistry()
    result = registry.register_commands(
        commands=[slash_command], command_dir=command_dir, conflict_resolution="prefix"
    )

    # Display results
    if result.registered_commands:
        click.echo(click.style("✓ Command registered successfully!", fg="green"))
        click.echo(f"Command: {result.registered_commands[0]}")

        if result.files_created:
            click.echo(f"File: {result.files_created[0]}")

        if result.conflicts_detected:
            click.echo(click.style("⚠ Conflicts detected:", fg="yellow"))
            for conflict in result.conflicts_detected:
                click.echo(f"  • {conflict}")
    else:
        click.echo(click.style("✗ Command registration failed!", fg="red"))

    if result.errors:
        click.echo(click.style("Errors:", fg="red"))
        for error in result.errors:
            click.echo(f"  • {error}")


@commands.command()
@click.argument("name")
@click.option("--force", is_flag=True, help="Force removal without confirmation")
def unregister(name: str, force: bool) -> None:
    """Unregister a slash command.

    NAME: Command name to remove (with or without /synapse: prefix)
    """
    # Normalize command name
    if not name.startswith("/"):
        name = f"/synapse:{name}"
    elif name.startswith("/") and not name.startswith("/synapse:"):
        name = f"/synapse:{name[1:]}"

    registry = CommandRegistry()
    command_info = registry.get_command(name)

    if not command_info:
        click.echo(click.style(f"✗ Command '{name}' not found", fg="red"))
        return

    # Confirmation unless forced
    if not force:
        click.echo(f"Command: {command_info.name}")
        click.echo(f"File: {command_info.file_path}")
        click.echo(f"Agent: {command_info.agent_target}")

        if not click.confirm("\nAre you sure you want to unregister this command?"):
            click.echo("Cancelled")
            return

    # Unregister command
    success = registry.unregister_command(name)

    if success:
        click.echo(click.style("✓ Command unregistered successfully!", fg="green"))
    else:
        click.echo(click.style("✗ Failed to unregister command", fg="red"))


@commands.command()
@click.option(
    "--command-dir",
    default=".claude/commands",
    help="Directory to scan for commands (default: .claude/commands)",
    type=str,
)
def scan(command_dir: str) -> None:
    """Scan command directory and update registry."""
    registry = CommandRegistry()

    click.echo(f"Scanning {command_dir} for commands...")

    commands_found = registry.scan_and_update_registry(command_dir)

    if commands_found > 0:
        click.echo(click.style(f"✓ Found and registered {commands_found} commands", fg="green"))
    else:
        click.echo("No new commands found")

    # Display current registry status
    total_commands = len(registry.list_commands())
    last_scan = registry.get_registry_model().last_scan_date

    click.echo("\nRegistry Status:")
    click.echo(f"  Total Commands: {total_commands}")
    if last_scan:
        click.echo(f"  Last Scan: {last_scan.strftime('%Y-%m-%d %H:%M:%S')}")


@commands.command()
@click.argument("name")
@click.option(
    "--command-dir",
    default=".claude/commands",
    help="Directory containing command files (default: .claude/commands)",
    type=str,
)
def info(name: str, command_dir: str) -> None:
    """Show detailed information about a command.

    NAME: Command name to inspect
    """
    # Normalize command name
    if not name.startswith("/"):
        name = f"/synapse:{name}"
    elif name.startswith("/") and not name.startswith("/synapse:"):
        name = f"/synapse:{name[1:]}"

    registry = CommandRegistry()

    # Update registry first
    registry.scan_and_update_registry(command_dir)

    command_info = registry.get_command(name)

    if not command_info:
        click.echo(click.style(f"✗ Command '{name}' not found", fg="red"))
        return

    # Display command information
    click.echo("Command Information:")
    click.echo("=" * 30)
    click.echo(f"Name: {command_info.name}")
    click.echo(f"Agent Target: {command_info.agent_target}")
    click.echo(f"Synapse Managed: {'Yes' if command_info.is_synapse_managed else 'No'}")
    click.echo(f"File Path: {command_info.file_path}")

    if command_info.installation_date:
        click.echo(f"Installed: {command_info.installation_date.strftime('%Y-%m-%d %H:%M:%S')}")

    if command_info.last_modified:
        click.echo(f"Modified: {command_info.last_modified.strftime('%Y-%m-%d %H:%M:%S')}")

    # Check if file exists and show preview
    file_path = Path(command_info.file_path)
    if file_path.exists():
        click.echo(click.style("\n✓ File exists", fg="green"))

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            # Show first few lines as preview
            click.echo("\nFile Preview:")
            click.echo("-" * 20)
            for i, line in enumerate(lines[:10]):
                click.echo(line)
                if i == 9 and len(lines) > 10:
                    click.echo(f"... ({len(lines) - 10} more lines)")

        except Exception as e:
            click.echo(click.style(f"✗ Error reading file: {e}", fg="red"))
    else:
        click.echo(click.style("✗ File not found", fg="red"))


def register_commands_group(cli_group: click.Group) -> None:
    """Register the commands group with the main CLI."""
    cli_group.add_command(commands)
