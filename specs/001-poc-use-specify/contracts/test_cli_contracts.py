"""
Contract tests for Synapse CLI.

Only tests the single "synapse init" command - all other functionality is via Claude Code
slash commands. These tests verify the CLI interface contracts and will fail until
implementation is complete.
"""
import json
from pathlib import Path

from click.testing import CliRunner


class TestInitCommand:
    """Test the only CLI command: synapse init."""

    def test_init_creates_project_structure(self):
        """synapse init should create .claude and .synapse directories with proper structure."""
        # This test will fail until implementation
        from synapse.cli.main import cli

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['init'])

            assert result.exit_code == 0
            assert Path('.claude/agents').exists()
            assert Path('.claude/commands').exists()
            assert Path('.synapse').exists()
            assert Path('.synapse/config.yaml').exists()
            assert Path('.synapse/task_log.json').exists()
            assert Path('CLAUDE.md').exists()

    def test_init_with_custom_project_name(self):
        """synapse init --project-name should set custom project name."""
        from synapse.cli.main import cli

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['init', '--project-name', 'MyCustomProject'])

            assert result.exit_code == 0

            # Check that config contains custom project name
            config_path = Path('.synapse/config.yaml')
            assert config_path.exists()

            import yaml
            with open(config_path) as f:
                config = yaml.safe_load(f)

            assert config['project_name'] == 'MyCustomProject'

    def test_init_with_custom_workflow_dir(self):
        """synapse init --workflow-dir should use custom directory."""
        from synapse.cli.main import cli

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['init', '--workflow-dir', '.custom-synapse'])

            assert result.exit_code == 0
            assert Path('.custom-synapse').exists()
            assert not Path('.synapse').exists()
            assert Path('.claude').exists()  # Claude directory should still be created

    def test_init_prevents_overwrite_without_force(self):
        """synapse init should fail if project already initialized without --force."""
        from synapse.cli.main import cli

        runner = CliRunner()
        with runner.isolated_filesystem():
            # First init
            result1 = runner.invoke(cli, ['init'])
            assert result1.exit_code == 0

            # Second init should fail
            result2 = runner.invoke(cli, ['init'])
            assert result2.exit_code == 1
            assert 'already initialized' in result2.output

    def test_init_with_force_overwrites(self):
        """synapse init --force should overwrite existing configuration."""
        from synapse.cli.main import cli

        runner = CliRunner()
        with runner.isolated_filesystem():
            # First init
            result1 = runner.invoke(cli, ['init', '--project-name', 'Original'])
            assert result1.exit_code == 0

            # Force overwrite
            result2 = runner.invoke(cli, ['init', '--force', '--project-name', 'Updated'])
            assert result2.exit_code == 0

            # Check config was updated
            config_path = Path('.synapse/config.yaml')
            import yaml
            with open(config_path) as f:
                config = yaml.safe_load(f)

            assert config['project_name'] == 'Updated'


# All other functionality (status, validate, agent management, log viewing)
# is handled by Claude Code slash commands, not CLI commands


class TestTemplateScaffolding:
    """Test template scaffolding behavior."""

    def test_agent_templates_are_created(self):
        """Init should create all Claude agent template files."""
        from synapse.cli.main import cli

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['init'])

            assert result.exit_code == 0

            # Check all Claude agent templates exist
            agent_files = [
                '.claude/agents/dev.md',
                '.claude/agents/auditor.md',
                '.claude/agents/dispatcher.md'
            ]

            for file_path in agent_files:
                assert Path(file_path).exists()

                # Check file has content
                with open(file_path) as f:
                    content = f.read()
                assert len(content) > 0
                assert '# ' in content  # Should be markdown

            # Check Claude commands exist
            command_files = [
                '.claude/commands/status.md',
                '.claude/commands/workflow.md',
                '.claude/commands/validate.md',
                '.claude/commands/agent.md'
            ]

            for file_path in command_files:
                assert Path(file_path).exists()

                # Check file has content
                with open(file_path) as f:
                    content = f.read()
                assert len(content) > 0

    def test_claude_context_file_created(self):
        """Init should create CLAUDE.md context file."""
        from synapse.cli.main import cli

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['init'])

            assert result.exit_code == 0
            assert Path('CLAUDE.md').exists()

            with open('CLAUDE.md') as f:
                content = f.read()

            assert 'Synapse Agent Workflow' in content
            assert 'DEV Agent' in content
            assert 'AUDITOR Agent' in content
            assert 'DISPATCHER Agent' in content

    def test_task_log_initialized(self):
        """Init should create empty task log with proper structure."""
        from synapse.cli.main import cli

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['init'])

            assert result.exit_code == 0
            assert Path('.synapse/task_log.json').exists()

            with open('.synapse/task_log.json') as f:
                log_data = json.load(f)

            assert 'workflow_id' in log_data
            assert 'entries' in log_data
            assert isinstance(log_data['entries'], list)
