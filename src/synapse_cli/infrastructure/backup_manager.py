"""Backup and restore management."""
from pathlib import Path
from typing import Optional
from datetime import datetime
import shutil
import sys

from ..core.models import BackupInfo


class BackupManager:
    """Manages .claude directory backups."""

    def __init__(self):
        pass

    def get_backup_dir(self, target_dir: Optional[Path] = None) -> Path:
        """
        Get the backup directory path.

        Args:
            target_dir: Target project directory (defaults to current working directory)

        Returns:
            Path to backup directory
        """
        if target_dir is None:
            target_dir = Path.cwd()
        return target_dir / ".synapse" / "backups"

    def create_backup(
        self,
        target_dir: Optional[Path] = None,
        workflow_name: Optional[str] = None
    ) -> Optional[BackupInfo]:
        """
        Create a backup of the .claude directory.

        Args:
            target_dir: Target project directory
            workflow_name: Optional workflow name for metadata

        Returns:
            BackupInfo if successful, None otherwise
        """
        if target_dir is None:
            target_dir = Path.cwd()

        claude_dir = target_dir / ".claude"

        # If .claude doesn't exist, no backup needed
        if not claude_dir.exists():
            return None

        backup_root = self.get_backup_dir(target_dir)
        backup_root.mkdir(parents=True, exist_ok=True)

        # Create timestamped backup
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        backup_dir = backup_root / f"claude_backup_{timestamp_str}"

        try:
            shutil.copytree(claude_dir, backup_dir, dirs_exist_ok=False)
            return BackupInfo(
                path=backup_dir,
                created_at=timestamp,
                workflow_name=workflow_name
            )
        except (IOError, OSError) as e:
            print(f"Warning: Could not create backup: {e}", file=sys.stderr)
            return None

    def get_latest_backup(
        self,
        target_dir: Optional[Path] = None
    ) -> Optional[BackupInfo]:
        """
        Get the most recent backup.

        Args:
            target_dir: Target project directory

        Returns:
            BackupInfo for latest backup, or None if no backups exist
        """
        if target_dir is None:
            target_dir = Path.cwd()

        backup_root = self.get_backup_dir(target_dir)

        if not backup_root.exists():
            return None

        # Find all backup directories
        backup_dirs = [
            d for d in backup_root.iterdir()
            if d.is_dir() and d.name.startswith("claude_backup_")
        ]

        if not backup_dirs:
            return None

        # Sort by directory name (which contains timestamp) - newest first
        backup_dirs.sort(key=lambda x: x.name, reverse=True)
        latest = backup_dirs[0]

        # Parse timestamp from directory name: claude_backup_YYYYMMDD_HHMMSS
        timestamp_str = latest.name.replace("claude_backup_", "")
        created_at = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

        return BackupInfo(
            path=latest,
            created_at=created_at
        )

    def restore_from_backup(
        self,
        backup_path: Path,
        target_dir: Optional[Path] = None
    ) -> bool:
        """
        Restore .claude directory from a backup.

        Args:
            backup_path: Path to backup directory
            target_dir: Target project directory

        Returns:
            True if successful, False otherwise
        """
        if target_dir is None:
            target_dir = Path.cwd()

        if not backup_path.exists():
            print(f"Error: Backup not found: {backup_path}", file=sys.stderr)
            return False

        claude_dir = target_dir / ".claude"

        try:
            # Remove existing .claude
            if claude_dir.exists():
                shutil.rmtree(claude_dir)

            # Copy backup to .claude
            shutil.copytree(backup_path, claude_dir)
            return True
        except (IOError, OSError) as e:
            print(f"Error: Could not restore backup: {e}", file=sys.stderr)
            return False


# Singleton instance
_backup_manager = BackupManager()


def get_backup_manager() -> BackupManager:
    """Get the global backup manager instance."""
    return _backup_manager
