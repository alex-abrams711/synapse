"""Validation service for pre-flight checks."""
from pathlib import Path
from typing import Optional
import subprocess
import sys

from ..infrastructure.config_store import get_config_store
from ..infrastructure.resources import get_resource_manager


class ValidationService:
    """Handles all validation logic."""

    def __init__(self):
        self.config_store = get_config_store()
        self.resource_manager = get_resource_manager()

    def validate_synapse_initialized(
        self,
        target_dir: Optional[Path] = None
    ) -> bool:
        """
        Check if synapse is initialized.

        Args:
            target_dir: Target directory to check (defaults to current working directory)

        Returns:
            True if synapse is initialized, False otherwise
        """
        return self.config_store.exists(target_dir)

    def validate_workflow_exists(self, workflow_name: str) -> bool:
        """
        Check if workflow exists.

        Args:
            workflow_name: Name of the workflow to check

        Returns:
            True if workflow exists, False otherwise
        """
        return self.resource_manager.validate_workflow_exists(workflow_name)

    def check_uv_available(self) -> bool:
        """
        Check if uv is installed.

        Returns:
            True if uv is available, False otherwise
        """
        try:
            result = subprocess.run(
                ['uv', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def validate_workflow_preconditions(
        self,
        workflow_name: str,
        target_dir: Optional[Path] = None
    ) -> None:
        """
        Validate all preconditions before applying workflow.

        Args:
            workflow_name: Name of the workflow to validate
            target_dir: Target directory (defaults to current working directory)

        Raises:
            SystemExit: If validation fails
        """
        if target_dir is None:
            target_dir = Path.cwd()

        # 1. Check synapse initialized
        if not self.validate_synapse_initialized(target_dir):
            print("Error: Synapse not initialized.", file=sys.stderr)
            print("Run 'synapse init' first.", file=sys.stderr)
            sys.exit(1)

        # 2. Check workflow exists
        if not self.validate_workflow_exists(workflow_name):
            print(f"Error: Workflow '{workflow_name}' not found.", file=sys.stderr)
            workflows = self.resource_manager.discover_workflows()
            if workflows:
                print("\nAvailable workflows:", file=sys.stderr)
                for wf in workflows:
                    print(f"  - {wf}", file=sys.stderr)
            sys.exit(1)

        # 3. Check uv (warning only)
        if not self.check_uv_available():
            print("Warning: 'uv' not available.", file=sys.stderr)
            print("Some features may not work.", file=sys.stderr)
            print()

        # 4. Check for workflow switch
        active = self.config_store.get_active_workflow(target_dir)
        if active and active != workflow_name:
            print(f"Warning: Will replace '{active}' with '{workflow_name}'.",
                  file=sys.stderr)
            try:
                response = input("Continue? (y/n): ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n\nCancelled.", file=sys.stderr)
                sys.exit(1)

            if response != 'y':
                print("Cancelled.", file=sys.stderr)
                sys.exit(1)
            print()

    def validate_removal_preconditions(
        self,
        target_dir: Optional[Path] = None
    ) -> None:
        """
        Validate preconditions before removing workflow.

        Args:
            target_dir: Target directory (defaults to current working directory)

        Raises:
            SystemExit: If validation fails or nothing to remove
        """
        if target_dir is None:
            target_dir = Path.cwd()

        # Check synapse initialized
        if not self.validate_synapse_initialized(target_dir):
            print("Error: Synapse not initialized.", file=sys.stderr)
            sys.exit(1)

        # Check if there's an active workflow
        active = self.config_store.get_active_workflow(target_dir)
        if not active:
            print("No active workflow to remove.", file=sys.stderr)
            print("\nTo apply a workflow:", file=sys.stderr)
            print("  synapse workflow <name>", file=sys.stderr)
            sys.exit(0)


# Singleton instance
_validation_service = ValidationService()


def get_validation_service() -> ValidationService:
    """Get the global validation service instance."""
    return _validation_service
