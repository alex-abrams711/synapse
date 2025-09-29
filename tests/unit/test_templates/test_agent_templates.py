"""
Template validation tests for Synapse agent templates.

These tests verify that agent templates are valid and conform to expected structure.
These tests will fail until template implementation is complete.
"""
from pathlib import Path

import yaml

from synapse.services.validator import TemplateValidator


class TestAgentTemplateValidation:
    """Test validation of Claude agent templates."""

    def test_dev_agent_template_structure(self) -> None:
        """DEV agent template should have required sections and content."""
        # This test will fail until template implementation
        validator = TemplateValidator()

        # Test template content validation
        template_content = """
# DEV Agent

## Role
Implementation agent for coding tasks

## Capabilities
- Code implementation
- Unit testing
- Code review

## Rules
1. Follow TDD practices
2. Maintain code quality

## Prompt Template
You are the DEV agent in a Synapse workflow system.
        """

        result = validator.validate_agent_template("dev", template_content)
        assert result.is_valid
        assert "# DEV Agent" in template_content
        assert "## Role" in template_content
        assert "## Capabilities" in template_content
        assert "## Rules" in template_content
        assert "## Prompt Template" in template_content

    def test_auditor_agent_template_structure(self) -> None:
        """AUDITOR agent template should have required sections and content."""
        validator = TemplateValidator()

        template_content = """
# AUDITOR Agent

## Role
Quality assurance and verification agent

## Capabilities
- Code review
- Test verification
- Quality analysis

## Rules
1. Thorough verification required
2. Document all findings

## Prompt Template
You are the AUDITOR agent in a Synapse workflow system.
        """

        result = validator.validate_agent_template("auditor", template_content)
        assert result.is_valid
        assert "# AUDITOR Agent" in template_content

    def test_dispatcher_agent_template_structure(self) -> None:
        """DISPATCHER agent template should have required sections and content."""
        validator = TemplateValidator()

        template_content = """
# DISPATCHER Agent

## Role
Task coordination and workflow management

## Capabilities
- Task assignment
- Workflow orchestration
- Progress monitoring

## Rules
1. Coordinate between agents
2. Track task completion

## Prompt Template
You are the DISPATCHER agent in a Synapse workflow system.
        """

        result = validator.validate_agent_template("dispatcher", template_content)
        assert result.is_valid
        assert "# DISPATCHER Agent" in template_content

    def test_invalid_agent_template_fails_validation(self) -> None:
        """Templates missing required sections should fail validation."""
        validator = TemplateValidator()

        # Missing required sections
        incomplete_template = """
# Some Agent
This is not a proper template.
        """

        result = validator.validate_agent_template("invalid", incomplete_template)
        assert not result.is_valid
        assert len(result.errors) > 0


class TestCommandTemplateValidation:
    """Test validation of Claude slash command templates."""

    def test_status_command_template_structure(self) -> None:
        """Status command template should have proper structure."""
        validator = TemplateValidator()

        template_content = """
# /status - Show Workflow Status

## Description
Display current workflow status and agent activity.

## Usage
```
/status
```

## Implementation
Show workflow state, active tasks, and recent activity.
        """

        result = validator.validate_command_template("status", template_content)
        assert result.is_valid
        assert "# /status" in template_content
        assert "## Description" in template_content
        assert "## Usage" in template_content

    def test_workflow_command_template_structure(self) -> None:
        """Workflow command template should have proper structure."""
        validator = TemplateValidator()

        template_content = """
# /workflow - Manage Workflow State

## Description
Manage workflow state and view task logs.

## Usage
```
/workflow status
/workflow log --lines 20
```

## Implementation
Interface for workflow state management.
        """

        result = validator.validate_command_template("workflow", template_content)
        assert result.is_valid

    def test_validate_command_template_structure(self) -> None:
        """Validate command template should have proper structure."""
        validator = TemplateValidator()

        template_content = """
# /validate - Validate Configuration

## Description
Validate project configuration and templates.

## Usage
```
/validate
/validate --fix
```

## Implementation
Check configuration validity and offer fixes.
        """

        result = validator.validate_command_template("validate", template_content)
        assert result.is_valid

    def test_agent_command_template_structure(self) -> None:
        """Agent command template should have proper structure."""
        validator = TemplateValidator()

        template_content = """
# /agent - Manage Agents

## Description
View and configure agent settings.

## Usage
```
/agent status
/agent dev enable
```

## Implementation
Interface for agent management.
        """

        result = validator.validate_command_template("agent", template_content)
        assert result.is_valid


class TestMainContextValidation:
    """Test validation of main CLAUDE.md context file."""

    def test_claude_context_structure(self) -> None:
        """CLAUDE.md should have proper structure and content."""
        validator = TemplateValidator()

        context_content = """
# Synapse Agent Workflow System

## Project Overview
This project uses Synapse for agent workflow orchestration.

## Available Agents
- DEV: Code implementation
- AUDITOR: Quality assurance
- DISPATCHER: Task coordination

## Available Commands
- /status: Show workflow status
- /workflow: Manage workflow state
- /validate: Validate configuration
- /agent: Manage agents

## Current Workflow
Check .synapse/task_log.json for current tasks and status.
        """

        result = validator.validate_context_template(context_content)
        assert result.is_valid
        assert "# Synapse Agent Workflow" in context_content
        assert "## Available Agents" in context_content
        assert "## Available Commands" in context_content


class TestTemplateFileValidation:
    """Test validation of template files from filesystem."""

    def test_template_files_exist_and_valid(self) -> None:
        """All template files should exist and be valid after scaffolding."""
        # This test verifies the actual template files created by scaffolding
        import tempfile

        from synapse.models.project import ProjectConfig
        from synapse.services.scaffolder import ProjectScaffolder

        scaffolder = ProjectScaffolder()
        config = ProjectConfig(
            project_name="test_project",
            synapse_version="1.0.0",
            workflow_dir=".synapse",
            agents={},
            task_log_path="task_log.json"
        )

        # Test in a temporary directory to avoid affecting the real project
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            result = scaffolder.create_project_structure(temp_path, config)

            # Verify the scaffolder succeeded
            assert result.success

            # Verify key files were created
            assert (temp_path / ".claude" / "agents" / "dev.md").exists()
            assert (temp_path / ".claude" / "agents" / "auditor.md").exists()
            assert (temp_path / ".claude" / "agents" / "dispatcher.md").exists()
            assert (temp_path / ".synapse" / "config.yaml").exists()
            assert (temp_path / ".synapse" / "task_log.json").exists()

    def test_yaml_config_template_valid(self) -> None:
        """YAML configuration template should be valid YAML."""
        # Test that config template is valid YAML
        config_template = """
project_name: "Test Project"
synapse_version: "1.0.0"
workflow_dir: ".synapse"
task_log_path: "task_log.json"

agents:
  dev:
    enabled: true
    context_file: ".claude/agents/dev.md"
    custom_rules: []
  auditor:
    enabled: true
    context_file: ".claude/agents/auditor.md"
    custom_rules: []
  dispatcher:
    enabled: true
    context_file: ".claude/agents/dispatcher.md"
    custom_rules: []
        """

        # Should parse without error
        parsed_config = yaml.safe_load(config_template)
        assert parsed_config is not None
        assert parsed_config['project_name'] == "Test Project"
        assert 'agents' in parsed_config
        assert len(parsed_config['agents']) == 3
