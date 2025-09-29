"""Command and conflict management models for Synapse workflow system."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgentType(str, Enum):
    """Types of agents that can be targeted by commands."""

    DEV = "DEV"
    AUDITOR = "AUDITOR"
    DISPATCHER = "DISPATCHER"


class ConflictType(str, Enum):
    """Types of command conflicts."""

    NAME_COLLISION = "name_collision"
    FUNCTIONALITY_OVERLAP = "functionality_overlap"
    PREFIX_CONFLICT = "prefix_conflict"


class ConflictResolution(str, Enum):
    """Types of conflict resolution strategies."""

    USE_PREFIX = "use_prefix"
    WARN_USER = "warn_user"
    SKIP_COMMAND = "skip_command"
    USER_CHOICE = "user_choice"


class SlashCommand(BaseModel):
    """Definition of a Claude Code slash command."""

    model_config = ConfigDict(
        use_enum_values=True, json_encoders={datetime: lambda v: v.isoformat()}
    )

    name: str = Field(..., description="Command name (e.g., '/synapse:plan')")
    description: str = Field(..., description="Human-readable description")
    agent_target: AgentType = Field(..., description="Which agent this command invokes")
    command_template: str = Field(..., description="Template content for the command")
    is_synapse_managed: bool = Field(
        default=True, description="Whether this command is managed by Synapse"
    )
    installation_date: datetime | None = Field(
        default=None, description="When command was installed"
    )
    command_file_path: str | None = Field(
        default=None, description="Path to command definition file"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate command name format."""
        if not v.startswith("/"):
            raise ValueError("Command name must start with '/'")
        if " " in v:
            raise ValueError("Command name cannot contain spaces")
        if ":" in v and not v.startswith("/synapse:"):
            raise ValueError("Prefixed commands must use '/synapse:' prefix")
        return v

    @field_validator("agent_target")
    @classmethod
    def validate_agent_target(cls, v: AgentType) -> AgentType:
        """Validate agent target is supported."""
        valid_agents = {AgentType.DEV, AgentType.AUDITOR, AgentType.DISPATCHER}
        if v not in valid_agents:
            raise ValueError(f"Agent target must be one of: {[a.value for a in valid_agents]}")
        return v

    @field_validator("command_template")
    @classmethod
    def validate_command_template(cls, v: str) -> str:
        """Validate command template has required structure."""
        if not v.strip():
            raise ValueError("Command template cannot be empty")
        # If it contains newlines OR is longer than simple test strings, should start with #
        if "\n" in v.strip() or len(v.strip()) > 15:
            if not v.strip().startswith("#"):
                raise ValueError("Command template must start with markdown heading")
        return v

    def get_file_name(self) -> str:
        """Generate appropriate file name for this command."""
        # Convert /synapse:plan to synapse-plan.md
        name = self.name.lstrip("/")
        name = name.replace(":", "-")
        return f"{name}.md"

    def is_prefixed_command(self) -> bool:
        """Check if this is a prefixed synapse command."""
        return self.name.startswith("/synapse:")


class ConflictInfo(BaseModel):
    """Information about detected command conflicts."""

    model_config = ConfigDict(
        use_enum_values=True, json_encoders={datetime: lambda v: v.isoformat()}
    )

    command_name: str = Field(..., description="Name of conflicting command")
    existing_source: str = Field(..., description="Source of existing command")
    synapse_command: SlashCommand = Field(..., description="Synapse command that conflicts")
    conflict_type: ConflictType = Field(..., description="Type of conflict")
    resolution: ConflictResolution = Field(..., description="How conflict was resolved")
    detected_date: datetime | None = Field(default=None, description="When conflict was detected")
    is_resolvable: bool = Field(
        default=True, description="Whether conflict can be automatically resolved"
    )

    @field_validator("command_name")
    @classmethod
    def validate_command_name(cls, v: str) -> str:
        """Validate command name format."""
        if not v.strip():
            raise ValueError("Command name cannot be empty")
        v = v.strip()
        if not v.startswith("/"):
            raise ValueError("Command name must start with '/'")
        return v

    @field_validator("existing_source")
    @classmethod
    def validate_existing_source(cls, v: str) -> str:
        """Validate existing source is a valid path."""
        if not v.strip():
            raise ValueError("Existing source cannot be empty")
        return v.strip()

    @field_validator("synapse_command")
    @classmethod
    def validate_synapse_command(cls, v: SlashCommand) -> SlashCommand:
        """Validate synapse command format."""
        if not v.name.startswith("/synapse:"):
            raise ValueError("Synapse command must start with '/synapse:'")
        return v

    def model_post_init(self, __context: None) -> None:
        """Initialize with current timestamp if not provided."""
        if self.detected_date is None:
            self.detected_date = datetime.now()


