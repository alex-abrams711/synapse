"""Unit tests for services/removal_service.py."""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime
from synapse_cli.services.removal_service import RemovalService, get_removal_service
from synapse_cli.core.models import WorkflowManifest, BackupInfo


class TestRemovalService:
    """Test RemovalService class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def removal_service(self):
        """Create RemovalService instance with mocked dependencies."""
        service = RemovalService("0.3.0")
        service.config_store = Mock()
        service.manifest_store = Mock()
        service.backup_manager = Mock()
        service.file_ops = Mock()
        service.settings_service = Mock()
        return service

    @pytest.fixture
    def sample_manifest(self):
        """Create sample manifest for testing."""
        return WorkflowManifest(
            workflow_name="test-workflow",
            applied_at=datetime.now(),
            synapse_version="0.3.0",
            files_copied=[
                {'path': '.claude/agents/test.py', 'type': 'agents'},
                {'path': '.claude/hooks/test.sh', 'type': 'hooks'}
            ],
            hooks_added=[
                {'command': 'test.py', 'hook_type': 'user_prompt_submit'}
            ],
            settings_updated=['key1']
        )

    def test_remove_workflow_with_backup(
        self, removal_service, temp_dir, sample_manifest
    ):
        """Test remove_workflow using backup restoration."""
        backup = BackupInfo(path=temp_dir / "backup", created_at=datetime.now())

        removal_service.manifest_store.load.return_value = sample_manifest
        removal_service.backup_manager.get_latest_backup.return_value = backup
        removal_service.backup_manager.restore_from_backup.return_value = True
        removal_service.config_store.clear_workflow_tracking.return_value = True
        removal_service.manifest_store.delete.return_value = True

        with patch('builtins.input', return_value='y'):
            result = removal_service.remove_workflow(temp_dir)

        assert result is True
        removal_service.backup_manager.restore_from_backup.assert_called_once_with(
            backup.path, temp_dir
        )
        removal_service.manifest_store.delete.assert_called_once()

    def test_remove_workflow_with_manifest_fallback(
        self, removal_service, temp_dir, sample_manifest
    ):
        """Test remove_workflow using manifest when no backup."""
        removal_service.manifest_store.load.return_value = sample_manifest
        removal_service.backup_manager.get_latest_backup.return_value = None
        removal_service.config_store.clear_workflow_tracking.return_value = True
        removal_service.manifest_store.delete.return_value = True

        # Mock _remove_from_manifest
        removal_service._remove_from_manifest = Mock(return_value=True)

        with patch('builtins.input', return_value='y'):
            result = removal_service.remove_workflow(temp_dir)

        assert result is True
        removal_service._remove_from_manifest.assert_called_once_with(
            sample_manifest, temp_dir
        )

    def test_remove_workflow_user_cancels(
        self, removal_service, temp_dir, sample_manifest
    ):
        """Test remove_workflow when user cancels."""
        removal_service.manifest_store.load.return_value = sample_manifest
        removal_service.backup_manager.get_latest_backup.return_value = None

        with patch('builtins.input', return_value='n'):
            result = removal_service.remove_workflow(temp_dir)

        assert result is False
        # Should not call any removal methods
        removal_service.backup_manager.restore_from_backup.assert_not_called()

    def test_remove_workflow_backup_fails(
        self, removal_service, temp_dir, sample_manifest
    ):
        """Test remove_workflow when backup restoration fails."""
        backup = BackupInfo(path=temp_dir / "backup", created_at=datetime.now())

        removal_service.manifest_store.load.return_value = sample_manifest
        removal_service.backup_manager.get_latest_backup.return_value = backup
        removal_service.backup_manager.restore_from_backup.return_value = False
        removal_service.config_store.clear_workflow_tracking.return_value = True

        # Mock _remove_from_manifest as fallback
        removal_service._remove_from_manifest = Mock(return_value=True)

        with patch('builtins.input', return_value='y'):
            result = removal_service.remove_workflow(temp_dir)

        # Should try backup first, then fallback to manifest
        removal_service.backup_manager.restore_from_backup.assert_called_once()
        removal_service._remove_from_manifest.assert_called_once()

    def test_remove_workflow_no_backup_no_manifest(
        self, removal_service, temp_dir
    ):
        """Test remove_workflow when neither backup nor manifest exists."""
        removal_service.manifest_store.load.return_value = None
        removal_service.backup_manager.get_latest_backup.return_value = None
        removal_service.config_store.clear_workflow_tracking.return_value = True

        with patch('builtins.input', return_value='y'):
            result = removal_service.remove_workflow(temp_dir)

        assert result is False

    def test_remove_from_manifest_success(
        self, removal_service, temp_dir, sample_manifest
    ):
        """Test _remove_from_manifest removes all files successfully."""
        # Create test files
        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir()
        (claude_dir / "agents").mkdir()
        (claude_dir / "hooks").mkdir()

        test_file1 = claude_dir / "agents" / "test.py"
        test_file2 = claude_dir / "hooks" / "test.sh"
        test_file1.write_text("test")
        test_file2.write_text("test")

        removal_service.settings_service.remove_hooks_from_settings.return_value = True

        result = removal_service._remove_from_manifest(sample_manifest, temp_dir)

        assert result is True
        assert not test_file1.exists()
        assert not test_file2.exists()
        removal_service.file_ops.cleanup_empty_directories.assert_called_once()

    def test_remove_from_manifest_file_removal_fails(
        self, removal_service, temp_dir, sample_manifest
    ):
        """Test _remove_from_manifest when file removal fails."""
        # Don't create files, so they won't exist to be removed
        removal_service.settings_service.remove_hooks_from_settings.return_value = True

        result = removal_service._remove_from_manifest(sample_manifest, temp_dir)

        # Should still succeed since missing files are ok
        assert result is True

    def test_remove_from_manifest_hooks_removal_fails(
        self, removal_service, temp_dir, sample_manifest
    ):
        """Test _remove_from_manifest when hooks removal fails."""
        removal_service.settings_service.remove_hooks_from_settings.return_value = False

        result = removal_service._remove_from_manifest(sample_manifest, temp_dir)

        assert result is False

    def test_remove_from_manifest_absolute_paths(
        self, removal_service, temp_dir
    ):
        """Test _remove_from_manifest with absolute file paths."""
        # Create file with absolute path
        test_file = temp_dir / "test_file.txt"
        test_file.write_text("test")

        manifest = WorkflowManifest(
            workflow_name="test",
            applied_at=datetime.now(),
            synapse_version="0.3.0",
            files_copied=[{'path': str(test_file), 'type': 'test'}],
            hooks_added=[],
            settings_updated=[]
        )

        result = removal_service._remove_from_manifest(manifest, temp_dir)

        assert result is True
        assert not test_file.exists()

    def test_display_removal_plan_with_manifest_and_backup(
        self, removal_service, sample_manifest, temp_dir, capsys
    ):
        """Test _display_removal_plan with both manifest and backup."""
        backup = BackupInfo(path=temp_dir / "backup", created_at=datetime.now())

        removal_service._display_removal_plan(sample_manifest, backup)

        captured = capsys.readouterr()
        assert "Workflow Removal" in captured.out
        assert "test-workflow" in captured.out
        assert "Files: 2" in captured.out
        assert "Hooks: 1" in captured.out
        assert "Backup available" in captured.out
        assert "Will restore from backup" in captured.out

    def test_display_removal_plan_no_backup(
        self, removal_service, sample_manifest, capsys
    ):
        """Test _display_removal_plan with no backup."""
        removal_service._display_removal_plan(sample_manifest, None)

        captured = capsys.readouterr()
        assert "No backup found" in captured.out
        assert "Will attempt selective removal" in captured.out

    def test_display_removal_plan_no_manifest(
        self, removal_service, capsys
    ):
        """Test _display_removal_plan with no manifest."""
        removal_service._display_removal_plan(None, None)

        captured = capsys.readouterr()
        assert "Workflow Removal" in captured.out
        assert "No backup found" in captured.out

    def test_confirm_removal_yes(self, removal_service):
        """Test _confirm_removal when user confirms."""
        with patch('builtins.input', return_value='y'):
            result = removal_service._confirm_removal()
        assert result is True

    def test_confirm_removal_no(self, removal_service):
        """Test _confirm_removal when user declines."""
        with patch('builtins.input', return_value='n'):
            result = removal_service._confirm_removal()
        assert result is False

    def test_confirm_removal_eof(self, removal_service):
        """Test _confirm_removal on EOF."""
        with patch('builtins.input', side_effect=EOFError()):
            result = removal_service._confirm_removal()
        assert result is False

    def test_confirm_removal_interrupt(self, removal_service):
        """Test _confirm_removal on keyboard interrupt."""
        with patch('builtins.input', side_effect=KeyboardInterrupt()):
            result = removal_service._confirm_removal()
        assert result is False

    def test_display_manual_cleanup_instructions(
        self, removal_service, capsys
    ):
        """Test _display_manual_cleanup_instructions."""
        removal_service._display_manual_cleanup_instructions()

        captured = capsys.readouterr()
        assert "manual cleanup" in captured.out
        assert ".claude/agents/" in captured.out
        assert ".claude/hooks/" in captured.out
        assert ".claude/commands/synapse/" in captured.out
        assert "settings.json" in captured.out

    def test_factory_function(self):
        """Test get_removal_service factory function."""
        service = get_removal_service("0.3.0")
        assert isinstance(service, RemovalService)
        assert service.synapse_version == "0.3.0"
