"""Manifest persistence."""
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

from .persistence import JsonStore
from ..core.models import WorkflowManifest
from ..core.types import ManifestDict


class ManifestStore:
    """Handles workflow-manifest.json persistence."""

    def __init__(self, synapse_version: str):
        self._store = JsonStore[ManifestDict](".synapse", "workflow-manifest.json")
        self._synapse_version = synapse_version

    def get_path(self, target_dir: Optional[Path] = None) -> Path:
        """
        Get path to manifest file.

        Args:
            target_dir: Target directory (defaults to current working directory)

        Returns:
            Path to workflow-manifest.json
        """
        return self._store.get_path(target_dir)

    def load(self, target_dir: Optional[Path] = None) -> Optional[WorkflowManifest]:
        """
        Load manifest file.

        Args:
            target_dir: Target directory (defaults to current working directory)

        Returns:
            WorkflowManifest if file exists, None otherwise
        """
        data = self._store.load(target_dir)
        if data is None:
            return None

        return WorkflowManifest.from_dict(data)

    def save(
        self,
        manifest: WorkflowManifest,
        target_dir: Optional[Path] = None
    ) -> bool:
        """
        Save manifest file.

        Args:
            manifest: WorkflowManifest to save
            target_dir: Target directory (defaults to current working directory)

        Returns:
            True if save was successful, False otherwise
        """
        return self._store.save(manifest.to_dict(), target_dir)

    def exists(self, target_dir: Optional[Path] = None) -> bool:
        """
        Check if manifest exists.

        Args:
            target_dir: Target directory (defaults to current working directory)

        Returns:
            True if manifest exists, False otherwise
        """
        return self._store.exists(target_dir)

    def create_manifest(
        self,
        workflow_name: str,
        copied_files: Dict[str, List[Path]],
        hooks_added: List[Dict],
        settings_updated: List[str],
        target_dir: Optional[Path] = None
    ) -> WorkflowManifest:
        """
        Create a new workflow manifest.

        Args:
            workflow_name: Name of the workflow
            copied_files: Dict mapping directory types to lists of copied file paths
            hooks_added: List of hook dicts with 'name' and 'path' keys
            settings_updated: List of setting names that were updated
            target_dir: Target directory (defaults to current working directory)

        Returns:
            New WorkflowManifest instance
        """
        if target_dir is None:
            target_dir = Path.cwd()

        # Flatten copied files
        all_copied = []
        for dir_type, file_list in copied_files.items():
            for file_path in file_list:
                try:
                    rel_path = file_path.relative_to(target_dir)
                    all_copied.append({
                        'path': str(rel_path),
                        'type': dir_type
                    })
                except ValueError:
                    all_copied.append({
                        'path': str(file_path),
                        'type': dir_type
                    })

        return WorkflowManifest(
            workflow_name=workflow_name,
            applied_at=datetime.now(),
            synapse_version=self._synapse_version,
            files_copied=all_copied,
            hooks_added=hooks_added,
            settings_updated=settings_updated
        )

    def delete(self, target_dir: Optional[Path] = None) -> bool:
        """
        Delete manifest file.

        Args:
            target_dir: Target directory (defaults to current working directory)

        Returns:
            True if delete was successful or file doesn't exist, False on error
        """
        path = self.get_path(target_dir)
        if path.exists():
            try:
                path.unlink()
                return True
            except IOError:
                return False
        return True


# Factory function
def get_manifest_store(synapse_version: str) -> ManifestStore:
    """Get a manifest store instance."""
    return ManifestStore(synapse_version)
