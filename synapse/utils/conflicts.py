"""Command conflict detection and resolution utilities."""

import re
from pathlib import Path

from synapse.models.command import (
    AgentType,
    ConflictInfo,
    ConflictResolution,
    ConflictType,
    SlashCommand,
)


class CommandInfo:
    """Information about an existing command."""

    def __init__(self, name: str, source_file: str, description: str = "") -> None:
        """Initialize command info."""
        self.name = name
        self.source_file = source_file
        self.description = description


class ConflictSummary:
    """Summary of detected conflicts."""

    def __init__(self) -> None:
        """Initialize conflict summary."""
        self.total_conflicts = 0
        self.name_collisions = 0
        self.functionality_overlaps = 0
        self.prefix_conflicts = 0


class ConflictDetectionResult:
    """Result of conflict detection process."""

    def __init__(self) -> None:
        """Initialize conflict detection result."""
        self.conflicts: list[ConflictInfo] = []
        self.conflict_summary = ConflictSummary()
        self.existing_commands: dict[str, CommandInfo] = {}
        self.scan_date = None


def detect_command_conflicts(
    proposed_commands: list[str], command_dir: str
) -> ConflictDetectionResult:
    """Detect conflicts between proposed commands and existing commands.

    Args:
        proposed_commands: List of proposed command names
        command_dir: Directory containing existing command files

    Returns:
        ConflictDetectionResult with detected conflicts
    """
    result = ConflictDetectionResult()
    existing_commands = scan_existing_commands(command_dir)
    result.existing_commands = existing_commands

    for proposed_cmd in proposed_commands:
        conflicts = _detect_conflicts_for_command(proposed_cmd, existing_commands)
        result.conflicts.extend(conflicts)

    # Update summary
    result.conflict_summary = _calculate_conflict_summary(result.conflicts)

    return result


def scan_existing_commands(command_dir: str) -> dict[str, CommandInfo]:
    """Scan directory for existing command files.

    Args:
        command_dir: Directory to scan for command files

    Returns:
        Dictionary mapping command names to CommandInfo objects
    """
    commands: dict[str, CommandInfo] = {}
    command_path = Path(command_dir)

    if not command_path.exists():
        return commands

    # Scan for .md files in commands directory
    for file_path in command_path.glob("*.md"):
        try:
            content = file_path.read_text(encoding="utf-8")
            command_info = parse_command_file(str(file_path), content)
            if command_info:
                commands[command_info.name] = command_info
        except Exception:
            # Skip files that can't be read or parsed
            continue

    return commands


def parse_command_file(file_path: str, content: str) -> CommandInfo | None:
    """Parse command file to extract command information.

    Args:
        file_path: Path to command file
        content: Content of command file

    Returns:
        CommandInfo object or None if not a valid command file
    """
    lines = content.split("\n")

    # Look for command name in first heading
    for line in lines[:10]:  # Check first 10 lines
        line = line.strip()
        if line.startswith("#") and "/" in line:
            # Extract command name
            match = re.search(r"(/[\w:]+)", line)
            if match:
                command_name = match.group(1)

                # Extract description
                description = ""
                desc_match = re.search(r"(/[\w:]+)\s*-\s*(.+)", line)
                if desc_match:
                    description = desc_match.group(2).strip()

                return CommandInfo(
                    name=command_name,
                    source_file=file_path,
                    description=description,
                )

    return None


