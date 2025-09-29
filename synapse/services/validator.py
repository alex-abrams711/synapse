"""Template validation service for Synapse agent workflow system."""

import re
from pathlib import Path

import yaml

from synapse.models.project import ValidationResult


class TemplateValidator:
    """Service for validating agent templates and configuration files."""

    def __init__(self) -> None:
        """Initialize the template validator."""
        self.required_agent_sections = [
            "# ",  # Title section
            "## Role",
            "## Capabilities",
            "## Rules",
            "## Prompt Template"
        ]

        self.required_command_sections = [
            "# /",  # Command title
            "## Description",
            "## Usage",
            "## Implementation"
        ]

    def validate_agent_template(self, agent_id: str, content: str) -> ValidationResult:
        """Validate an agent template file content."""
        result = ValidationResult(is_valid=True)

        # Check if content is non-empty
        if not content.strip():
            result.add_error("Template content is empty")
            return result

        # Check for required sections
        for section in self.required_agent_sections:
            if section not in content:
                result.add_error(f"Missing required section: {section}")

        # Validate agent ID in title
        expected_title = f"# {agent_id.upper()} Agent"
        alt_title = f"# {agent_id.title()} Agent"
        if expected_title not in content and alt_title not in content:
            result.add_warning(f"Agent title should include '{expected_title}' or '{alt_title}'")

        # Check for placeholder variables
        placeholders = re.findall(r'\{\{(\w+)\}\}', content)
        valid_placeholders = [
            'project_name', 'workflow_dir', 'synapse_version', 'created_at'
        ]

        for placeholder in placeholders:
            if placeholder not in valid_placeholders:
                result.add_warning(f"Unknown placeholder: {{{{{placeholder}}}}}")

        # Check for markdown formatting
        if not content.strip().startswith('#'):
            result.add_error("Template should start with a markdown header")

        return result

    def validate_command_template(self, command_name: str, content: str) -> ValidationResult:
        """Validate a command template file content."""
        result = ValidationResult(is_valid=True)

        # Check if content is non-empty
        if not content.strip():
            result.add_error("Command template content is empty")
            return result

        # Check for required sections
        for section in self.required_command_sections:
            if section not in content:
                result.add_error(f"Missing required section: {section}")

        # Validate command name in title
        expected_title = f"# /{command_name}"
        if expected_title not in content:
            result.add_error(f"Command title should start with '{expected_title}'")

        # Check for usage examples
        if "```" not in content:
            result.add_warning("Command template should include usage examples in code blocks")

        return result

    def validate_context_template(self, content: str) -> ValidationResult:
        """Validate the main CLAUDE.md context template."""
        result = ValidationResult(is_valid=True)

        # Check if content is non-empty
        if not content.strip():
            result.add_error("Context template content is empty")
            return result

        # Check for required sections
        required_sections = [
            "# Synapse Agent Workflow",
            "## Available Agents",
            "## Available Commands"
        ]

        for section in required_sections:
            if section not in content:
                result.add_error(f"Missing required section: {section}")

        # Check for agent references
        required_agents = ["DEV", "AUDITOR", "DISPATCHER"]
        for agent in required_agents:
            if agent not in content:
                result.add_warning(f"Missing reference to {agent} agent")

        # Check for command references
        required_commands = ["/status", "/workflow", "/validate", "/agent"]
        for command in required_commands:
            if command not in content:
                result.add_warning(f"Missing reference to {command} command")

        return result

    def validate_yaml_config(self, content: str) -> ValidationResult:
        """Validate YAML configuration content."""
        result = ValidationResult(is_valid=True)

        try:
            config = yaml.safe_load(content)
        except yaml.YAMLError as e:
            result.add_error(f"Invalid YAML syntax: {e}")
            return result

        if config is None:
            result.add_error("YAML content is empty or invalid")
            return result

        # Check required top-level fields
        required_fields = [
            'project_name', 'synapse_version', 'workflow_dir', 'agents'
        ]

        for field in required_fields:
            if field not in config:
                result.add_error(f"Missing required field: {field}")

        # Validate agents section
        if 'agents' in config and isinstance(config['agents'], dict):
            required_agents = ['dev', 'auditor', 'dispatcher']
            for agent in required_agents:
                if agent not in config['agents']:
                    result.add_warning(f"Missing agent configuration: {agent}")
                else:
                    agent_config = config['agents'][agent]
                    if not isinstance(agent_config, dict):
                        result.add_error(f"Agent {agent} configuration must be a dictionary")
                    else:
                        # Check required agent fields
                        agent_required = ['enabled', 'context_file']
                        for field in agent_required:
                            if field not in agent_config:
                                result.add_error(f"Agent {agent} missing required field: {field}")

                        # Validate context file path
                        if 'context_file' in agent_config:
                            context_file = agent_config['context_file']
                            if not context_file.startswith('.claude/agents/'):
                                result.add_error(
                            f"Agent {agent} context_file must be under .claude/agents/"
                        )
                            if not context_file.endswith('.md'):
                                result.add_error(
                            f"Agent {agent} context_file must be a markdown file"
                        )

        return result

    def validate_json_structure(
        self, content: str, schema_type: str = "task_log"
    ) -> ValidationResult:
        """Validate JSON file structure."""
        result = ValidationResult(is_valid=True)

        try:
            import json
            data = json.loads(content)
        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON syntax: {e}")
            return result

        if data is None:
            result.add_error("JSON content is empty")
            return result

        if schema_type == "task_log":
            required_fields = ['workflow_id', 'project_name', 'synapse_version', 'entries']
            for field in required_fields:
                if field not in data:
                    result.add_error(f"Missing required field: {field}")

            # Validate entries structure
            if 'entries' in data:
                if not isinstance(data['entries'], list):
                    result.add_error("'entries' field must be a list")
                else:
                    for i, entry in enumerate(data['entries']):
                        if not isinstance(entry, dict):
                            result.add_error(f"Entry {i} must be a dictionary")
                            continue

                        entry_required = ['timestamp', 'agent_id', 'action', 'message']
                        for field in entry_required:
                            if field not in entry:
                                result.add_error(f"Entry {i} missing required field: {field}")

        elif schema_type == "workflow_state":
            required_fields = ['workflow_id', 'status']
            for field in required_fields:
                if field not in data:
                    result.add_error(f"Missing required field: {field}")

            # Validate status values
            if 'status' in data:
                valid_statuses = ['IDLE', 'ACTIVE', 'PAUSED', 'COMPLETED', 'ERROR']
                if data['status'] not in valid_statuses:
                    result.add_error(
                        f"Invalid status: {data['status']}. Must be one of {valid_statuses}"
                    )

        return result

    def validate_file_path(
        self, file_path: Path, expected_type: str | None = None
    ) -> ValidationResult:
        """Validate that a file path exists and has the expected type."""
        result = ValidationResult(is_valid=True)

        if not file_path.exists():
            result.add_error(f"File does not exist: {file_path}")
            return result

        if not file_path.is_file():
            result.add_error(f"Path is not a file: {file_path}")
            return result

        if expected_type:
            if expected_type == "markdown" and not file_path.suffix == ".md":
                result.add_error(f"Expected markdown file (.md): {file_path}")
            elif expected_type == "yaml" and file_path.suffix not in [".yaml", ".yml"]:
                result.add_error(f"Expected YAML file (.yaml/.yml): {file_path}")
            elif expected_type == "json" and not file_path.suffix == ".json":
                result.add_error(f"Expected JSON file (.json): {file_path}")

        # Check file is readable
        try:
            with open(file_path, encoding='utf-8') as f:
                f.read(1)  # Try to read first character
        except (OSError, UnicodeDecodeError) as e:
            result.add_error(f"File is not readable: {e}")

        return result

    def validate_directory_structure(
        self, base_path: Path, workflow_dir: str = ".synapse"
    ) -> ValidationResult:
        """Validate the expected directory structure exists."""
        result = ValidationResult(is_valid=True)

        # Check required directories
        required_dirs = [
            base_path / ".claude",
            base_path / ".claude" / "agents",
            base_path / ".claude" / "commands",
            base_path / workflow_dir
        ]

        for dir_path in required_dirs:
            if not dir_path.exists():
                result.add_error(f"Required directory missing: {dir_path}")
            elif not dir_path.is_dir():
                result.add_error(f"Path exists but is not a directory: {dir_path}")

        # Check required files
        required_files = [
            base_path / "CLAUDE.md",
            base_path / workflow_dir / "config.yaml",
            base_path / workflow_dir / "task_log.json"
        ]

        for file_path in required_files:
            file_result = self.validate_file_path(file_path)
            if file_result.has_errors():
                result.add_error(f"Required file issue: {file_path}")

        return result
