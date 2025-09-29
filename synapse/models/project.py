"""Project configuration models for Synapse agent workflow system."""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from synapse.models.template import TemplateConfig


@dataclass
class AgentConfig:
    """Per-project configuration for a specific Claude Code agent."""

    agent_id: str
    enabled: bool
    context_file: str
    custom_prompt: str | None = None
    custom_rules: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate agent configuration fields."""
        if not self.context_file.startswith(".claude/agents/"):
            raise ValueError("Context file must be under .claude/agents/")
        if not self.context_file.endswith(".md"):
            raise ValueError("Context file must be a markdown file")


@dataclass
class ProjectConfig:
    """Configuration for a scaffolded project's Synapse workflow."""

    project_name: str
    synapse_version: str
    workflow_dir: str
    task_log_path: str
    agents: dict[str, AgentConfig] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    # Template integration settings
    template_integration_enabled: bool = True
    claude_md_template_version: str = "1.0.0"
    preserve_user_content: bool = True
    auto_detect_conflicts: bool = True
    backup_on_integration: bool = True
    template_config: TemplateConfig | None = None

    def __post_init__(self) -> None:
        """Validate project configuration fields."""
        if not self.project_name.strip():
            raise ValueError("Project name must be non-empty")

        # Validate semantic versioning format
        version_pattern = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$"
        if not re.match(version_pattern, self.synapse_version):
            raise ValueError("Synapse version must follow semantic versioning")

        # Validate workflow directory is relative
        if self.workflow_dir.startswith("/") or "\\" in self.workflow_dir:
            raise ValueError("Workflow directory must be relative path")

    def add_agent(
        self, agent_id: str, enabled: bool = True, custom_rules: list[str] | None = None
    ) -> AgentConfig:
        """Add an agent configuration to this project."""
        context_file = f".claude/agents/{agent_id}.md"
        agent_config = AgentConfig(
            agent_id=agent_id,
            enabled=enabled,
            context_file=context_file,
            custom_rules=custom_rules or [],
        )
        self.agents[agent_id] = agent_config
        self.last_updated = datetime.now()
        return agent_config

    def enable_agent(self, agent_id: str) -> None:
        """Enable an agent."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found in configuration")
        self.agents[agent_id].enabled = True
        self.last_updated = datetime.now()

    def disable_agent(self, agent_id: str) -> None:
        """Disable an agent."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found in configuration")
        self.agents[agent_id].enabled = False
        self.last_updated = datetime.now()

    def get_enabled_agents(self) -> list[str]:
        """Get list of enabled agent IDs."""
        return [agent_id for agent_id, config in self.agents.items() if config.enabled]

    def get_agent_context_file(self, agent_id: str) -> str:
        """Get the context file path for an agent."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found in configuration")
        return self.agents[agent_id].context_file

    def update_agent_rules(self, agent_id: str, custom_rules: list[str]) -> None:
        """Update custom rules for an agent."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found in configuration")
        self.agents[agent_id].custom_rules = custom_rules
        self.last_updated = datetime.now()

    # Template integration methods
    def set_template_config(self, template_config: TemplateConfig) -> None:
        """Set the template configuration for this project."""
        self.template_config = template_config
        self.last_updated = datetime.now()

    def enable_template_integration(self) -> None:
        """Enable template integration for this project."""
        self.template_integration_enabled = True
        self.last_updated = datetime.now()

    def disable_template_integration(self) -> None:
        """Disable template integration for this project."""
        self.template_integration_enabled = False
        self.last_updated = datetime.now()

    def update_template_settings(
        self,
        template_version: str | None = None,
        preserve_content: bool | None = None,
        auto_detect_conflicts: bool | None = None,
        backup_on_integration: bool | None = None,
    ) -> None:
        """Update template integration settings."""
        if template_version is not None:
            # Validate semantic versioning format
            version_pattern = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$"
            if not re.match(version_pattern, template_version):
                raise ValueError("Template version must follow semantic versioning")
            self.claude_md_template_version = template_version

        if preserve_content is not None:
            self.preserve_user_content = preserve_content

        if auto_detect_conflicts is not None:
            self.auto_detect_conflicts = auto_detect_conflicts

        if backup_on_integration is not None:
            self.backup_on_integration = backup_on_integration

        self.last_updated = datetime.now()

    def get_template_settings(self) -> dict[str, bool | str | TemplateConfig | None]:
        """Get current template integration settings."""
        return {
            "enabled": self.template_integration_enabled,
            "template_version": self.claude_md_template_version,
            "preserve_user_content": self.preserve_user_content,
            "auto_detect_conflicts": self.auto_detect_conflicts,
            "backup_on_integration": self.backup_on_integration,
            "template_config": self.template_config,
        }

    def is_template_integration_configured(self) -> bool:
        """Check if template integration is properly configured."""
        return (
            self.template_integration_enabled
            and self.template_config is not None
            and bool(self.claude_md_template_version.strip())
        )


@dataclass
class InitResult:
    """Result of project initialization operation."""

    success: bool
    project_name: str
    workflow_dir: str
    agents_created: list[str] = field(default_factory=list)
    commands_created: list[str] = field(default_factory=list)
    files_created: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # Template integration results
    template_integration_performed: bool = False
    claude_md_backup_created: str | None = None
    template_config_created: bool = False
    conflicts_detected: list[str] = field(default_factory=list)

    def add_warning(self, message: str) -> None:
        """Add a warning message to the result."""
        self.warnings.append(message)

    def add_file_created(self, file_path: str) -> None:
        """Add a created file to the result."""
        self.files_created.append(file_path)

    def add_agent_created(self, agent_id: str) -> None:
        """Add a created agent to the result."""
        self.agents_created.append(agent_id)

    def add_command_created(self, command_name: str) -> None:
        """Add a created command to the result."""
        self.commands_created.append(command_name)

    def set_template_integration_performed(self, backup_path: str | None = None) -> None:
        """Mark template integration as performed."""
        self.template_integration_performed = True
        if backup_path:
            self.claude_md_backup_created = backup_path

    def set_template_config_created(self) -> None:
        """Mark template config as created."""
        self.template_config_created = True

    def add_conflict_detected(self, conflict_description: str) -> None:
        """Add a detected conflict to the result."""
        self.conflicts_detected.append(conflict_description)


@dataclass
class ValidationResult:
    """Result of template or configuration validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    validation_errors: list[str] = field(default_factory=list)  # Test compatibility
    content_integrity: dict[str, Any] = field(default_factory=dict)  # Content integrity metrics

    def add_error(self, message: str) -> None:
        """Add an error message to the result."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning message to the result."""
        self.warnings.append(message)

    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
