"""Workflow commands for Synapse CLI.

Handles workflow listing, status, application, and removal.
"""

from pathlib import Path
from typing import Optional

from ..services.workflow_service import WorkflowService
from ..services.removal_service import RemovalService


class WorkflowCommand:
    """Command for managing workflows."""

    def __init__(
        self,
        synapse_version: str,
        workflow_service: Optional[WorkflowService] = None,
        removal_service: Optional[RemovalService] = None
    ):
        """Initialize the workflow command.

        Args:
            synapse_version: Version string for Synapse CLI
            workflow_service: Workflow service instance (optional, uses singleton if not provided)
            removal_service: Removal service instance (optional, uses singleton if not provided)
        """
        self.synapse_version = synapse_version

        # Use provided dependencies or fall back to singletons
        if workflow_service is None:
            from ..services.workflow_service import get_workflow_service
            workflow_service = get_workflow_service(synapse_version)
        self.workflow_service = workflow_service

        if removal_service is None:
            from ..services.removal_service import get_removal_service
            removal_service = get_removal_service(synapse_version)
        self.removal_service = removal_service

    def list(self) -> None:
        """List available workflows."""
        workflows = self.workflow_service.list_workflows()

        print("Available workflows:\n")

        if not workflows:
            print("No workflows found.")
            return

        # Display each workflow with its metadata
        for workflow_info in workflows:
            print(f"  {workflow_info.name}")

            if workflow_info.description:
                print(f"    {workflow_info.description}")

            if workflow_info.version:
                print(f"    Version: {workflow_info.version}")

            print()  # Blank line between workflows

        print(f"Total: {len(workflows)} workflow(s)")
        print("\nUse 'synapse workflow <name>' to apply a workflow.")

    def status(self, target_dir: Optional[Path] = None) -> None:
        """Show active workflow and associated artifacts.

        Args:
            target_dir: Target project directory. Defaults to current directory.
        """
        workflow_status = self.workflow_service.get_workflow_status(target_dir)

        # Check if we have any workflow information
        active_workflow = workflow_status.get('active_workflow')
        manifest = workflow_status.get('manifest')

        if not active_workflow and not manifest:
            print("No active workflow found.")
            print("\nTo apply a workflow, use:")
            print("  synapse workflow <name>")
            print("\nTo list available workflows, use:")
            print("  synapse workflow list")
            return

        print("Active Workflow Status")
        print("=" * 60)

        # Show active workflow
        if active_workflow:
            print(f"\nActive Workflow: {active_workflow}")

        # Show workflow history
        applied_workflows = workflow_status.get('applied_workflows', [])
        if applied_workflows:
            print(f"\nWorkflow History ({len(applied_workflows)} applied):")
            print("-" * 60)
            for entry in applied_workflows:
                print(f"  {entry['name']} (applied: {entry['applied_at']})")

        # Show detailed manifest information
        if manifest:
            print("\n" + "=" * 60)
            print("Detailed Workflow Artifacts")
            print("=" * 60)
            print(f"\nWorkflow: {manifest.workflow_name}")
            print(f"Applied: {manifest.applied_at}")
            print(f"Synapse Version: {manifest.synapse_version}")

            # Show copied files
            if manifest.files_copied:
                print(f"\nFiles Copied ({len(manifest.files_copied)} total):")
                print("-" * 60)

                # Group by type
                files_by_type = {}
                for file_info in manifest.files_copied:
                    file_type = file_info['type']
                    if file_type not in files_by_type:
                        files_by_type[file_type] = []
                    files_by_type[file_type].append(file_info['path'])

                for file_type in sorted(files_by_type.keys()):
                    print(f"\n{file_type.capitalize()}:")
                    for file_path in sorted(files_by_type[file_type]):
                        print(f"  {file_path}")
            else:
                print("\nNo files copied")

            # Show hooks added
            if manifest.hooks_added:
                print(f"\nHooks Added ({len(manifest.hooks_added)} total):")
                print("-" * 60)
                for hook in manifest.hooks_added:
                    hook_name = hook.get('name') or 'unnamed'
                    hook_trigger = hook.get('trigger') or hook.get('hook_type') or 'no trigger'
                    print(f"  {hook_name} ({hook_trigger})")
            else:
                print("\nNo hooks added")

            # Show settings updated
            if manifest.settings_updated:
                print(f"\nSettings Updated ({len(manifest.settings_updated)} keys):")
                print("-" * 60)
                for setting in sorted(manifest.settings_updated):
                    print(f"  {setting}")
            else:
                print("\nNo settings updated")
        else:
            print("\n" + "=" * 60)
            print("\nWarning: Workflow manifest not found.")
            print("Detailed artifact tracking is not available.")

        # Warn if config and manifest are out of sync
        if active_workflow and manifest and active_workflow != manifest.workflow_name:
            print("\n" + "=" * 60)
            print("WARNING: Workflow tracking inconsistency detected!")
            print(f"  Config shows: {active_workflow}")
            print(f"  Manifest shows: {manifest.workflow_name}")
            print("  Consider re-applying the workflow to fix this.")

        print("\n" + "=" * 60)
        print("\nTo remove this workflow, use:")
        print("  synapse workflow remove")

    def apply(
        self,
        workflow_name: str,
        target_dir: Optional[Path] = None,
        force: bool = False
    ) -> bool:
        """Apply a workflow to the project.

        Args:
            workflow_name: Name of the workflow to apply
            target_dir: Target project directory. Defaults to current directory.
            force: Force overwrite of existing files

        Returns:
            True if successful, False otherwise
        """
        return self.workflow_service.apply_workflow(
            workflow_name,
            target_dir,
            force
        )

    def remove(self, target_dir: Optional[Path] = None) -> bool:
        """Remove current workflow.

        Args:
            target_dir: Target project directory. Defaults to current directory.

        Returns:
            True if successful, False otherwise
        """
        return self.removal_service.remove_workflow(target_dir)


# Singleton instance
_workflow_command_instance: Optional[WorkflowCommand] = None


def get_workflow_command(synapse_version: str) -> WorkflowCommand:
    """Get or create the singleton WorkflowCommand instance.

    Args:
        synapse_version: Version string for Synapse CLI

    Returns:
        The singleton WorkflowCommand instance
    """
    global _workflow_command_instance
    if _workflow_command_instance is None:
        _workflow_command_instance = WorkflowCommand(synapse_version)
    return _workflow_command_instance
