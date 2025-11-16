"""End-to-end tests for CLI commands.

Tests the CLI by invoking it via subprocess, simulating actual user interaction.
"""

import json
import pytest
import subprocess
import sys
from pathlib import Path


@pytest.fixture
def test_project(tmp_path):
    """Create a test project directory."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


def run_synapse_cli(*args, cwd=None, input_text=None):
    """Helper to run synapse CLI commands.

    Args:
        *args: CLI arguments
        cwd: Working directory
        input_text: Text to provide as stdin (for interactive prompts)

    Returns:
        Tuple of (stdout, stderr, returncode)
    """
    cmd = [sys.executable, "-m", "synapse_cli"] + list(args)

    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        input=input_text
    )

    return result.stdout, result.stderr, result.returncode


class TestCLIHelp:
    """Tests for CLI help and version commands."""

    def test_help_command(self):
        """Test that --help works."""
        stdout, stderr, code = run_synapse_cli("--help")

        assert code == 0
        assert "Synapse" in stdout
        assert "usage:" in stdout.lower()
        assert "init" in stdout
        assert "workflow" in stdout

    def test_no_command_shows_help(self):
        """Test that running with no command shows help."""
        stdout, stderr, code = run_synapse_cli()

        assert code == 1
        # Help should be shown in either stdout or stderr
        output = stdout + stderr
        assert "usage:" in output.lower()


class TestCLIInit:
    """Tests for 'synapse init' command."""

    def test_init_command_creates_synapse_directory(self, test_project):
        """Test that init creates .synapse directory."""
        stdout, stderr, code = run_synapse_cli(
            "init",
            str(test_project),
            cwd=test_project,
            input_text="1\n"  # Select Claude Code
        )

        assert code == 0
        assert (test_project / ".synapse").exists()
        assert (test_project / ".synapse" / "config.json").exists()

    def test_init_creates_valid_config(self, test_project):
        """Test that init creates valid config.json."""
        stdout, stderr, code = run_synapse_cli(
            "init",
            str(test_project),
            cwd=test_project,
            input_text="1\n"
        )

        assert code == 0

        config_path = test_project / ".synapse" / "config.json"
        with open(config_path) as f:
            config = json.load(f)

        assert "synapse_version" in config
        assert "project" in config
        assert "agent" in config
        assert config["agent"]["type"] == "claude-code"

    def test_init_fails_if_already_initialized(self, test_project):
        """Test that init fails if .synapse already exists."""
        # Initialize once
        run_synapse_cli(
            "init",
            str(test_project),
            cwd=test_project,
            input_text="1\n"
        )

        # Try to initialize again
        stdout, stderr, code = run_synapse_cli(
            "init",
            str(test_project),
            cwd=test_project,
            input_text="1\n"
        )

        assert code == 1
        assert "already exists" in stderr.lower()


class TestCLIWorkflowList:
    """Tests for 'synapse workflow list' command."""

    def test_workflow_list_command(self):
        """Test that workflow list shows available workflows."""
        stdout, stderr, code = run_synapse_cli("workflow", "list")

        assert code == 0
        assert "Available workflows" in stdout
        assert "feature-planning" in stdout or "feature-implementation" in stdout

    def test_workflow_list_shows_count(self):
        """Test that workflow list shows workflow count."""
        stdout, stderr, code = run_synapse_cli("workflow", "list")

        assert code == 0
        assert "workflow(s)" in stdout


class TestCLIWorkflowStatus:
    """Tests for 'synapse workflow status' command."""

    def test_workflow_status_no_active_workflow(self, test_project):
        """Test workflow status when no workflow is active."""
        # Initialize project first
        run_synapse_cli(
            "init",
            str(test_project),
            cwd=test_project,
            input_text="1\n"
        )

        # Check status
        stdout, stderr, code = run_synapse_cli(
            "workflow",
            "status",
            cwd=test_project
        )

        assert code == 0
        assert "No active workflow" in stdout


class TestCLIWorkflowApply:
    """Tests for applying workflows via CLI."""

    def test_workflow_apply_requires_init(self, test_project):
        """Test that workflow apply requires initialized project."""
        stdout, stderr, code = run_synapse_cli(
            "workflow",
            "feature-planning",
            cwd=test_project
        )

        # Should fail because project is not initialized
        assert code == 1

    def test_workflow_apply_success(self, test_project):
        """Test successful workflow application."""
        # Initialize project first
        run_synapse_cli(
            "init",
            str(test_project),
            cwd=test_project,
            input_text="1\n"
        )

        # Apply workflow
        stdout, stderr, code = run_synapse_cli(
            "workflow",
            "feature-planning",
            cwd=test_project
        )

        assert code == 0
        assert "successfully" in stdout.lower() or "applied" in stdout.lower()

        # Verify .claude directory was created
        assert (test_project / ".claude").exists()

        # Verify manifest was created
        assert (test_project / ".synapse" / "workflow-manifest.json").exists()


class TestCLIWorkflowRemove:
    """Tests for removing workflows via CLI."""

    def test_workflow_remove_requires_active_workflow(self, test_project):
        """Test that remove requires an active workflow."""
        # Initialize project
        run_synapse_cli(
            "init",
            str(test_project),
            cwd=test_project,
            input_text="1\n"
        )

        # Try to remove without applying a workflow
        stdout, stderr, code = run_synapse_cli(
            "workflow",
            "remove",
            cwd=test_project
        )

        assert code == 1

    def test_workflow_remove_success(self, test_project):
        """Test successful workflow removal."""
        # Initialize project
        run_synapse_cli(
            "init",
            str(test_project),
            cwd=test_project,
            input_text="1\n"
        )

        # Apply workflow
        run_synapse_cli(
            "workflow",
            "feature-planning",
            cwd=test_project
        )

        # Remove workflow (confirm with 'y')
        stdout, stderr, code = run_synapse_cli(
            "workflow",
            "remove",
            cwd=test_project,
            input_text="y\n"
        )

        assert code == 0

        # Verify manifest was deleted
        assert not (test_project / ".synapse" / "workflow-manifest.json").exists()

    def test_workflow_remove_can_be_cancelled(self, test_project):
        """Test that workflow removal can be cancelled."""
        # Initialize and apply workflow
        run_synapse_cli(
            "init",
            str(test_project),
            cwd=test_project,
            input_text="1\n"
        )

        run_synapse_cli(
            "workflow",
            "feature-planning",
            cwd=test_project
        )

        # Try to remove but cancel with 'n'
        stdout, stderr, code = run_synapse_cli(
            "workflow",
            "remove",
            cwd=test_project,
            input_text="n\n"
        )

        # Should return non-zero since removal was cancelled
        assert code == 1

        # Manifest should still exist
        assert (test_project / ".synapse" / "workflow-manifest.json").exists()


class TestCLIWorkflowSwitching:
    """Tests for switching between workflows via CLI."""

    def test_workflow_switching_with_confirmation(self, test_project):
        """Test switching from one workflow to another."""
        # Initialize project
        run_synapse_cli(
            "init",
            str(test_project),
            cwd=test_project,
            input_text="1\n"
        )

        # Apply first workflow
        run_synapse_cli(
            "workflow",
            "feature-planning",
            cwd=test_project
        )

        # Switch to second workflow (confirm with 'y')
        stdout, stderr, code = run_synapse_cli(
            "workflow",
            "feature-implementation",
            cwd=test_project,
            input_text="y\n"
        )

        assert code == 0

        # Verify new workflow is active
        manifest_path = test_project / ".synapse" / "workflow-manifest.json"
        with open(manifest_path) as f:
            manifest = json.load(f)

        assert manifest["workflow_name"] == "feature-implementation"


class TestCLIErrorHandling:
    """Tests for CLI error handling."""

    def test_invalid_workflow_name(self, test_project):
        """Test applying a non-existent workflow."""
        # Initialize project
        run_synapse_cli(
            "init",
            str(test_project),
            cwd=test_project,
            input_text="1\n"
        )

        # Try to apply non-existent workflow
        stdout, stderr, code = run_synapse_cli(
            "workflow",
            "non-existent-workflow",
            cwd=test_project
        )

        assert code == 1
        assert "not found" in stderr.lower() or "does not exist" in stderr.lower()
