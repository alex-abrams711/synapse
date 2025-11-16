"""Configuration persistence."""
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

from .persistence import JsonStore
from ..core.models import ProjectConfig
from ..core.types import ConfigDict


class ConfigStore:
    """Handles config.json persistence and workflow tracking."""

    def __init__(self):
        self._store = JsonStore[ConfigDict](".synapse", "config.json")

    def get_path(self, target_dir: Optional[Path] = None) -> Path:
        """
        Get path to config.json.

        Args:
            target_dir: Target directory (defaults to current working directory)

        Returns:
            Path to config.json
        """
        return self._store.get_path(target_dir)

    def load(self, target_dir: Optional[Path] = None) -> Optional[ConfigDict]:
        """
        Load config.json.

        Args:
            target_dir: Target directory (defaults to current working directory)

        Returns:
            ConfigDict if file exists, None otherwise
        """
        return self._store.load(target_dir)

    def save(self, config: ConfigDict, target_dir: Optional[Path] = None) -> bool:
        """
        Save config.json.

        Args:
            config: Configuration data to save
            target_dir: Target directory (defaults to current working directory)

        Returns:
            True if save was successful, False otherwise
        """
        return self._store.save(config, target_dir)

    def exists(self, target_dir: Optional[Path] = None) -> bool:
        """
        Check if synapse is initialized.

        Args:
            target_dir: Target directory (defaults to current working directory)

        Returns:
            True if config.json exists, False otherwise
        """
        return self._store.exists(target_dir)

    def update_workflow_tracking(
        self,
        workflow_name: str,
        target_dir: Optional[Path] = None
    ) -> bool:
        """
        Update active workflow in config.

        Args:
            workflow_name: Name of the workflow to track
            target_dir: Target directory (defaults to current working directory)

        Returns:
            True if update was successful, False otherwise
        """
        config = self.load(target_dir)
        if config is None:
            return False

        # Update active workflow
        if 'workflows' not in config:
            config['workflows'] = {}

        config['workflows']['active_workflow'] = workflow_name

        # Add to history
        workflow_entry = {
            'name': workflow_name,
            'applied_at': datetime.now().isoformat()
        }

        applied = config['workflows'].get('applied_workflows', [])
        if not any(w.get('name') == workflow_name for w in applied):
            applied.append(workflow_entry)
            config['workflows']['applied_workflows'] = applied

        return self.save(config, target_dir)

    def clear_workflow_tracking(self, target_dir: Optional[Path] = None) -> bool:
        """
        Clear active workflow from config.

        Args:
            target_dir: Target directory (defaults to current working directory)

        Returns:
            True if clear was successful, False otherwise
        """
        config = self.load(target_dir)
        if config is None:
            return False

        if 'workflows' in config:
            config['workflows']['active_workflow'] = None

        return self.save(config, target_dir)

    def get_active_workflow(self, target_dir: Optional[Path] = None) -> Optional[str]:
        """
        Get the currently active workflow.

        Args:
            target_dir: Target directory (defaults to current working directory)

        Returns:
            Name of active workflow, or None if no active workflow
        """
        config = self.load(target_dir)
        if config is None:
            return None

        return config.get('workflows', {}).get('active_workflow')


# Singleton instance
_config_store = ConfigStore()


def get_config_store() -> ConfigStore:
    """Get the global config store instance."""
    return _config_store
