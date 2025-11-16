"""Workflow application and management service."""
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import sys

from ..infrastructure.resources import get_resource_manager
from ..infrastructure.config_store import get_config_store
from ..infrastructure.manifest_store import get_manifest_store
from ..infrastructure.backup_manager import get_backup_manager
from ..infrastructure.file_operations import get_file_operations
from ..services.settings_service import get_settings_service
from ..services.validation_service import get_validation_service
from ..core.models import WorkflowInfo, BackupInfo


class WorkflowService:
    """High-level workflow operations."""

    def __init__(self, synapse_version: str):
        self.synapse_version = synapse_version
        self.resource_manager = get_resource_manager()
        self.config_store = get_config_store()
        self.manifest_store = get_manifest_store(synapse_version)
        self.backup_manager = get_backup_manager()
        self.file_ops = get_file_operations()
        self.settings_service = get_settings_service()
        self.validation_service = get_validation_service()

    def list_workflows(self) -> List[WorkflowInfo]:
        """Get list of available workflows."""
        workflow_names = self.resource_manager.discover_workflows()
        workflows = []

        for name in workflow_names:
            info = self.resource_manager.get_workflow_info(name)
            if info:
                workflows.append(info)

        return workflows

    def get_workflow_status(
        self,
        target_dir: Optional[Path] = None
    ) -> Dict:
        """
        Get current workflow status.

        Returns:
            Dictionary with status information
        """
        if target_dir is None:
            target_dir = Path.cwd()

        config = self.config_store.load(target_dir)
        manifest = self.manifest_store.load(target_dir)

        return {
            'active_workflow': config.get('workflows', {}).get('active_workflow') if config else None,
            'applied_workflows': config.get('workflows', {}).get('applied_workflows', []) if config else [],
            'manifest': manifest,
            'has_config': config is not None,
            'has_manifest': manifest is not None
        }

    def apply_workflow(
        self,
        workflow_name: str,
        target_dir: Optional[Path] = None,
        force: bool = False
    ) -> bool:
        """
        Apply a workflow to the project.

        Args:
            workflow_name: Name of workflow to apply
            target_dir: Target project directory
            force: Force overwrite of existing files

        Returns:
            True if successful
        """
        if target_dir is None:
            target_dir = Path.cwd()

        # Validate preconditions
        self.validation_service.validate_workflow_preconditions(
            workflow_name,
            target_dir
        )

        # Get workflow info
        info = self.resource_manager.get_workflow_info(workflow_name)
        if not info:
            print(f"Error: Could not load workflow info", file=sys.stderr)
            return False

        print(f"Applying workflow: {workflow_name}")
        if info.description:
            print(f"  {info.description}")

        if force:
            print("\nForce mode enabled - will overwrite existing files")

        # Create backup
        print("\nCreating backup...")
        backup = self.backup_manager.create_backup(target_dir, workflow_name)
        if backup:
            print(f"  Backup created at: {backup.path}")
        else:
            print("  No backup needed")

        # Remove old workflow if replacing existing workflow
        print("\nChecking for existing workflow...")
        if self.manifest_store.exists(target_dir):
            existing_manifest = self.manifest_store.load(target_dir)
            if existing_manifest:
                print(f"  Replacing existing workflow: {existing_manifest.workflow_name}")

                # Remove old hooks from settings.json
                if existing_manifest.hooks_added:
                    print(f"  Removing {len(existing_manifest.hooks_added)} hook(s) from settings...")
                    if self.settings_service.remove_hooks_from_settings(
                        existing_manifest.hooks_added,
                        target_dir
                    ):
                        print("    ✓ Hooks removed from settings")
                    else:
                        print("    ⚠ Warning: Could not remove all hooks from settings", file=sys.stderr)

                # Remove old workflow files
                if existing_manifest.files_copied:
                    print(f"  Removing {len(existing_manifest.files_copied)} file(s) from previous workflow...")
                    removed_count = 0
                    failed_count = 0

                    for file_info in existing_manifest.files_copied:
                        file_path = Path(file_info['path'])
                        if not file_path.is_absolute():
                            file_path = target_dir / file_path

                        if file_path.exists():
                            try:
                                file_path.unlink()
                                removed_count += 1
                            except IOError:
                                failed_count += 1

                    if removed_count > 0:
                        print(f"    ✓ Removed {removed_count} file(s)")
                    if failed_count > 0:
                        print(f"    ⚠ Warning: Failed to remove {failed_count} file(s)", file=sys.stderr)

                    # Clean up empty directories
                    self.file_ops.cleanup_empty_directories(target_dir / ".claude")
        else:
            print("  No existing workflow found")

        # Copy workflow directories
        print("\nCopying workflow directories...")
        copy_results = self._apply_workflow_directories(
            workflow_name,
            target_dir,
            force
        )

        # Display results
        self._display_copy_results(copy_results)

        # Merge settings
        print("\n" + "=" * 60)
        print("Merging settings.json...")
        print("-" * 60)

        merge_result = self.settings_service.merge_settings_json(
            workflow_name,
            target_dir
        )

        if merge_result['error']:
            print(f"\nError: {merge_result['error']}", file=sys.stderr)
            return False

        self._display_merge_results(merge_result, target_dir)

        # Create and save manifest
        print("\n" + "=" * 60)
        print("Saving workflow manifest...")
        print("-" * 60)

        copied_files = {}
        for dir_type in ["agents", "hooks", "commands"]:
            copied, _, _ = copy_results.get(dir_type, ([], [], []))
            if copied:
                copied_files[dir_type] = copied

        manifest = self.manifest_store.create_manifest(
            workflow_name=workflow_name,
            copied_files=copied_files,
            hooks_added=merge_result['hooks_added'],
            settings_updated=merge_result['settings_updated'],
            target_dir=target_dir
        )

        if self.manifest_store.save(manifest, target_dir):
            print(f"\nManifest saved to {self.manifest_store.get_path(target_dir)}")
        else:
            print(f"\nWarning: Could not save manifest", file=sys.stderr)

        # Update config tracking
        print("\n" + "=" * 60)
        print("Updating workflow tracking...")
        print("-" * 60)

        if self.config_store.update_workflow_tracking(workflow_name, target_dir):
            print(f"\nWorkflow tracking updated")
            print(f"  Active workflow: {workflow_name}")
        else:
            print(f"\nWarning: Could not update tracking", file=sys.stderr)

        print("\n" + "=" * 60)
        print("Workflow applied successfully!")

        return True

    def _apply_workflow_directories(
        self,
        workflow_name: str,
        target_dir: Path,
        force: bool
    ) -> Dict[str, Tuple[List[Path], List[Path], List[Path]]]:
        """Apply workflow directories to .claude/."""
        workflow_dir = self.resource_manager.workflows_dir / workflow_name
        claude_dir = target_dir / ".claude"

        claude_dir.mkdir(parents=True, exist_ok=True)

        results = {}

        # Define mappings: (source_subdir, target_subdir, display_name)
        mappings = [
            ("agents", "agents", "agents"),
            ("hooks", "hooks", "hooks"),
            ("commands/synapse", "commands/synapse", "commands"),
        ]

        for src_subdir, dst_subdir, display_name in mappings:
            src_path = workflow_dir / src_subdir
            dst_path = claude_dir / dst_subdir

            if src_path.exists():
                copied, skipped, created = self.file_ops.copy_directory_with_conflicts(
                    src_path, dst_path, force
                )
                results[display_name] = (copied, skipped, created)

                # Make scripts executable
                if display_name == "hooks":
                    for hook_file in dst_path.glob("*.sh"):
                        hook_file.chmod(0o755)
            else:
                results[display_name] = ([], [], [])

        return results

    def _display_copy_results(self, results: Dict) -> None:
        """Display file copy results."""
        print("\nDirectory Results:")
        print("-" * 60)

        for dir_type in ["agents", "hooks", "commands"]:
            copied, skipped, _ = results.get(dir_type, ([], [], []))

            if not copied and not skipped:
                continue

            print(f"\n{dir_type.capitalize()}:")

            if copied:
                print(f"  Copied {len(copied)} file(s):")
                for file in copied:
                    print(f"    + {file}")

            if skipped:
                print(f"  Skipped {len(skipped)} file(s):")
                for file in skipped:
                    print(f"    ! {file}")

    def _display_merge_results(self, result: Dict, target_dir: Path) -> None:
        """Display settings merge results."""
        if result['merged']:
            settings_file = target_dir / ".claude" / "settings.json"
            if result['created']:
                print(f"\nCreated settings.json at {settings_file}")
            else:
                print(f"\nMerged settings into {settings_file}")

            if result['hooks_added']:
                print(f"  Added {len(result['hooks_added'])} hook(s)")

            if result['settings_updated']:
                print(f"  Updated: {', '.join(result['settings_updated'])}")
        else:
            print("\nNo settings.json in workflow")


# Factory function
def get_workflow_service(synapse_version: str) -> WorkflowService:
    """Get a workflow service instance."""
    return WorkflowService(synapse_version)
