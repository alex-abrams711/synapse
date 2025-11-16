"""Unit tests for services/workflow_service.py."""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from synapse_cli.services.workflow_service import WorkflowService, get_workflow_service
from synapse_cli.core.models import WorkflowInfo, BackupInfo
from datetime import datetime


class TestWorkflowService:
    """Test WorkflowService class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def workflow_service(self):
        """Create WorkflowService instance with mocked dependencies."""
        service = WorkflowService("0.3.0")
        service.resource_manager = Mock()
        service.config_store = Mock()
        service.manifest_store = Mock()
        service.backup_manager = Mock()
        service.file_ops = Mock()
        service.settings_service = Mock()
        service.validation_service = Mock()
        return service

    def test_list_workflows(self, workflow_service):
        """Test list_workflows returns WorkflowInfo objects."""
        workflow_service.resource_manager.discover_workflows.return_value = [
            "workflow1", "workflow2"
        ]
        workflow_service.resource_manager.get_workflow_info.side_effect = [
            WorkflowInfo(name="workflow1", description="Test 1"),
            WorkflowInfo(name="workflow2", description="Test 2")
        ]

        workflows = workflow_service.list_workflows()

        assert len(workflows) == 2
        assert workflows[0].name == "workflow1"
        assert workflows[1].name == "workflow2"

    def test_list_workflows_filters_none(self, workflow_service):
        """Test list_workflows filters out workflows that return None."""
        workflow_service.resource_manager.discover_workflows.return_value = [
            "workflow1", "invalid"
        ]
        workflow_service.resource_manager.get_workflow_info.side_effect = [
            WorkflowInfo(name="workflow1"),
            None  # Invalid workflow
        ]

        workflows = workflow_service.list_workflows()

        assert len(workflows) == 1
        assert workflows[0].name == "workflow1"

    def test_get_workflow_status_with_config_and_manifest(
        self, workflow_service, temp_dir
    ):
        """Test get_workflow_status with both config and manifest."""
        config = {
            'workflows': {
                'active_workflow': 'test-workflow',
                'applied_workflows': [{'name': 'test-workflow'}]
            }
        }
        manifest = Mock()

        workflow_service.config_store.load.return_value = config
        workflow_service.manifest_store.load.return_value = manifest

        status = workflow_service.get_workflow_status(temp_dir)

        assert status['active_workflow'] == 'test-workflow'
        assert len(status['applied_workflows']) == 1
        assert status['manifest'] == manifest
        assert status['has_config'] is True
        assert status['has_manifest'] is True

    def test_get_workflow_status_no_config(self, workflow_service, temp_dir):
        """Test get_workflow_status with no config."""
        workflow_service.config_store.load.return_value = None
        workflow_service.manifest_store.load.return_value = None

        status = workflow_service.get_workflow_status(temp_dir)

        assert status['active_workflow'] is None
        assert status['applied_workflows'] == []
        assert status['has_config'] is False
        assert status['has_manifest'] is False

    def test_apply_workflow_success(self, workflow_service, temp_dir):
        """Test apply_workflow with successful application."""
        # Setup mocks
        workflow_info = WorkflowInfo(name="test-workflow", description="Test")
        backup_info = BackupInfo(path=temp_dir / "backup", created_at=datetime.now())

        workflow_service.resource_manager.get_workflow_info.return_value = workflow_info
        workflow_service.backup_manager.create_backup.return_value = backup_info
        workflow_service.manifest_store.exists.return_value = False  # No existing workflow
        workflow_service.settings_service.merge_settings_json.return_value = {
            'merged': True,
            'created': False,
            'hooks_added': [],
            'settings_updated': [],
            'error': None
        }
        workflow_service.manifest_store.save.return_value = True
        workflow_service.config_store.update_workflow_tracking.return_value = True

        # Mock _apply_workflow_directories
        workflow_service._apply_workflow_directories = Mock(return_value={})

        result = workflow_service.apply_workflow("test-workflow", temp_dir)

        assert result is True
        workflow_service.validation_service.validate_workflow_preconditions.assert_called_once()
        workflow_service.backup_manager.create_backup.assert_called_once()
        workflow_service.manifest_store.save.assert_called_once()

    def test_apply_workflow_no_info(self, workflow_service, temp_dir):
        """Test apply_workflow when workflow info cannot be loaded."""
        workflow_service.resource_manager.get_workflow_info.return_value = None

        result = workflow_service.apply_workflow("test-workflow", temp_dir)

        assert result is False

    def test_apply_workflow_merge_error(self, workflow_service, temp_dir):
        """Test apply_workflow when settings merge fails."""
        workflow_info = WorkflowInfo(name="test-workflow")

        workflow_service.resource_manager.get_workflow_info.return_value = workflow_info
        workflow_service.backup_manager.create_backup.return_value = None
        workflow_service.manifest_store.exists.return_value = False  # No existing workflow
        workflow_service._apply_workflow_directories = Mock(return_value={})
        workflow_service.settings_service.merge_settings_json.return_value = {
            'merged': False,
            'error': "Merge failed"
        }

        result = workflow_service.apply_workflow("test-workflow", temp_dir)

        assert result is False

    def test_apply_workflow_force_mode(self, workflow_service, temp_dir):
        """Test apply_workflow with force=True."""
        workflow_info = WorkflowInfo(name="test-workflow")

        workflow_service.resource_manager.get_workflow_info.return_value = workflow_info
        workflow_service.backup_manager.create_backup.return_value = None
        workflow_service.manifest_store.exists.return_value = False  # No existing workflow
        workflow_service.settings_service.merge_settings_json.return_value = {
            'merged': True,
            'created': False,
            'hooks_added': [],
            'settings_updated': [],
            'error': None
        }
        workflow_service.manifest_store.save.return_value = True
        workflow_service.config_store.update_workflow_tracking.return_value = True

        # Mock the private method to capture force parameter
        apply_dirs_mock = Mock(return_value={})
        workflow_service._apply_workflow_directories = apply_dirs_mock

        result = workflow_service.apply_workflow("test-workflow", temp_dir, force=True)

        # Verify force was passed
        apply_dirs_mock.assert_called_once_with("test-workflow", temp_dir, True)

    def test_apply_workflow_directories(self, workflow_service, temp_dir):
        """Test _apply_workflow_directories copies files correctly."""
        # Setup workflow directory
        workflows_dir = temp_dir / "workflows"
        workflow_dir = workflows_dir / "test-workflow"
        workflow_dir.mkdir(parents=True)

        # Create source directories
        (workflow_dir / "agents").mkdir()
        (workflow_dir / "hooks").mkdir()
        (workflow_dir / "commands" / "synapse").mkdir(parents=True)

        # Create test files
        (workflow_dir / "agents" / "test.py").write_text("test")
        (workflow_dir / "hooks" / "test.sh").write_text("#!/bin/bash")

        type(workflow_service.resource_manager).workflows_dir = PropertyMock(return_value=workflows_dir)

        # Mock file_ops
        workflow_service.file_ops.copy_directory_with_conflicts.return_value = (
            [temp_dir / ".claude" / "agents" / "test.py"],
            [],
            []
        )

        results = workflow_service._apply_workflow_directories("test-workflow", temp_dir, False)

        assert "agents" in results
        assert "hooks" in results
        assert "commands" in results

    def test_display_copy_results(self, workflow_service, temp_dir, capsys):
        """Test _display_copy_results prints correctly."""
        results = {
            "agents": (
                [temp_dir / "file1.py", temp_dir / "file2.py"],
                [temp_dir / "skipped.py"],
                []
            ),
            "hooks": ([], [], []),
            "commands": ([], [], [])
        }

        workflow_service._display_copy_results(results)

        captured = capsys.readouterr()
        assert "Agents:" in captured.out
        assert "Copied 2 file(s):" in captured.out
        assert "Skipped 1 file(s):" in captured.out

    def test_display_merge_results_created(self, workflow_service, temp_dir, capsys):
        """Test _display_merge_results for new settings.json."""
        result = {
            'merged': True,
            'created': True,
            'hooks_added': [{'command': 'test.py'}],
            'settings_updated': ['key1', 'key2']
        }

        workflow_service._display_merge_results(result, temp_dir)

        captured = capsys.readouterr()
        assert "Created settings.json" in captured.out
        assert "Added 1 hook(s)" in captured.out
        assert "Updated: key1, key2" in captured.out

    def test_display_merge_results_merged(self, workflow_service, temp_dir, capsys):
        """Test _display_merge_results for merged settings.json."""
        result = {
            'merged': True,
            'created': False,
            'hooks_added': [],
            'settings_updated': []
        }

        workflow_service._display_merge_results(result, temp_dir)

        captured = capsys.readouterr()
        assert "Merged settings into" in captured.out

    def test_display_merge_results_no_settings(self, workflow_service, temp_dir, capsys):
        """Test _display_merge_results when workflow has no settings."""
        result = {
            'merged': False,
            'created': False,
            'hooks_added': [],
            'settings_updated': []
        }

        workflow_service._display_merge_results(result, temp_dir)

        captured = capsys.readouterr()
        assert "No settings.json in workflow" in captured.out

    def test_factory_function(self):
        """Test get_workflow_service factory function."""
        service = get_workflow_service("0.3.0")
        assert isinstance(service, WorkflowService)
        assert service.synapse_version == "0.3.0"

    def test_apply_workflow_replaces_existing_hooks(self, workflow_service, temp_dir):
        """Test apply_workflow removes hooks from previous workflow before applying new one."""
        from synapse_cli.core.models import WorkflowManifest
        from datetime import datetime

        # Setup existing workflow manifest with hooks
        existing_manifest = WorkflowManifest(
            workflow_name="old-workflow",
            applied_at=datetime.now(),
            synapse_version="0.3.0",
            hooks_added=[
                {'hook_type': 'Stop', 'command': '/old/hook1.py'},
                {'hook_type': 'PreToolUse', 'command': '/old/hook2.py'}
            ]
        )

        workflow_info = WorkflowInfo(name="new-workflow", description="New workflow")

        # Mock dependencies
        workflow_service.manifest_store.exists.return_value = True
        workflow_service.manifest_store.load.return_value = existing_manifest
        workflow_service.settings_service.remove_hooks_from_settings.return_value = True
        workflow_service.resource_manager.get_workflow_info.return_value = workflow_info
        workflow_service.backup_manager.create_backup.return_value = None
        workflow_service._apply_workflow_directories = Mock(return_value={})
        workflow_service.settings_service.merge_settings_json.return_value = {
            'merged': True,
            'created': False,
            'hooks_added': [{'hook_type': 'Stop', 'command': '/new/hook.py'}],
            'settings_updated': [],
            'error': None
        }
        workflow_service.manifest_store.save.return_value = True
        workflow_service.config_store.update_workflow_tracking.return_value = True

        # Apply new workflow
        result = workflow_service.apply_workflow("new-workflow", temp_dir)

        # Verify old hooks were removed
        assert result is True
        workflow_service.manifest_store.exists.assert_called_once_with(temp_dir)
        workflow_service.manifest_store.load.assert_called_once_with(temp_dir)
        workflow_service.settings_service.remove_hooks_from_settings.assert_called_once_with(
            existing_manifest.hooks_added,
            temp_dir
        )

    def test_apply_workflow_no_existing_manifest(self, workflow_service, temp_dir):
        """Test apply_workflow when no existing workflow manifest exists."""
        workflow_info = WorkflowInfo(name="new-workflow", description="New workflow")

        # Mock dependencies - no existing manifest
        workflow_service.manifest_store.exists.return_value = False
        workflow_service.resource_manager.get_workflow_info.return_value = workflow_info
        workflow_service.backup_manager.create_backup.return_value = None
        workflow_service._apply_workflow_directories = Mock(return_value={})
        workflow_service.settings_service.merge_settings_json.return_value = {
            'merged': True,
            'created': False,
            'hooks_added': [],
            'settings_updated': [],
            'error': None
        }
        workflow_service.manifest_store.save.return_value = True
        workflow_service.config_store.update_workflow_tracking.return_value = True

        # Apply workflow
        result = workflow_service.apply_workflow("new-workflow", temp_dir)

        # Verify no hook removal attempted
        assert result is True
        workflow_service.manifest_store.exists.assert_called_once_with(temp_dir)
        workflow_service.settings_service.remove_hooks_from_settings.assert_not_called()

    def test_apply_workflow_existing_manifest_no_hooks(self, workflow_service, temp_dir):
        """Test apply_workflow when existing manifest has no hooks."""
        from synapse_cli.core.models import WorkflowManifest
        from datetime import datetime

        # Existing manifest with no hooks
        existing_manifest = WorkflowManifest(
            workflow_name="old-workflow",
            applied_at=datetime.now(),
            synapse_version="0.3.0",
            hooks_added=[]  # No hooks
        )

        workflow_info = WorkflowInfo(name="new-workflow", description="New workflow")

        # Mock dependencies
        workflow_service.manifest_store.exists.return_value = True
        workflow_service.manifest_store.load.return_value = existing_manifest
        workflow_service.resource_manager.get_workflow_info.return_value = workflow_info
        workflow_service.backup_manager.create_backup.return_value = None
        workflow_service._apply_workflow_directories = Mock(return_value={})
        workflow_service.settings_service.merge_settings_json.return_value = {
            'merged': True,
            'created': False,
            'hooks_added': [],
            'settings_updated': [],
            'error': None
        }
        workflow_service.manifest_store.save.return_value = True
        workflow_service.config_store.update_workflow_tracking.return_value = True

        # Apply workflow
        result = workflow_service.apply_workflow("new-workflow", temp_dir)

        # Verify no hook removal attempted (manifest exists but has no hooks)
        assert result is True
        workflow_service.settings_service.remove_hooks_from_settings.assert_not_called()

    def test_apply_workflow_hook_removal_fails(self, workflow_service, temp_dir, capsys):
        """Test apply_workflow continues even if hook removal fails."""
        from synapse_cli.core.models import WorkflowManifest
        from datetime import datetime

        # Setup existing workflow manifest with hooks
        existing_manifest = WorkflowManifest(
            workflow_name="old-workflow",
            applied_at=datetime.now(),
            synapse_version="0.3.0",
            hooks_added=[{'hook_type': 'Stop', 'command': '/old/hook.py'}]
        )

        workflow_info = WorkflowInfo(name="new-workflow", description="New workflow")

        # Mock dependencies - hook removal fails
        workflow_service.manifest_store.exists.return_value = True
        workflow_service.manifest_store.load.return_value = existing_manifest
        workflow_service.settings_service.remove_hooks_from_settings.return_value = False  # Fails
        workflow_service.resource_manager.get_workflow_info.return_value = workflow_info
        workflow_service.backup_manager.create_backup.return_value = None
        workflow_service._apply_workflow_directories = Mock(return_value={})
        workflow_service.settings_service.merge_settings_json.return_value = {
            'merged': True,
            'created': False,
            'hooks_added': [],
            'settings_updated': [],
            'error': None
        }
        workflow_service.manifest_store.save.return_value = True
        workflow_service.config_store.update_workflow_tracking.return_value = True

        # Apply workflow
        result = workflow_service.apply_workflow("new-workflow", temp_dir)

        # Verify it continues despite hook removal failure (prints warning)
        assert result is True
        captured = capsys.readouterr()
        assert "⚠" in captured.out or "Warning" in captured.err