def _detect_conflicts_for_command(
    proposed_cmd: str, existing_commands: dict[str, CommandInfo]
) -> list[ConflictInfo]:
    """Detect conflicts for a single proposed command.

    Args:
        proposed_cmd: Proposed command name
        existing_commands: Dictionary of existing commands

    Returns:
        List of ConflictInfo objects for detected conflicts
    """
    conflicts = []
    synapse_command_obj = SlashCommand(
        name=f"/synapse:{proposed_cmd}",
        description=f"Synapse {proposed_cmd} command",
        agent_target=AgentType.DEV,  # Default to DEV agent
        command_template=(
            f"# Synapse {proposed_cmd.title()} Command\n\n" f"Invoke {proposed_cmd} functionality."
        ),
        is_synapse_managed=True,
    )

    # Check for exact name collisions
    if f"/{proposed_cmd}" in existing_commands:
        existing_cmd = existing_commands[f"/{proposed_cmd}"]
        conflict = ConflictInfo(
            command_name=f"/{proposed_cmd}",
            existing_source=existing_cmd.source_file,
            synapse_command=synapse_command_obj,
            conflict_type=ConflictType.NAME_COLLISION,
            resolution=ConflictResolution.USE_PREFIX,
            is_resolvable=True,
        )
        conflicts.append(conflict)

    # Check for prefix conflicts (existing synapse commands)
    synapse_file_name = synapse_command_obj.name.replace("/", "").replace(":", "-") + ".md"
    if synapse_file_name in [Path(cmd.source_file).name for cmd in existing_commands.values()]:
        conflict = ConflictInfo(
            command_name=proposed_cmd,
            existing_source="Existing synapse command",
            synapse_command=synapse_command_obj,
            conflict_type=ConflictType.PREFIX_CONFLICT,
            resolution=ConflictResolution.WARN_USER,
            is_resolvable=True,
        )
        conflicts.append(conflict)

    # Check for functionality overlaps
    functionality_conflicts = _detect_functionality_overlap(
        proposed_cmd, existing_commands, synapse_command_obj
    )
    conflicts.extend(functionality_conflicts)

    return conflicts


def _detect_functionality_overlap(
    proposed_cmd: str, existing_commands: dict[str, CommandInfo], synapse_command_obj: SlashCommand
) -> list[ConflictInfo]:
    """Detect functionality overlap between proposed and existing commands.

    Args:
        proposed_cmd: Proposed command name
        existing_commands: Dictionary of existing commands
        synapse_command_obj: SlashCommand object for the proposed command

    Returns:
        List of ConflictInfo objects for functionality overlaps
    """
    conflicts: list[ConflictInfo] = []

    # Define semantic similarity patterns
    similarity_patterns = {
        "plan": ["planning", "design", "architect", "strategy"],
        "implement": ["build", "create", "develop", "code"],
        "review": ["audit", "check", "validate", "inspect"],
        "dev": ["developer", "development"],
        "audit": ["review", "check", "validate"],
        "dispatch": ["coordinate", "manage", "orchestrate"],
    }

    patterns = similarity_patterns.get(proposed_cmd, [])
    if not patterns:
        return conflicts

    for cmd_name, cmd_info in existing_commands.items():
        # Check command name and description for semantic similarity
        cmd_text = f"{cmd_name} {cmd_info.description}".lower()

        for pattern in patterns:
            if pattern in cmd_text:
                # Ensure command name starts with /
                formatted_cmd_name = cmd_name if cmd_name.startswith("/") else f"/{cmd_name}"
                conflict = ConflictInfo(
                    command_name=formatted_cmd_name,
                    existing_source=cmd_info.source_file,
                    synapse_command=synapse_command_obj,
                    conflict_type=ConflictType.FUNCTIONALITY_OVERLAP,
                    resolution=ConflictResolution.WARN_USER,
                    is_resolvable=True,
                )
                conflicts.append(conflict)
                break  # Only add one conflict per command

    return conflicts


def _calculate_conflict_summary(conflicts: list[ConflictInfo]) -> ConflictSummary:
    """Calculate summary statistics for conflicts.

    Args:
        conflicts: List of detected conflicts

    Returns:
        ConflictSummary with statistics
    """
    summary = ConflictSummary()
    summary.total_conflicts = len(conflicts)

    for conflict in conflicts:
        if conflict.conflict_type == ConflictType.NAME_COLLISION:
            summary.name_collisions += 1
        elif conflict.conflict_type == ConflictType.FUNCTIONALITY_OVERLAP:
            summary.functionality_overlaps += 1
        elif conflict.conflict_type == ConflictType.PREFIX_CONFLICT:
            summary.prefix_conflicts += 1

    return summary


