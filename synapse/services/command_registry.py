"""Command registration service for managing slash commands and conflict resolution."""

from datetime import datetime
from pathlib import Path
from typing import Any

from synapse.models.command import (
    AgentType,
    CommandInfo,
    SlashCommand,
)
from synapse.models.command import (
    CommandRegistry as CommandRegistryModel,
)
from synapse.utils.conflicts import detect_command_conflicts


class CommandRegistrationResult:
    """Result of command registration operation."""

    def __init__(
        self,
        registered_commands: list[str],
        conflicts_detected: list[str],
        files_created: list[str],
        errors: list[str] | None = None,
        success: bool = True,
    ):
        """Initialize registration result."""
        self.registered_commands = registered_commands
        self.conflicts_detected = conflicts_detected
        self.files_created = files_created
        self.errors = errors or []
        self.success = success


class CommandRegistry:
    """Service for managing slash command registration and installation."""

    def __init__(self, registry_model: CommandRegistryModel | None = None):
        """Initialize command registry service."""
        self.registry = registry_model or CommandRegistryModel()

    def register_commands(
        self, commands: list[SlashCommand], command_dir: str, conflict_resolution: str = "prefix"
    ) -> CommandRegistrationResult:
        """Register a list of slash commands with conflict resolution.

        Args:
            commands: List of SlashCommand objects to register
            command_dir: Directory where command files will be created
            conflict_resolution: Strategy for handling conflicts ("prefix", "skip", "warn")

        Returns:
            CommandRegistrationResult with registration status
        """
        registered_commands: list[str] = []
        conflicts_detected: list[str] = []
        files_created: list[str] = []
        errors: list[str] = []

        try:
            # Create command directory if it doesn't exist
            cmd_dir_path = Path(command_dir)
            cmd_dir_path.mkdir(parents=True, exist_ok=True)

            # Extract command names for conflict detection
            command_names = [cmd.name.replace("/synapse:", "") for cmd in commands]

            # Detect conflicts
            conflict_result = detect_command_conflicts(command_names, command_dir)

            # Process conflicts
            for conflict in conflict_result.conflicts:
                conflicts_detected.append(conflict.command_name)

            # Register commands
            for command in commands:
                try:
                    result = self._register_single_command(
                        command, cmd_dir_path, conflict_resolution
                    )

                    if result["success"]:
                        registered_commands.append(command.name)
                        if result["file_created"]:
                            files_created.append(result["file_created"])

                        # Add to registry model
                        command_info = CommandInfo(
                            name=command.name,
                            file_path=result["file_created"] or "",
                            agent_target=command.agent_target,
                            installation_date=datetime.now(),
                            is_synapse_managed=command.is_synapse_managed,
                            last_modified=datetime.now(),
                        )
                        self.registry.add_command(command_info)
                    else:
                        errors.extend(result.get("errors", []))

                except Exception as e:
                    errors.append(f"Failed to register {command.name}: {e}")

            # Update registry scan date
            self.registry.last_scan_date = datetime.now()

        except Exception as e:
            errors.append(f"Registration failed: {e}")

        return CommandRegistrationResult(
            registered_commands=registered_commands,
            conflicts_detected=conflicts_detected,
            files_created=files_created,
            errors=errors,
        )

    def _register_single_command(
        self, command: SlashCommand, command_dir: Path, conflict_resolution: str
    ) -> dict[str, Any]:
        """Register a single command to the filesystem.

        Args:
            command: SlashCommand to register
            command_dir: Directory path for command files
            conflict_resolution: How to handle conflicts

        Returns:
            Dictionary with registration result
        """
        try:
            # Determine file name based on conflict resolution
            if conflict_resolution == "prefix":
                # Use synapse prefix for file name
                file_name = f"synapse-{command.name.replace('/synapse:', '')}.md"
            else:
                file_name = f"{command.name.replace('/', '').replace(':', '-')}.md"

            file_path = command_dir / file_name

            # Create command file content
            content = self._generate_command_file_content(command)

            # Write command file
            file_path.write_text(content, encoding="utf-8")

            return {"success": True, "file_created": str(file_path), "errors": []}

        except Exception as e:
            return {"success": False, "file_created": None, "errors": [str(e)]}

    def _generate_command_file_content(self, command: SlashCommand) -> str:
        """Generate command file content from SlashCommand."""
        content = f"""# {command.name}

## Description

{command.description}

## Agent Target

**Target Agent**: {command.agent_target.value}

## Usage

```
{command.name}
```

## Implementation

{command.command_template}

---

*This command was automatically generated by Synapse on {datetime.now().isoformat()}*
*Synapse Managed: {'Yes' if command.is_synapse_managed else 'No'}*
"""
        return content

    def list_commands(self) -> list[CommandInfo]:
        """List all registered commands."""
        return list(self.registry.installed_commands.values())

    def get_command(self, command_name: str) -> CommandInfo | None:
        """Get command info by name."""
        return self.registry.get_command(command_name)

    def unregister_command(self, command_name: str) -> bool:
        """Unregister a command and remove its file."""
        command_info = self.registry.get_command(command_name)
        if command_info and command_info.file_path:
            try:
                # Remove file if it exists
                file_path = Path(command_info.file_path)
                if file_path.exists():
                    file_path.unlink()

                # Remove from registry
                return self.registry.remove_command(command_name)
            except Exception:
                return False
        return False

    def scan_and_update_registry(self, command_dir: str) -> int:
        """Scan command directory and update registry with found commands.

        Returns:
            Number of commands found and added to registry
        """
        cmd_dir_path = Path(command_dir)
        if not cmd_dir_path.exists():
            return 0

        commands_found = 0

        # Scan for .md files
        for file_path in cmd_dir_path.glob("*.md"):
            try:
                content = file_path.read_text(encoding="utf-8")
                command_info = self._parse_command_file(str(file_path), content)

                if command_info and not self.registry.has_command(command_info.name):
                    self.registry.add_command(command_info)
                    commands_found += 1

            except Exception:
                # Skip files that can't be parsed
                continue

        self.registry.last_scan_date = datetime.now()
        return commands_found

    def _parse_command_file(self, file_path: str, content: str) -> CommandInfo | None:
        """Parse command file to extract command information."""
        lines = content.split("\n")

        # Look for command name in first heading
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line.startswith("#") and ("/" in line):
                # Extract command name - look for /command or /synapse:command
                import re

                match = re.search(r"(/[a-zA-Z:]+)", line)
                if match:
                    command_name = match.group(1)

                    # Extract agent target if present
                    agent_target = "DEV"  # Default
                    for content_line in lines:
                        if "**Target Agent**:" in content_line:
                            agent_match = re.search(r"\*\*Target Agent\*\*:\s*(\w+)", content_line)
                            if agent_match:
                                agent_target = agent_match.group(1)
                            break

                    # Check if synapse managed
                    is_synapse_managed = "Synapse Managed: Yes" in content

                    return CommandInfo(
                        name=command_name,
                        file_path=file_path,
                        agent_target=AgentType(agent_target),
                        installation_date=datetime.now(),
                        is_synapse_managed=is_synapse_managed,
                        last_modified=datetime.now(),
                    )

        return None

    def get_registry_model(self) -> CommandRegistryModel:
        """Get the underlying registry model."""
        return self.registry
