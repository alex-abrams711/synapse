"""Resource and workflow discovery."""
from pathlib import Path
from typing import List, Optional
import json
import sys

from ..core.models import WorkflowInfo


class ResourceManager:
    """Manages package resources and workflow discovery."""

    def __init__(self):
        self._resources_dir: Optional[Path] = None
        self._workflows_dir: Optional[Path] = None

    @property
    def resources_dir(self) -> Path:
        """
        Get the resources directory from the installed package.

        Returns:
            Path to resources directory

        Raises:
            SystemExit: If resources directory cannot be found
        """
        if self._resources_dir is None:
            self._resources_dir = self._locate_resources()
        return self._resources_dir

    @property
    def workflows_dir(self) -> Path:
        """
        Get the workflows directory from resources.

        Returns:
            Path to workflows directory

        Raises:
            SystemExit: If workflows directory cannot be found
        """
        if self._workflows_dir is None:
            self._workflows_dir = self.resources_dir / "workflows"
            if not self._workflows_dir.exists():
                print(f"Error: Workflows directory not found", file=sys.stderr)
                sys.exit(1)
        return self._workflows_dir

    def _locate_resources(self) -> Path:
        """
        Locate resources directory with fallback logic.

        Returns:
            Path to resources directory

        Raises:
            SystemExit: If resources directory cannot be found
        """
        package_dir = Path(__file__).parent.parent

        # Try editable install location
        resources_dir = package_dir.parent.parent / "resources"
        if resources_dir.exists():
            return resources_dir

        # Try wheel install location
        resources_dir = package_dir.parent / "synapse_resources"
        if resources_dir.exists():
            return resources_dir

        print(f"Error: Resources directory not found.", file=sys.stderr)
        sys.exit(1)

    def discover_workflows(self) -> List[str]:
        """
        Discover available workflows.

        Returns:
            List of workflow names
        """
        workflows = []
        for item in self.workflows_dir.iterdir():
            if item.is_dir() and (item / "settings.json").exists():
                workflows.append(item.name)
        return sorted(workflows)

    def get_workflow_info(self, workflow_name: str) -> Optional[WorkflowInfo]:
        """
        Get workflow metadata.

        Args:
            workflow_name: Name of the workflow

        Returns:
            WorkflowInfo object if found, None otherwise
        """
        settings_file = self.workflows_dir / workflow_name / "settings.json"

        if not settings_file.exists():
            return None

        try:
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                metadata = settings.get("workflow_metadata", {})

                return WorkflowInfo(
                    name=workflow_name,
                    description=metadata.get("description"),
                    version=metadata.get("version"),
                    path=self.workflows_dir / workflow_name
                )
        except (json.JSONDecodeError, IOError):
            return None

    def validate_workflow_exists(self, workflow_name: str) -> bool:
        """
        Validate that a workflow exists.

        Args:
            workflow_name: Name of the workflow to validate

        Returns:
            True if workflow exists and has settings.json, False otherwise
        """
        workflow_dir = self.workflows_dir / workflow_name
        return workflow_dir.is_dir() and (workflow_dir / "settings.json").exists()


# Singleton instance
_resource_manager = ResourceManager()


def get_resource_manager() -> ResourceManager:
    """Get the global resource manager instance."""
    return _resource_manager