def resolve_conflict(conflict: ConflictInfo) -> str:
    """Resolve a command conflict based on resolution strategy.

    Args:
        conflict: ConflictInfo object with resolution strategy

    Returns:
        Resolved command name
    """
    if conflict.resolution == ConflictResolution.USE_PREFIX:
        return conflict.synapse_command.name
    elif conflict.resolution == ConflictResolution.SKIP_COMMAND:
        return ""  # Empty string indicates skip
    else:
        # For WARN_USER or USER_CHOICE, return the synapse command name
        return conflict.synapse_command.name


class ConflictResolver:
    """Utility class for resolving command conflicts."""

    def resolve_with_prefix(self, command_name: str) -> str:
        """Resolve conflict by adding synapse prefix.

        Args:
            command_name: Original command name

        Returns:
            Prefixed command name
        """
        if command_name.startswith("/"):
            command_name = command_name[1:]
        return f"synapse:{command_name}"

    def resolve_with_warning(self, command_name: str) -> dict[str, str]:
        """Resolve conflict with warning to user.

        Args:
            command_name: Command name that conflicts

        Returns:
            Dictionary with action and details
        """
        return {
            "action": "warn_user",
            "command": command_name,
            "message": f"Command '{command_name}' conflicts with existing command",
        }

    def resolve_with_skip(self, command_name: str) -> dict[str, str]:
        """Resolve conflict by skipping command installation.

        Args:
            command_name: Command name to skip

        Returns:
            Dictionary with action and details
        """
        return {
            "action": "skip_command",
            "command": command_name,
            "message": f"Skipping installation of '{command_name}' due to conflict",
        }


class InteractiveResolver:
    """Interactive conflict resolution utility."""

    def resolve_interactively(self, conflicts: dict[str, list[str]]) -> dict[str, str]:
        """Resolve conflicts interactively with user input.

        Args:
            conflicts: Dictionary mapping command names to resolution options

        Returns:
            Dictionary mapping command names to chosen resolutions
        """
        resolutions = {}

        for command, options in conflicts.items():
            # In a real implementation, this would prompt the user
            # For now, default to the first option
            if options:
                if "prefix" in options[0].lower():
                    resolutions[command] = "use_prefix"
                elif "skip" in options[0].lower():
                    resolutions[command] = "skip_command"
                else:
                    resolutions[command] = "warn_user"

        return resolutions


def detect_functionality_overlap(
    existing_commands: list[str], synapse_commands: list[str]
) -> list[ConflictInfo]:
    """Detect functionality overlap between command sets.

    Args:
        existing_commands: List of existing command names
        synapse_commands: List of synapse command names

    Returns:
        List of ConflictInfo objects for overlaps
    """
    overlaps = []

    # Create dummy existing commands for overlap detection
    existing_cmd_info = {
        cmd: CommandInfo(name=cmd, source_file=f"{cmd}.md") for cmd in existing_commands
    }

    for synapse_cmd in synapse_commands:
        cmd_name = synapse_cmd.replace("/synapse:", "")
        # Create SlashCommand object for overlap detection
        synapse_name = f"/synapse:{cmd_name}"
        synapse_command_obj = SlashCommand(
            name=synapse_name,
            description=f"Synapse {cmd_name} command",
            agent_target=AgentType.DEV,
            command_template=(
                f"# Synapse {cmd_name.title()} Command\n\n" f"Invoke {cmd_name} functionality."
            ),
            is_synapse_managed=True,
        )
        functionality_conflicts = _detect_functionality_overlap(
            cmd_name, existing_cmd_info, synapse_command_obj
        )
        overlaps.extend(functionality_conflicts)

    return overlaps
