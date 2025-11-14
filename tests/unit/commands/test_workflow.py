"""Unit tests for WorkflowCommand."""

import pytest
from pathlib import Path
from unittest.mock import Mock
from dataclasses import dataclass

from synapse_cli.commands.workflow import WorkflowCommand
from synapse_cli.core.models import WorkflowInfo, WorkflowManifest
from synapse_cli.core.types import WorkflowMode


@dataclass
class MockWorkflowStatus:
    """Mock workflow status for testing."""
    has_active_workflow: bool
    active_workflow: str = None
    workflow_history: list = None
    manifest: WorkflowManifest = None
    has_inconsistency: bool = False

    def __post_init__(self):
        if self.workflow_history is None:
            self.workflow_history = []


class TestWorkflowCommand:
    """Tests for WorkflowCommand class."""

    @pytest.fixture
    def mock_workflow_service(self):
        """Create a mock WorkflowService."""
        return Mock()

    @pytest.fixture
    def mock_removal_service(self):
        """Create a mock RemovalService."""
        return Mock()

    @pytest.fixture
    def workflow_command(self, mock_workflow_service, mock_removal_service):
        """Create a WorkflowCommand instance with mocked dependencies."""
        return WorkflowCommand(
            synapse_version="0.1.0",
            workflow_service=mock_workflow_service,
            removal_service=mock_removal_service
        )

    def test_list_with_workflows(self, workflow_command, mock_workflow_service, capsys):
        """Test listing workflows when workflows exist."""
        mock_workflows = [
            WorkflowInfo(
                name="feature-planning",
                description="Planning workflow",
                version="1.0.0"
            ),
            WorkflowInfo(
                name="feature-implementation",
                description="Implementation workflow",
                version="1.0.0"
            )
        ]
        mock_workflow_service.list_workflows.return_value = mock_workflows

        workflow_command.list()

        captured = capsys.readouterr()
        assert "Available workflows:" in captured.out
        assert "feature-planning" in captured.out
        assert "feature-implementation" in captured.out
        assert "Planning workflow" in captured.out
        assert "Total: 2 workflow(s)" in captured.out

    def test_list_no_workflows(self, workflow_command, mock_workflow_service, capsys):
        """Test listing workflows when no workflows exist."""
        mock_workflow_service.list_workflows.return_value = []

        workflow_command.list()

        captured = capsys.readouterr()
        assert "Available workflows:" in captured.out
        assert "No workflows found." in captured.out

    def test_list_workflows_without_description(self, workflow_command, mock_workflow_service, capsys):
        """Test listing workflows without descriptions."""
        mock_workflows = [
            WorkflowInfo(name="basic-workflow", description=None, version=None)
        ]
        mock_workflow_service.list_workflows.return_value = mock_workflows

        workflow_command.list()

        captured = capsys.readouterr()
        assert "basic-workflow" in captured.out
        assert "Total: 1 workflow(s)" in captured.out

    def test_status_no_active_workflow(self, workflow_command, mock_workflow_service, capsys):
        """Test status when no active workflow exists."""
        mock_status = MockWorkflowStatus(has_active_workflow=False)
        mock_workflow_service.get_workflow_status.return_value = mock_status

        workflow_command.status()

        captured = capsys.readouterr()
        assert "No active workflow found." in captured.out
        assert "synapse workflow <name>" in captured.out

    def test_status_with_active_workflow(self, workflow_command, mock_workflow_service, capsys):
        """Test status with active workflow."""
        mock_manifest = WorkflowManifest(
            workflow_name="feature-planning",
            applied_at="2024-01-01T00:00:00",
            synapse_version="0.1.0",
            files_copied=[
                {"path": ".claude/agents/planner.py", "type": "agents"},
                {"path": ".claude/hooks/validate.sh", "type": "hooks"}
            ],
            hooks_added=[
                {"name": "validate", "trigger": "UserPromptSubmit"}
            ],
            settings_updated=["someKey"]
        )

        mock_status = MockWorkflowStatus(
            has_active_workflow=True,
            active_workflow="feature-planning",
            workflow_history=[
                {"name": "feature-planning", "applied_at": "2024-01-01T00:00:00"}
            ],
            manifest=mock_manifest
        )
        mock_workflow_service.get_workflow_status.return_value = mock_status

        workflow_command.status()

        captured = capsys.readouterr()
        assert "Active Workflow Status" in captured.out
        assert "feature-planning" in captured.out
        assert "Files Copied (2 total):" in captured.out
        assert "Hooks Added (1 total):" in captured.out

    def test_status_with_inconsistency(self, workflow_command, mock_workflow_service, capsys):
        """Test status with config/manifest inconsistency."""
        mock_manifest = WorkflowManifest(
            workflow_name="workflow-a",
            applied_at="2024-01-01T00:00:00",
            synapse_version="0.1.0",
            files_copied=[],
            hooks_added=[],
            settings_updated=[]
        )

        mock_status = MockWorkflowStatus(
            has_active_workflow=True,
            active_workflow="workflow-b",
            manifest=mock_manifest,
            has_inconsistency=True
        )
        mock_workflow_service.get_workflow_status.return_value = mock_status

        workflow_command.status()

        captured = capsys.readouterr()
        assert "WARNING: Workflow tracking inconsistency detected!" in captured.out
        assert "workflow-b" in captured.out
        assert "workflow-a" in captured.out

    def test_status_without_manifest(self, workflow_command, mock_workflow_service, capsys):
        """Test status when manifest doesn't exist."""
        mock_status = MockWorkflowStatus(
            has_active_workflow=True,
            active_workflow="feature-planning",
            manifest=None
        )
        mock_workflow_service.get_workflow_status.return_value = mock_status

        workflow_command.status()

        captured = capsys.readouterr()
        assert "Active Workflow: feature-planning" in captured.out
        assert "Warning: Workflow manifest not found." in captured.out

    def test_status_with_target_dir(self, workflow_command, mock_workflow_service, tmp_path):
        """Test status with specific target directory."""
        mock_status = MockWorkflowStatus(has_active_workflow=False)
        mock_workflow_service.get_workflow_status.return_value = mock_status

        workflow_command.status(tmp_path)

        mock_workflow_service.get_workflow_status.assert_called_once_with(tmp_path)

    def test_apply_workflow(self, workflow_command, mock_workflow_service):
        """Test applying a workflow."""
        mock_workflow_service.apply_workflow.return_value = True

        result = workflow_command.apply("feature-planning")

        assert result is True
        mock_workflow_service.apply_workflow.assert_called_once_with(
            "feature-planning",
            None,
            False
        )

    def test_apply_workflow_with_force(self, workflow_command, mock_workflow_service):
        """Test applying a workflow with force flag."""
        mock_workflow_service.apply_workflow.return_value = True

        result = workflow_command.apply("feature-planning", force=True)

        assert result is True
        mock_workflow_service.apply_workflow.assert_called_once_with(
            "feature-planning",
            None,
            True
        )

    def test_apply_workflow_with_target_dir(self, workflow_command, mock_workflow_service, tmp_path):
        """Test applying a workflow with specific target directory."""
        mock_workflow_service.apply_workflow.return_value = True

        result = workflow_command.apply("feature-planning", target_dir=tmp_path)

        assert result is True
        mock_workflow_service.apply_workflow.assert_called_once_with(
            "feature-planning",
            tmp_path,
            False
        )

    def test_apply_workflow_failure(self, workflow_command, mock_workflow_service):
        """Test applying a workflow that fails."""
        mock_workflow_service.apply_workflow.return_value = False

        result = workflow_command.apply("feature-planning")

        assert result is False

    def test_remove_workflow(self, workflow_command, mock_removal_service):
        """Test removing a workflow."""
        mock_removal_service.remove_workflow.return_value = True

        result = workflow_command.remove()

        assert result is True
        mock_removal_service.remove_workflow.assert_called_once_with(None)

    def test_remove_workflow_with_target_dir(self, workflow_command, mock_removal_service, tmp_path):
        """Test removing a workflow with specific target directory."""
        mock_removal_service.remove_workflow.return_value = True

        result = workflow_command.remove(target_dir=tmp_path)

        assert result is True
        mock_removal_service.remove_workflow.assert_called_once_with(tmp_path)

    def test_remove_workflow_failure(self, workflow_command, mock_removal_service):
        """Test removing a workflow that fails."""
        mock_removal_service.remove_workflow.return_value = False

        result = workflow_command.remove()

        assert result is False

    def test_status_with_empty_manifest_lists(self, workflow_command, mock_workflow_service, capsys):
        """Test status with empty manifest lists."""
        mock_manifest = WorkflowManifest(
            workflow_name="feature-planning",
            applied_at="2024-01-01T00:00:00",
            synapse_version="0.1.0",
            files_copied=[],
            hooks_added=[],
            settings_updated=[]
        )

        mock_status = MockWorkflowStatus(
            has_active_workflow=True,
            active_workflow="feature-planning",
            manifest=mock_manifest
        )
        mock_workflow_service.get_workflow_status.return_value = mock_status

        workflow_command.status()

        captured = capsys.readouterr()
        assert "No files copied" in captured.out
        assert "No hooks added" in captured.out
        assert "No settings updated" in captured.out
