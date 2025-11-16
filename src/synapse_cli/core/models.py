"""Domain models for synapse."""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from .types import ConfigDict, ManifestDict, WorkflowMode


@dataclass
class ProjectConfig:
    """Project configuration model."""
    name: str
    root_directory: Path
    synapse_version: str
    initialized_at: datetime

    @classmethod
    def from_dict(cls, data: ConfigDict) -> 'ProjectConfig':
        """Create from config dictionary."""
        return cls(
            name=data['project']['name'],
            root_directory=Path(data['project']['root_directory']),
            synapse_version=data['synapse_version'],
            initialized_at=datetime.fromisoformat(data['initialized_at'])
        )

    def to_dict(self) -> ConfigDict:
        """Convert to config dictionary."""
        return {
            'synapse_version': self.synapse_version,
            'initialized_at': self.initialized_at.isoformat(),
            'project': {
                'name': self.name,
                'root_directory': str(self.root_directory)
            }
        }


@dataclass
class WorkflowManifest:
    """Workflow manifest model."""
    workflow_name: str
    applied_at: datetime
    synapse_version: str
    files_copied: List[Dict[str, str]] = field(default_factory=list)
    hooks_added: List[Dict[str, str]] = field(default_factory=list)
    settings_updated: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: ManifestDict) -> 'WorkflowManifest':
        """Create from manifest dictionary."""
        return cls(
            workflow_name=data['workflow_name'],
            applied_at=datetime.fromisoformat(data['applied_at']),
            synapse_version=data['synapse_version'],
            files_copied=data.get('files_copied', []),
            hooks_added=data.get('hooks_added', []),
            settings_updated=data.get('settings_updated', [])
        )

    def to_dict(self) -> ManifestDict:
        """Convert to manifest dictionary."""
        return {
            'workflow_name': self.workflow_name,
            'applied_at': self.applied_at.isoformat(),
            'synapse_version': self.synapse_version,
            'files_copied': self.files_copied,
            'hooks_added': self.hooks_added,
            'settings_updated': self.settings_updated
        }


@dataclass
class WorkflowInfo:
    """Workflow metadata."""
    name: str
    description: Optional[str] = None
    version: Optional[str] = None
    path: Optional[Path] = None


@dataclass
class BackupInfo:
    """Backup metadata."""
    path: Path
    created_at: datetime
    workflow_name: Optional[str] = None
