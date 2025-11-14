"""Unit tests for infrastructure/backup_manager.py."""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime
import time
from synapse_cli.infrastructure.backup_manager import BackupManager, get_backup_manager
from synapse_cli.core.models import BackupInfo


class TestBackupManager:
    """Test BackupManager class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def backup_manager(self):
        """Create BackupManager instance for testing."""
        return BackupManager()

    @pytest.fixture
    def setup_claude_dir(self, temp_dir):
        """Create a sample .claude directory structure."""
        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir()

        # Create some test files and directories
        (claude_dir / "config.json").write_text('{"test": "config"}')

        hooks_dir = claude_dir / "hooks"
        hooks_dir.mkdir()
        (hooks_dir / "test_hook.py").write_text("# test hook")

        return claude_dir

    def test_singleton_pattern(self):
        """Test that get_backup_manager returns the same instance."""
        manager1 = get_backup_manager()
        manager2 = get_backup_manager()
        assert manager1 is manager2

    def test_get_backup_dir_default(self, backup_manager):
        """Test get_backup_dir with default target directory."""
        backup_dir = backup_manager.get_backup_dir()
        assert backup_dir == Path.cwd() / ".synapse" / "backups"

    def test_get_backup_dir_custom(self, backup_manager, temp_dir):
        """Test get_backup_dir with custom target directory."""
        backup_dir = backup_manager.get_backup_dir(temp_dir)
        assert backup_dir == temp_dir / ".synapse" / "backups"

    def test_create_backup_no_claude_dir(self, backup_manager, temp_dir):
        """Test create_backup when .claude directory doesn't exist."""
        result = backup_manager.create_backup(temp_dir)
        assert result is None

    def test_create_backup_with_claude_dir(self, backup_manager, temp_dir, setup_claude_dir):
        """Test create_backup with existing .claude directory."""
        result = backup_manager.create_backup(temp_dir)

        assert result is not None
        assert isinstance(result, BackupInfo)
        assert result.path.exists()
        assert result.path.is_dir()
        assert result.workflow_name is None
        assert isinstance(result.created_at, datetime)

        # Verify backup contains files
        assert (result.path / "config.json").exists()
        assert (result.path / "hooks" / "test_hook.py").exists()

    def test_create_backup_with_workflow_name(self, backup_manager, temp_dir, setup_claude_dir):
        """Test create_backup with workflow name."""
        result = backup_manager.create_backup(temp_dir, workflow_name="test-workflow")

        assert result is not None
        assert result.workflow_name == "test-workflow"

    def test_create_backup_creates_backup_dir(self, backup_manager, temp_dir, setup_claude_dir):
        """Test that create_backup creates the backup directory if it doesn't exist."""
        backup_dir = temp_dir / ".synapse" / "backups"
        assert not backup_dir.exists()

        result = backup_manager.create_backup(temp_dir)

        assert backup_dir.exists()
        assert result is not None

    def test_create_backup_timestamped_name(self, backup_manager, temp_dir, setup_claude_dir):
        """Test that backup directory has timestamped name."""
        result = backup_manager.create_backup(temp_dir)

        assert result is not None
        assert result.path.name.startswith("claude_backup_")
        # Check format: claude_backup_YYYYMMDD_HHMMSS
        assert len(result.path.name) == len("claude_backup_20250101_120000")

    def test_create_backup_preserves_structure(self, backup_manager, temp_dir, setup_claude_dir):
        """Test that backup preserves directory structure and file contents."""
        result = backup_manager.create_backup(temp_dir)

        assert result is not None

        # Check structure
        assert (result.path / "config.json").exists()
        assert (result.path / "hooks").is_dir()
        assert (result.path / "hooks" / "test_hook.py").exists()

        # Check contents
        config_content = (result.path / "config.json").read_text()
        assert config_content == '{"test": "config"}'

        hook_content = (result.path / "hooks" / "test_hook.py").read_text()
        assert hook_content == "# test hook"

    def test_get_latest_backup_no_backups(self, backup_manager, temp_dir):
        """Test get_latest_backup when no backups exist."""
        result = backup_manager.get_latest_backup(temp_dir)
        assert result is None

    def test_get_latest_backup_no_backup_dir(self, backup_manager, temp_dir):
        """Test get_latest_backup when backup directory doesn't exist."""
        result = backup_manager.get_latest_backup(temp_dir)
        assert result is None

    def test_get_latest_backup_single_backup(self, backup_manager, temp_dir, setup_claude_dir):
        """Test get_latest_backup with single backup."""
        # Create a backup
        created = backup_manager.create_backup(temp_dir)

        # Get latest
        result = backup_manager.get_latest_backup(temp_dir)

        assert result is not None
        assert result.path == created.path

    def test_get_latest_backup_multiple_backups(self, backup_manager, temp_dir, setup_claude_dir):
        """Test get_latest_backup returns most recent backup."""
        # Create first backup
        first = backup_manager.create_backup(temp_dir)

        # Wait to ensure different timestamps (minimum 1 second for timestamp format)
        time.sleep(1.1)

        # Create second backup
        second = backup_manager.create_backup(temp_dir)

        # Get latest should return second
        result = backup_manager.get_latest_backup(temp_dir)

        assert result is not None
        assert result.path == second.path
        assert result.path != first.path

    def test_get_latest_backup_ignores_non_backup_dirs(self, backup_manager, temp_dir, setup_claude_dir):
        """Test get_latest_backup ignores directories that don't match backup pattern."""
        backup_root = temp_dir / ".synapse" / "backups"
        backup_root.mkdir(parents=True)

        # Create a non-backup directory
        (backup_root / "other_dir").mkdir()
        (backup_root / "other_dir" / "file.txt").write_text("test")

        # Should return None since no valid backups
        result = backup_manager.get_latest_backup(temp_dir)
        assert result is None

    def test_restore_from_backup_missing_backup(self, backup_manager, temp_dir):
        """Test restore_from_backup with non-existent backup."""
        fake_backup = temp_dir / "nonexistent"
        result = backup_manager.restore_from_backup(fake_backup, temp_dir)
        assert result is False

    def test_restore_from_backup_success(self, backup_manager, temp_dir, setup_claude_dir):
        """Test restore_from_backup successfully restores backup."""
        # Create backup
        backup_info = backup_manager.create_backup(temp_dir)
        assert backup_info is not None

        # Modify .claude directory
        claude_dir = temp_dir / ".claude"
        (claude_dir / "config.json").write_text('{"modified": "config"}')
        (claude_dir / "new_file.txt").write_text("new content")

        # Restore from backup
        result = backup_manager.restore_from_backup(backup_info.path, temp_dir)
        assert result is True

        # Verify original content is restored
        assert (claude_dir / "config.json").read_text() == '{"test": "config"}'
        assert not (claude_dir / "new_file.txt").exists()

    def test_restore_from_backup_removes_existing_claude(self, backup_manager, temp_dir, setup_claude_dir):
        """Test restore_from_backup removes existing .claude directory."""
        # Create backup
        backup_info = backup_manager.create_backup(temp_dir)
        assert backup_info is not None

        # Add extra content to .claude
        claude_dir = temp_dir / ".claude"
        (claude_dir / "extra_file.txt").write_text("extra")
        extra_dir = claude_dir / "extra_dir"
        extra_dir.mkdir()
        (extra_dir / "extra.txt").write_text("extra")

        # Restore
        result = backup_manager.restore_from_backup(backup_info.path, temp_dir)
        assert result is True

        # Verify extra content is removed
        assert not (claude_dir / "extra_file.txt").exists()
        assert not (claude_dir / "extra_dir").exists()

    def test_restore_from_backup_creates_claude_if_missing(self, backup_manager, temp_dir, setup_claude_dir):
        """Test restore_from_backup creates .claude directory if it doesn't exist."""
        # Create backup
        backup_info = backup_manager.create_backup(temp_dir)
        assert backup_info is not None

        # Remove .claude directory
        claude_dir = temp_dir / ".claude"
        import shutil
        shutil.rmtree(claude_dir)
        assert not claude_dir.exists()

        # Restore
        result = backup_manager.restore_from_backup(backup_info.path, temp_dir)
        assert result is True

        # Verify .claude is restored
        assert claude_dir.exists()
        assert (claude_dir / "config.json").exists()