class CommandInfo(BaseModel):
    """Information about an installed command for registry tracking."""

    model_config = ConfigDict(
        use_enum_values=True, json_encoders={datetime: lambda v: v.isoformat()}
    )

    name: str = Field(..., description="Command name")
    file_path: str = Field(..., description="Path to command file")
    agent_target: AgentType = Field(..., description="Target agent")
    installation_date: datetime | None = Field(
        default=None, description="When command was installed"
    )
    is_synapse_managed: bool = Field(default=False, description="Whether managed by Synapse")
    last_modified: datetime | None = Field(
        default=None, description="When command was last modified"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate command name format."""
        if not v.startswith("/"):
            raise ValueError("Command name must start with '/'")
        return v

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        """Validate file path is not empty."""
        if not v.strip():
            raise ValueError("File path cannot be empty")
        return v.strip()


class CommandRegistry(BaseModel):
    """Tracks installed slash commands and manages conflict detection."""

    model_config = ConfigDict(
        use_enum_values=True, json_encoders={datetime: lambda v: v.isoformat()}
    )

    installed_commands: dict[str, CommandInfo] = Field(
        default_factory=dict, description="Mapping of command names to command info"
    )
    conflicts: list[ConflictInfo] = Field(
        default_factory=list, description="Detected conflicts with existing commands"
    )
    last_scan_date: datetime | None = Field(
        default=None, description="When conflict detection was last performed"
    )
    synapse_commands: list[str] = Field(
        default_factory=list, description="List of available Synapse commands"
    )

    @field_validator("installed_commands")
    @classmethod
    def validate_installed_commands(cls, v: dict[str, CommandInfo]) -> dict[str, CommandInfo]:
        """Validate command names are unique and match keys."""
        for cmd_name, cmd_info in v.items():
            if not cmd_name.startswith("/"):
                raise ValueError(f"Command name must start with '/': {cmd_name}")
            if cmd_name != cmd_info.name:
                raise ValueError(
                    f"Dictionary key '{cmd_name}' must match command name '{cmd_info.name}'"
                )
        return v

    def add_command(self, command: CommandInfo) -> None:
        """Add a command to the registry."""
        self.installed_commands[command.name] = command
        if not command.last_modified:
            command.last_modified = datetime.now()

    def remove_command(self, command_name: str) -> bool:
        """Remove a command from the registry."""
        if command_name in self.installed_commands:
            del self.installed_commands[command_name]
            return True
        return False

    def get_command(self, command_name: str) -> CommandInfo | None:
        """Get command info by name."""
        return self.installed_commands.get(command_name)

    def has_command(self, command_name: str) -> bool:
        """Check if command is installed."""
        return command_name in self.installed_commands

    def add_conflict(self, conflict: ConflictInfo) -> None:
        """Add a detected conflict."""
        self.conflicts.append(conflict)

    def get_conflicts_for_command(self, command_name: str) -> list[ConflictInfo]:
        """Get all conflicts for a specific command."""
        return [
            conflict
            for conflict in self.conflicts
            if conflict.command_name == command_name or conflict.synapse_command == command_name
        ]

    def has_unresolved_conflicts(self) -> bool:
        """Check if there are any unresolved conflicts."""
        return any(
            conflict.resolution == ConflictResolution.USER_CHOICE for conflict in self.conflicts
        )

    def update_scan_date(self) -> None:
        """Update the last scan date to now."""
        self.last_scan_date = datetime.now()

    def get_synapse_managed_commands(self) -> list[CommandInfo]:
        """Get all Synapse-managed commands."""
        return [cmd for cmd in self.installed_commands.values() if cmd.is_synapse_managed]

    def get_user_commands(self) -> list[CommandInfo]:
        """Get all user-created commands."""
        return [cmd for cmd in self.installed_commands.values() if not cmd.is_synapse_managed]
