"""Template validation service for Synapse agent workflow system."""

import re
from pathlib import Path

import yaml

from synapse.models.project import ValidationResult
from synapse.models.template import TemplateConfig


class TemplateValidator:
    """Service for validating agent templates and configuration files."""

    def __init__(self) -> None:
        """Initialize the template validator."""
        self.required_agent_sections = [
            "# ",  # Title section
            "## Role",
            "## Capabilities",
            "## Rules",
            "## Prompt Template",
        ]

        self.required_command_sections = [
            "# /",  # Command title
            "## Description",
            "## Usage",
            "## Implementation",
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
        placeholders = re.findall(r"\{\{(\w+)\}\}", content)
        valid_placeholders = ["project_name", "workflow_dir", "synapse_version", "created_at"]

        for placeholder in placeholders:
            if placeholder not in valid_placeholders:
                result.add_warning(f"Unknown placeholder: {{{{{placeholder}}}}}")

        # Check for markdown formatting
        if not content.strip().startswith("#"):
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
            "## Available Commands",
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
        required_fields = ["project_name", "synapse_version", "workflow_dir", "agents"]

        for field in required_fields:
            if field not in config:
                result.add_error(f"Missing required field: {field}")

        # Validate agents section
        if "agents" in config and isinstance(config["agents"], dict):
            required_agents = ["dev", "auditor", "dispatcher"]
            for agent in required_agents:
                if agent not in config["agents"]:
                    result.add_warning(f"Missing agent configuration: {agent}")
                else:
                    agent_config = config["agents"][agent]
                    if not isinstance(agent_config, dict):
                        result.add_error(f"Agent {agent} configuration must be a dictionary")
                    else:
                        # Check required agent fields
                        agent_required = ["enabled", "context_file"]
                        for field in agent_required:
                            if field not in agent_config:
                                result.add_error(f"Agent {agent} missing required field: {field}")

                        # Validate context file path
                        if "context_file" in agent_config:
                            context_file = agent_config["context_file"]
                            if not context_file.startswith(".claude/agents/"):
                                result.add_error(
                                    f"Agent {agent} context_file must be under .claude/agents/"
                                )
                            if not context_file.endswith(".md"):
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
            required_fields = ["workflow_id", "project_name", "synapse_version", "entries"]
            for field in required_fields:
                if field not in data:
                    result.add_error(f"Missing required field: {field}")

            # Validate entries structure
            if "entries" in data:
                if not isinstance(data["entries"], list):
                    result.add_error("'entries' field must be a list")
                else:
                    for i, entry in enumerate(data["entries"]):
                        if not isinstance(entry, dict):
                            result.add_error(f"Entry {i} must be a dictionary")
                            continue

                        entry_required = ["timestamp", "agent_id", "action", "message"]
                        for field in entry_required:
                            if field not in entry:
                                result.add_error(f"Entry {i} missing required field: {field}")

        elif schema_type == "workflow_state":
            required_fields = ["workflow_id", "status"]
            for field in required_fields:
                if field not in data:
                    result.add_error(f"Missing required field: {field}")

            # Validate status values
            if "status" in data:
                valid_statuses = ["IDLE", "ACTIVE", "PAUSED", "COMPLETED", "ERROR"]
                if data["status"] not in valid_statuses:
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
            with open(file_path, encoding="utf-8") as f:
                f.read(1)  # Try to read first character
        except (OSError, UnicodeDecodeError) as e:
            result.add_error(f"File is not readable: {e}")

        return result

    def validate_template_integration(
        self,
        template_config: TemplateConfig | None = None,
        target_file: str | None = None,
        integrated_content: str | None = None,
        original_slots: dict[str, str] | None = None,
        template_version: str | None = None,
    ) -> ValidationResult:
        """Validate template integration - supports both file-based and content-based validation."""
        if integrated_content is not None:
            # Content-based validation (new enhanced method)
            return self._validate_integrated_content(
                integrated_content, original_slots or {}, template_version or "1.0.0"
            )
        elif template_config is not None and target_file is not None:
            # File-based validation (original method)
            return self._validate_template_config(template_config, target_file)
        else:
            result = ValidationResult(is_valid=False)
            result.add_error(
                "Must provide either (template_config, target_file) or integrated_content"
            )
            return result

    def _validate_template_config(
        self, template_config: TemplateConfig, target_file: str
    ) -> ValidationResult:
        """Validate template integration configuration and target file (original implementation)."""
        result = ValidationResult(is_valid=True)

        # Validate template config structure
        if not template_config.template_version:
            result.add_error("Template config missing template version")

        # Validate user content slots
        if template_config.user_content_slots:
            for slot_name, content in template_config.user_content_slots.items():
                if not slot_name.endswith("_slot"):
                    result.add_warning(f"Content slot name should end with '_slot': {slot_name}")

                if content and len(content.strip()) > 10000:
                    result.add_warning(f"Content slot '{slot_name}' is very large (>10KB)")

        # Validate target file path
        target_path = Path(target_file)
        if target_path.exists() and not target_path.is_file():
            result.add_error(f"Target path exists but is not a file: {target_file}")

        # Check if target directory is writable
        target_dir = target_path.parent
        if not target_dir.exists():
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                result.add_error(f"Cannot create target directory: {e}")
        elif not target_dir.is_dir():
            result.add_error(f"Target parent path is not a directory: {target_dir}")

        return result

    def _validate_integrated_content(
        self, integrated_content: str, original_slots: dict[str, str], template_version: str
    ) -> ValidationResult:
        """Validate integrated template content and preservation of original slots."""
        result = ValidationResult(is_valid=True)

        # Basic content validation
        if not integrated_content.strip():
            result.add_error("Integrated content is empty")
            return result

        # Validate markdown structure
        if not integrated_content.strip().startswith("#"):
            result.add_error("Integrated content should start with a markdown header")

        # Validate preservation of original slots
        slots_preserved = 0
        slots_lost = 0

        for slot_name, slot_content in original_slots.items():
            if slot_content.strip():
                if slot_content.strip() in integrated_content:
                    slots_preserved += 1
                else:
                    slots_lost += 1
                    result.add_warning(f"Original content from '{slot_name}' may not be preserved")

        # Check for Synapse-specific structure
        required_sections = ["# Synapse Agent Workflow", "## Available Agents"]
        for section in required_sections:
            if section not in integrated_content:
                result.add_warning(f"Missing expected section: {section}")

        # Validate template version compatibility
        if template_version and "synapse_version" in integrated_content.lower():
            # Template integration appears to be working
            pass
        else:
            result.add_warning("Template version information may be missing")

        # Add content integrity information as attributes for test compatibility
        # Note: This is a compatibility layer for test contracts that expect specific attributes
        # Using setattr to avoid mypy errors for dynamic attributes
        if not hasattr(result, "validation_errors"):
            result.validation_errors = result.errors  # Alias for test compatibility
        total_slots = slots_preserved + slots_lost
        preservation_rate = slots_preserved / total_slots if total_slots > 0 else 1.0
        if not hasattr(result, "content_integrity"):
            result.content_integrity = {
                "slots_preserved": slots_preserved,
                "slots_lost": slots_lost,
                "preservation_rate": preservation_rate,
            }

        return result

    def validate_content_preservation(
        self, original_content: str, integrated_content: str
    ) -> ValidationResult:
        """Validate that user content is preserved during template integration."""
        result = ValidationResult(is_valid=True)

        if not original_content.strip():
            # No original content to preserve
            return result

        if not integrated_content.strip():
            result.add_error("Integrated content is empty but original content existed")
            return result

        # Extract user content sections from original
        original_sections = self._extract_content_sections(original_content)

        # Check preservation of important user sections
        user_sections = {
            "project_context",
            "context",
            "custom_instructions",
            "instructions",
            "project_guidelines",
            "guidelines",
            "additional_information",
            "metadata",
        }

        preserved_sections = 0
        lost_sections = 0

        for section_name in user_sections:
            if section_name in original_sections:
                original_section = original_sections[section_name].strip()
                if original_section:
                    # Check if content appears anywhere in integrated version
                    if original_section in integrated_content:
                        preserved_sections += 1
                    else:
                        lost_sections += 1
                        result.add_warning(
                            f"User content from section '{section_name}' may have been lost"
                        )

        # Calculate preservation rate
        if preserved_sections + lost_sections > 0:
            preservation_rate = preserved_sections / (preserved_sections + lost_sections)
            if preservation_rate < 0.8:
                result.add_error(f"Low content preservation rate: {preservation_rate:.1%}")
            elif preservation_rate < 0.9:
                result.add_warning(f"Moderate content preservation rate: {preservation_rate:.1%}")

        return result

    def validate_jinja_template(self, template_content: str) -> ValidationResult:
        """Validate Jinja2 template syntax and structure."""
        result = ValidationResult(is_valid=True)

        if not template_content.strip():
            result.add_error("Template content is empty")
            return result

        # Check for proper Jinja2 syntax with our custom delimiters
        try:
            from jinja2 import Environment, meta

            # Create environment with same settings as integrator
            env = Environment(
                block_start_string="{%",
                block_end_string="%}",
                variable_start_string="{{{",
                variable_end_string="}}}",
                comment_start_string="{#",
                comment_end_string="#}",
            )

            # Parse template to check syntax
            ast = env.parse(template_content)

            # Extract variables used in template
            variables = meta.find_undeclared_variables(ast)

            # Check for required variables
            required_vars = {
                "project_name",
                "initialization_date",
                "user_context_slot",
                "user_instructions_slot",
                "user_guidelines_slot",
                "user_metadata_slot",
            }

            missing_vars = required_vars - variables
            if missing_vars:
                for var in missing_vars:
                    result.add_warning(f"Template missing recommended variable: {{{{{{{var}}}}}}}")

            # Check for unknown variables that might be typos
            expected_vars = required_vars | {"synapse_commands"}
            unknown_vars = variables - expected_vars
            if unknown_vars:
                for var in unknown_vars:
                    result.add_warning(f"Template uses unknown variable: {{{{{{{var}}}}}}}")

        except Exception as e:
            result.add_error(f"Invalid Jinja2 template syntax: {e}")

        # Check for markdown structure
        if not template_content.strip().startswith("#"):
            result.add_error("Template should start with a markdown header")

        # Check for slot placeholders
        slot_patterns = [
            r"\{\{\{\s*user_context_slot\s*\}\}\}",
            r"\{\{\{\s*user_instructions_slot\s*\}\}\}",
            r"\{\{\{\s*user_guidelines_slot\s*\}\}\}",
            r"\{\{\{\s*user_metadata_slot\s*\}\}\}",
        ]

        for pattern in slot_patterns:
            if not re.search(pattern, template_content):
                slot_name = pattern.split("_")[1]
                result.add_warning(f"Template missing {slot_name} content slot")

        return result

    def validate_command_template_syntax(
        self, template_content: str, command_name: str
    ) -> ValidationResult:
        """Validate command template syntax and structure."""
        result = ValidationResult(is_valid=True)

        if not template_content.strip():
            result.add_error("Command template content is empty")
            return result

        # Check for required command structure
        expected_title = f"# /synapse:{command_name}"
        if expected_title not in template_content:
            result.add_error(f"Command template should start with '{expected_title}'")

        # Check for required sections
        required_sections = ["## Description", "## Usage", "## Implementation"]
        for section in required_sections:
            if section not in template_content:
                result.add_error(f"Missing required section: {section}")

        # Check for usage examples
        if "```" not in template_content:
            result.add_warning("Command template should include usage examples in code blocks")

        # Check for agent role specification
        agent_roles = ["DEV", "AUDITOR", "DISPATCHER"]
        has_role = any(role in template_content for role in agent_roles)
        if not has_role:
            result.add_warning("Command template should specify which agent role it invokes")

        return result

    def _extract_content_sections(self, content: str) -> dict[str, str]:
        """Extract content sections from existing CLAUDE.md."""
        sections = {}

        # Split by markdown headers
        lines = content.split("\n")
        current_section = None
        current_content: list[str] = []

        for line in lines:
            if line.startswith("#"):
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()

                # Start new section
                current_section = line.strip("#").strip().lower().replace(" ", "_")
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

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
            base_path / workflow_dir,
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
            base_path / workflow_dir / "task_log.json",
        ]

        for file_path in required_files:
            file_result = self.validate_file_path(file_path)
            if file_result.has_errors():
                result.add_error(f"Required file issue: {file_path}")

        return result
