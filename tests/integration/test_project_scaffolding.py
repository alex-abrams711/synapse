"""
Integration tests for project scaffolding workflow.

These tests verify the complete project initialization workflow including
directory creation, template installation, and configuration setup.
These tests will fail until scaffolding implementation is complete.
"""
import json
import tempfile
from pathlib import Path

import yaml

from synapse.models.project import ProjectConfig
from synapse.services.scaffolder import ProjectScaffolder


class TestProjectScaffoldingWorkflow:
    """Test complete project scaffolding workflow."""

    def test_full_project_initialization(self) -> None:
        """Complete project initialization should create all required files and structure."""
        # This test will fail until implementation
        scaffolder = ProjectScaffolder()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create project configuration
            config = ProjectConfig(
                project_name="Test Project",
                synapse_version="1.0.0",
                workflow_dir=".synapse",
                agents={},
                task_log_path="task_log.json"
            )

            # This will fail until scaffolder is implemented
            result = scaffolder.create_project_structure(project_path, config)

            # Verify result
            assert result.success
            assert len(result.files_created) > 0

            # Verify directory structure
            assert (project_path / ".claude" / "agents").exists()
            assert (project_path / ".claude" / "commands").exists()
            assert (project_path / ".synapse").exists()

            # Verify configuration files
            assert (project_path / ".synapse" / "config.yaml").exists()
            assert (project_path / ".synapse" / "task_log.json").exists()
            assert (project_path / "CLAUDE.md").exists()

            # Verify agent files
            for agent in ["dev", "auditor", "dispatcher"]:
                agent_file = project_path / ".claude" / "agents" / f"{agent}.md"
                assert agent_file.exists()
                assert agent_file.stat().st_size > 0

            # Verify command files
            for command in ["status", "workflow", "validate", "agent"]:
                command_file = project_path / ".claude" / "commands" / f"{command}.md"
                assert command_file.exists()
                assert command_file.stat().st_size > 0

    def test_existing_directory_detection(self) -> None:
        """Scaffolding should adapt to existing project structure."""
        scaffolder = ProjectScaffolder()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create existing project structure
            (project_path / "src").mkdir()
            (project_path / "tests").mkdir()
            (project_path / "README.md").write_text("Existing project")

            config = ProjectConfig(
                project_name="Existing Project",
                synapse_version="1.0.0",
                workflow_dir=".synapse",
                agents={},
                task_log_path="task_log.json"
            )

            # Should not interfere with existing structure
            result = scaffolder.create_project_structure(project_path, config)

            assert result.success
            # Existing files should remain
            assert (project_path / "src").exists()
            assert (project_path / "tests").exists()
            assert (project_path / "README.md").exists()

            # New Synapse structure should be added
            assert (project_path / ".claude").exists()
            assert (project_path / ".synapse").exists()

    def test_custom_workflow_directory(self) -> None:
        """Scaffolding should support custom workflow directory names."""
        scaffolder = ProjectScaffolder()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            config = ProjectConfig(
                project_name="Custom Project",
                synapse_version="1.0.0",
                workflow_dir=".custom-synapse",
                agents={},
                task_log_path="task_log.json"
            )

            result = scaffolder.create_project_structure(project_path, config)

            assert result.success
            assert (project_path / ".custom-synapse").exists()
            assert not (project_path / ".synapse").exists()
            assert (project_path / ".custom-synapse" / "config.yaml").exists()

    def test_force_overwrite_existing_config(self) -> None:
        """Scaffolding with force should overwrite existing configuration."""
        scaffolder = ProjectScaffolder()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create initial configuration
            config1 = ProjectConfig(
                project_name="Original Project",
                synapse_version="1.0.0",
                workflow_dir=".synapse",
                agents={},
                task_log_path="task_log.json"
            )

            result1 = scaffolder.create_project_structure(project_path, config1)
            assert result1.success

            # Force overwrite with new configuration
            config2 = ProjectConfig(
                project_name="Updated Project",
                synapse_version="1.0.0",
                workflow_dir=".synapse",
                agents={},
                task_log_path="task_log.json"
            )

            result2 = scaffolder.create_project_structure(
                project_path, config2, force=True
            )
            assert result2.success

            # Verify configuration was updated
            config_path = project_path / ".synapse" / "config.yaml"
            with open(config_path) as f:
                updated_config = yaml.safe_load(f)

            assert updated_config['project_name'] == "Updated Project"


