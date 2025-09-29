"""
Integration tests for Claude Code integration.

These tests verify that the scaffolded project integrates properly with Claude Code,
including context files, slash commands, and agent definitions.
These tests will fail until Claude integration implementation is complete.
"""
import json
import tempfile
from pathlib import Path

from synapse.models.project import ProjectConfig
from synapse.services.scaffolder import ProjectScaffolder


class TestClaudeContextIntegration:
    """Test Claude Code context file integration."""

    def test_claude_md_context_structure(self) -> None:
        """CLAUDE.md should contain proper context for Claude Code."""
        scaffolder = ProjectScaffolder()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            config = ProjectConfig(
                project_name="Claude Integration Test",
                synapse_version="1.0.0",
                workflow_dir=".synapse",
                agents={},
                task_log_path="task_log.json"
            )

            # This will fail until scaffolder is implemented
            result = scaffolder.create_project_structure(project_path, config)
            assert result.success

            # Verify CLAUDE.md has proper structure for Claude Code
            claude_md = project_path / "CLAUDE.md"
            assert claude_md.exists()

            with open(claude_md) as f:
                content = f.read()

            # Should contain project overview
            assert "# Synapse Agent Workflow System" in content
            assert "Claude Integration Test" in content

            # Should reference agent files
            assert ".claude/agents/dev.md" in content
            assert ".claude/agents/auditor.md" in content
            assert ".claude/agents/dispatcher.md" in content

            # Should reference command files
            assert "/status" in content
            assert "/workflow" in content
            assert "/validate" in content
            assert "/agent" in content

            # Should reference workflow state
            assert ".synapse/task_log.json" in content
            assert ".synapse/config.yaml" in content

    def test_agent_context_files_claude_compatible(self) -> None:
        """Agent context files should be Claude Code compatible."""
        scaffolder = ProjectScaffolder()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            config = ProjectConfig(
                project_name="Agent Context Test",
                synapse_version="1.0.0",
                workflow_dir=".synapse",
                agents={},
                task_log_path="task_log.json"
            )

            result = scaffolder.create_project_structure(project_path, config)
            assert result.success

            # Check each agent file for Claude Code compatibility
            for agent_name in ["dev", "auditor", "dispatcher"]:
                agent_file = project_path / ".claude" / "agents" / f"{agent_name}.md"
                assert agent_file.exists()

                with open(agent_file) as f:
                    content = f.read()

                # Should be markdown format
                assert content.startswith("#")
                assert "## Role" in content
                assert "## Capabilities" in content
                assert "## Rules" in content

                # Should reference current task location
                assert ".synapse/task_log.json" in content

                # Should have proper agent instructions
                assert (
                    f"{agent_name.upper()} agent" in content
                    or f"{agent_name.title()} agent" in content
                )


class TestSlashCommandIntegration:
    """Test Claude Code slash command integration."""

    def test_status_command_integration(self) -> None:
        """/status command should be properly configured for Claude Code."""
        scaffolder = ProjectScaffolder()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            config = ProjectConfig(
                project_name="Status Command Test",
                synapse_version="1.0.0",
                workflow_dir=".synapse",
                agents={},
                task_log_path="task_log.json"
            )

            result = scaffolder.create_project_structure(project_path, config)
            assert result.success

            # Check status command file
            status_cmd = project_path / ".claude" / "commands" / "status.md"
            assert status_cmd.exists()

            with open(status_cmd) as f:
                content = f.read()

            # Should define the command properly
            assert "# /status" in content
            assert "## Description" in content
            assert "workflow status" in content.lower()

            # Should reference correct file paths
            assert ".synapse" in content

    def test_workflow_command_integration(self) -> None:
        """/workflow command should be properly configured for Claude Code."""
        scaffolder = ProjectScaffolder()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            config = ProjectConfig(
                project_name="Workflow Command Test",
                synapse_version="1.0.0",
                workflow_dir=".synapse",
                agents={},
                task_log_path="task_log.json"
            )

            result = scaffolder.create_project_structure(project_path, config)
            assert result.success

            # Check workflow command file
            workflow_cmd = project_path / ".claude" / "commands" / "workflow.md"
            assert workflow_cmd.exists()

            with open(workflow_cmd) as f:
                content = f.read()

            # Should define the command properly
            assert "# /workflow" in content
            assert "task_log.json" in content

    def test_validate_command_integration(self) -> None:
        """/validate command should be properly configured for Claude Code."""
        scaffolder = ProjectScaffolder()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            config = ProjectConfig(
                project_name="Validate Command Test",
                synapse_version="1.0.0",
                workflow_dir=".synapse",
                agents={},
                task_log_path="task_log.json"
            )

            result = scaffolder.create_project_structure(project_path, config)
            assert result.success

            # Check validate command file
            validate_cmd = project_path / ".claude" / "commands" / "validate.md"
            assert validate_cmd.exists()

            with open(validate_cmd) as f:
                content = f.read()

            # Should define the command properly
            assert "# /validate" in content
            assert "configuration" in content.lower()

    def test_agent_command_integration(self) -> None:
        """/agent command should be properly configured for Claude Code."""
        scaffolder = ProjectScaffolder()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            config = ProjectConfig(
                project_name="Agent Command Test",
                synapse_version="1.0.0",
                workflow_dir=".synapse",
                agents={},
                task_log_path="task_log.json"
            )

            result = scaffolder.create_project_structure(project_path, config)
            assert result.success

            # Check agent command file
            agent_cmd = project_path / ".claude" / "commands" / "agent.md"
            assert agent_cmd.exists()

            with open(agent_cmd) as f:
                content = f.read()

            # Should define the command properly
            assert "# /agent" in content
            assert "agent" in content.lower()


