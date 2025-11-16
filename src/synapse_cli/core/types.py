"""Type definitions and enums."""
from enum import Enum
from typing import TypedDict, List, Dict, Optional


class WorkflowMode(Enum):
    """Workflow configuration mode."""
    SINGLE = "single"
    MONOREPO = "monorepo"


class ExitCode(Enum):
    """Standard exit codes for hooks."""
    SUCCESS = 0
    SHOW_MESSAGE = 1
    BLOCK = 2


class ConfigDict(TypedDict, total=False):
    """Type definition for config.json structure."""
    synapse_version: str
    initialized_at: str
    project: Dict[str, str]
    agent: Dict[str, str]
    workflows: Dict[str, any]
    quality_config: Dict[str, any]
    third_party_workflow: Optional[Dict[str, any]]


class ManifestDict(TypedDict):
    """Type definition for workflow-manifest.json structure."""
    workflow_name: str
    applied_at: str
    synapse_version: str
    files_copied: List[Dict[str, str]]
    hooks_added: List[Dict[str, str]]
    settings_updated: List[str]