class TestTemplateInstallation:
    """Test template file installation and content generation."""

    def test_agent_template_content_generation(self) -> None:
        """Agent templates should be generated with proper content."""
        scaffolder = ProjectScaffolder()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            config = ProjectConfig(
                project_name="Template Test Project",
                synapse_version="1.0.0",
                workflow_dir=".synapse",
                agents={},
                task_log_path="task_log.json"
            )

            result = scaffolder.create_project_structure(project_path, config)
            assert result.success

            # Check DEV agent template content
            dev_template = project_path / ".claude" / "agents" / "dev.md"
            with open(dev_template) as f:
                dev_content = f.read()

            assert "# DEV Agent" in dev_content
            assert "Template Test Project" in dev_content  # Project name interpolation
            assert "## Role" in dev_content
            assert "## Capabilities" in dev_content

            # Check AUDITOR agent template content
            auditor_template = project_path / ".claude" / "agents" / "auditor.md"
            with open(auditor_template) as f:
                auditor_content = f.read()

            assert "# AUDITOR Agent" in auditor_content
            assert "verification" in auditor_content.lower()

    def test_command_template_content_generation(self) -> None:
        """Command templates should be generated with proper content."""
        scaffolder = ProjectScaffolder()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            config = ProjectConfig(
                project_name="Command Test Project",
                synapse_version="1.0.0",
                workflow_dir=".synapse",
                agents={},
                task_log_path="task_log.json"
            )

            result = scaffolder.create_project_structure(project_path, config)
            assert result.success

            # Check status command template
            status_template = project_path / ".claude" / "commands" / "status.md"
            with open(status_template) as f:
                status_content = f.read()

            assert "# /status" in status_content
            assert ".synapse" in status_content  # Should reference workflow directory

            # Check workflow command template
            workflow_template = project_path / ".claude" / "commands" / "workflow.md"
            with open(workflow_template) as f:
                workflow_content = f.read()

            assert "# /workflow" in workflow_content
            assert "task_log.json" in workflow_content

    def test_main_context_file_generation(self) -> None:
        """CLAUDE.md context file should be generated with project-specific content."""
        scaffolder = ProjectScaffolder()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            config = ProjectConfig(
                project_name="Context Test Project",
                synapse_version="1.0.0",
                workflow_dir=".synapse",
                agents={},
                task_log_path="task_log.json"
            )

            result = scaffolder.create_project_structure(project_path, config)
            assert result.success

            # Check CLAUDE.md content
            claude_md = project_path / "CLAUDE.md"
            with open(claude_md) as f:
                claude_content = f.read()

            assert "# Synapse Agent Workflow System" in claude_content
            assert "Context Test Project" in claude_content
            assert "DEV Agent" in claude_content
            assert "AUDITOR Agent" in claude_content
            assert "DISPATCHER Agent" in claude_content
            assert "/status" in claude_content
            assert "/workflow" in claude_content


class TestConfigurationSetup:
    """Test configuration file setup and initialization."""

    def test_yaml_config_creation(self) -> None:
        """YAML configuration file should be created with correct structure."""
        scaffolder = ProjectScaffolder()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            config = ProjectConfig(
                project_name="Config Test Project",
                synapse_version="1.0.0",
                workflow_dir=".synapse",
                agents={},
                task_log_path="task_log.json"
            )

            result = scaffolder.create_project_structure(project_path, config)
            assert result.success

            # Verify YAML config structure
            config_path = project_path / ".synapse" / "config.yaml"
            with open(config_path) as f:
                yaml_config = yaml.safe_load(f)

            assert yaml_config['project_name'] == "Config Test Project"
            assert yaml_config['synapse_version'] == "1.0.0"
            assert yaml_config['workflow_dir'] == ".synapse"
            assert 'agents' in yaml_config
            assert 'claude_commands' in yaml_config
            assert 'created_at' in yaml_config

    def test_task_log_initialization(self) -> None:
        """Task log should be initialized with proper structure."""
        scaffolder = ProjectScaffolder()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            config = ProjectConfig(
                project_name="Log Test Project",
                synapse_version="1.0.0",
                workflow_dir=".synapse",
                agents={},
                task_log_path="task_log.json"
            )

            result = scaffolder.create_project_structure(project_path, config)
            assert result.success

            # Verify task log structure
            log_path = project_path / ".synapse" / "task_log.json"
            with open(log_path) as f:
                log_data = json.load(f)

            assert 'workflow_id' in log_data
            assert 'project_name' in log_data
            assert 'synapse_version' in log_data
            assert 'entries' in log_data
            assert isinstance(log_data['entries'], list)
            assert len(log_data['entries']) == 0  # Should start empty

    def test_workflow_state_initialization(self) -> None:
        """Workflow state should be initialized properly."""
        scaffolder = ProjectScaffolder()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            config = ProjectConfig(
                project_name="Workflow Test Project",
                synapse_version="1.0.0",
                workflow_dir=".synapse",
                agents={},
                task_log_path="task_log.json"
            )

            result = scaffolder.create_project_structure(project_path, config)
            assert result.success

            # Verify workflow state file exists and has proper structure
            state_path = project_path / ".synapse" / "workflow_state.json"
            if state_path.exists():  # Optional file
                with open(state_path) as f:
                    state_data = json.load(f)

                assert 'workflow_id' in state_data
                assert 'status' in state_data
                assert state_data['status'] == 'IDLE'
