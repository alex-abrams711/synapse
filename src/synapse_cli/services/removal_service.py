"""Workflow removal service."""
from pathlib import Path
from typing import Optional, Dict, List
import sys

from ..infrastructure.config_store import get_config_store
from ..infrastructure.manifest_store import get_manifest_store
from ..infrastructure.backup_manager import get_backup_manager
from ..infrastructure.file_operations import get_file_operations
from ..services.settings_service import get_settings_service
from ..core.models import WorkflowManifest


class RemovalService:
    """Handles workflow removal."""

    def __init__(self, synapse_version: str):
        self.synapse_version = synapse_version
        self.config_store = get_config_store()
        self.manifest_store = get_manifest_store(synapse_version)
        self.backup_manager = get_backup_manager()
        self.file_ops = get_file_operations()
        self.settings_service = get_settings_service()

    def remove_workflow(
        self,
        target_dir: Optional[Path] = None
    ) -> bool:
        """
        Remove current workflow.

        Args:
            target_dir: Target project directory

        Returns:
            True if successful
        """
        if target_dir is None:
            target_dir = Path.cwd()

        # Load state
        manifest = self.manifest_store.load(target_dir)
        latest_backup = self.backup_manager.get_latest_backup(target_dir)

        # Display what will be removed
        self._display_removal_plan(manifest, latest_backup)

        # Confirm
        if not self._confirm_removal():
            return False

        print("\nRemoving workflow...")

        # Try backup restoration first
        removal_success = False
        if latest_backup:
            print(f"\nRestoring from backup: {latest_backup.path}")
            if self.backup_manager.restore_from_backup(latest_backup.path, target_dir):
                print("  ✓ Restored from backup")
                removal_success = True
            else:
                print("  ✗ Backup restoration failed")

        # Alternative: selective removal using manifest
        if not removal_success and manifest:
            print("\nSelective removal using manifest...")
            if self._remove_from_manifest(manifest, target_dir):
                print("  ✓ Removed using manifest")
                removal_success = True
            else:
                print("  ✗ Selective removal failed")

        # Clear tracking
        print("\nClearing workflow tracking...")
        if self.config_store.clear_workflow_tracking(target_dir):
            print("  ✓ Tracking cleared")
        else:
            print("  ⚠ Could not clear tracking", file=sys.stderr)

        # Remove manifest
        if removal_success:
            if self.manifest_store.delete(target_dir):
                print("  ✓ Manifest removed")

        print("\n" + "=" * 60)
        if removal_success:
            print("Workflow removed successfully!")
        else:
            print("Workflow removal incomplete. Manual cleanup may be required.")
            self._display_manual_cleanup_instructions()

        return removal_success

    def _remove_from_manifest(
        self,
        manifest: WorkflowManifest,
        target_dir: Path
    ) -> bool:
        """Remove files tracked in manifest."""
        files_removed = 0
        files_failed = 0

        # Remove files
        if manifest.files_copied:
            print(f"    Removing {len(manifest.files_copied)} files...")
            for file_info in manifest.files_copied:
                file_path = Path(file_info['path'])
                if not file_path.is_absolute():
                    file_path = target_dir / file_path

                if file_path.exists():
                    try:
                        file_path.unlink()
                        files_removed += 1
                        print(f"      - {file_info['path']}")
                    except IOError:
                        files_failed += 1

        # Remove hooks
        if manifest.hooks_added:
            print(f"    Removing {len(manifest.hooks_added)} hooks...")
            if self.settings_service.remove_hooks_from_settings(
                manifest.hooks_added,
                target_dir
            ):
                print("      ✓ Hooks removed")
            else:
                files_failed += 1

        # Cleanup empty directories
        print("    Cleaning up empty directories...")
        self.file_ops.cleanup_empty_directories(target_dir / ".claude")

        return files_failed == 0

    def _display_removal_plan(self, manifest, backup) -> None:
        """Display what will be removed."""
        print("Workflow Removal")
        print("=" * 60)

        if manifest:
            print(f"\nWorkflow: {manifest.workflow_name}")
            print(f"  Files: {len(manifest.files_copied)}")
            print(f"  Hooks: {len(manifest.hooks_added)}")
            print(f"  Settings: {len(manifest.settings_updated)}")

        if backup:
            print(f"\nBackup available: {backup.path}")
            print("  Will restore from backup (recommended)")
        else:
            print("\nNo backup found")
            if manifest:
                print("  Will attempt selective removal using manifest")

    def _confirm_removal(self) -> bool:
        """Confirm removal with user."""
        print("\n" + "=" * 60)
        try:
            response = input("\nProceed with removal? (y/n): ").strip().lower()
            return response == 'y'
        except (EOFError, KeyboardInterrupt):
            print("\n\nOperation cancelled.")
            return False

    def _display_manual_cleanup_instructions(self) -> None:
        """Display manual cleanup instructions."""
        print("\nFiles that may need manual cleanup:")
        print("  - Files in .claude/agents/")
        print("  - Files in .claude/hooks/")
        print("  - Files in .claude/commands/synapse/")
        print("  - Hook configurations in .claude/settings.json")


# Factory function
def get_removal_service(synapse_version: str) -> RemovalService:
    """Get a removal service instance."""
    return RemovalService(synapse_version)