class TestWorkflowStateIntegration:
    """Test workflow state integration with Claude Code."""

    def test_task_log_claude_readable(self) -> None:
        """Task log should be in format readable by Claude Code."""
        scaffolder = ProjectScaffolder()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            config = ProjectConfig(
                project_name="Task Log Test",
                synapse_version="1.0.0",
                workflow_dir=".synapse",
                agents={},
                task_log_path="task_log.json"
            )

            result = scaffolder.create_project_structure(project_path, config)
            assert result.success

            # Check task log format
            task_log = project_path / ".synapse" / "task_log.json"
            assert task_log.exists()

            with open(task_log) as f:
                log_data = json.load(f)

            # Should have structure Claude Code can understand
            assert 'workflow_id' in log_data
            assert 'project_name' in log_data
            assert 'entries' in log_data
            assert isinstance(log_data['entries'], list)

            # Project name should match config
            assert log_data['project_name'] == "Task Log Test"

    def test_config_yaml_claude_accessible(self) -> None:
        """Configuration YAML should be accessible to Claude Code."""
        scaffolder = ProjectScaffolder()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            config = ProjectConfig(
                project_name="Config Access Test",
                synapse_version="1.0.0",
                workflow_dir=".synapse",
                agents={},
                task_log_path="task_log.json"
            )

            result = scaffolder.create_project_structure(project_path, config)
            assert result.success

            # Check config accessibility
            config_file = project_path / ".synapse" / "config.yaml"
            assert config_file.exists()

            # File should be readable as YAML
            import yaml
            with open(config_file) as f:
                config_data = yaml.safe_load(f)

            # Should contain agent configuration
            assert 'agents' in config_data
            assert 'claude_commands' in config_data

            # Agent references should point to correct files
            for agent_name in ['dev', 'auditor', 'dispatcher']:
                if agent_name in config_data['agents']:
                    agent_config = config_data['agents'][agent_name]
                    assert 'context_file' in agent_config
                    assert f".claude/agents/{agent_name}.md" in agent_config['context_file']


class TestDirectoryStructureIntegration:
    """Test directory structure integration with Claude Code conventions."""

    def test_claude_directory_structure(self) -> None:
        """Claude directory should follow Claude Code conventions."""
        scaffolder = ProjectScaffolder()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            config = ProjectConfig(
                project_name="Directory Structure Test",
                synapse_version="1.0.0",
                workflow_dir=".synapse",
                agents={},
                task_log_path="task_log.json"
            )

            result = scaffolder.create_project_structure(project_path, config)
            assert result.success

            # Verify Claude Code standard structure
            claude_dir = project_path / ".claude"
            assert claude_dir.exists()
            assert claude_dir.is_dir()

            # Should have agents subdirectory
            agents_dir = claude_dir / "agents"
            assert agents_dir.exists()
            assert agents_dir.is_dir()

            # Should have commands subdirectory
            commands_dir = claude_dir / "commands"
            assert commands_dir.exists()
            assert commands_dir.is_dir()

            # Should not have unnecessary files
            claude_files = list(claude_dir.rglob("*"))
            # Filter to only .md files and directories
            md_files = [f for f in claude_files if f.is_file() and f.suffix == '.md']
            directories = [f for f in claude_files if f.is_dir()]

            # Should have expected number of files
            assert len(md_files) >= 7  # 3 agents + 4 commands
            assert len(directories) == 2  # agents/ and commands/

    def test_synapse_directory_structure(self) -> None:
        """Synapse directory should contain workflow files."""
        scaffolder = ProjectScaffolder()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            config = ProjectConfig(
                project_name="Synapse Directory Test",
                synapse_version="1.0.0",
                workflow_dir=".synapse",
                agents={},
                task_log_path="task_log.json"
            )

            result = scaffolder.create_project_structure(project_path, config)
            assert result.success

            # Verify Synapse workflow structure
            synapse_dir = project_path / ".synapse"
            assert synapse_dir.exists()
            assert synapse_dir.is_dir()

            # Should contain required workflow files
            required_files = [
                "config.yaml",
                "task_log.json"
            ]

            for file_name in required_files:
                file_path = synapse_dir / file_name
                assert file_path.exists()
                assert file_path.is_file()
                assert file_path.stat().st_size > 0  # Should not be empty

    def test_root_level_context_file(self) -> None:
        """Root level CLAUDE.md should exist and be properly formatted."""
        scaffolder = ProjectScaffolder()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            config = ProjectConfig(
                project_name="Root Context Test",
                synapse_version="1.0.0",
                workflow_dir=".synapse",
                agents={},
                task_log_path="task_log.json"
            )

            result = scaffolder.create_project_structure(project_path, config)
            assert result.success

            # Verify CLAUDE.md at root level
            claude_md = project_path / "CLAUDE.md"
            assert claude_md.exists()
            assert claude_md.is_file()

            with open(claude_md) as f:
                content = f.read()

            # Should be substantial content
            assert len(content) > 500  # Should be a meaningful context file

            # Should reference the project structure
            assert "Synapse Agent Workflow" in content
            assert "Root Context Test" in content
