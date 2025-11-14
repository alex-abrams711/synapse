# Synapse CLI Modularization Proposal
## Ultra-Deep Analysis and Refactoring Strategy

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [Proposed Architecture](#proposed-architecture)
4. [Module Design Details](#module-design-details)
5. [Dependency Graph](#dependency-graph)
6. [Migration Strategy](#migration-strategy)
7. [Testing Strategy](#testing-strategy)
8. [Risk Analysis](#risk-analysis)
9. [Implementation Roadmap](#implementation-roadmap)
10. [Code Examples](#code-examples)

---

## Executive Summary

**Problem**: The `__init__.py` file has grown to 1,823 lines with 40 functions, making it difficult to maintain, test, and extend.

**Solution**: Refactor into a clean, layered architecture with 8 focused modules organized by responsibility and dependency direction.

**Benefits**:
- ✅ Improved testability (isolated modules, easier mocking)
- ✅ Better maintainability (clear boundaries, single responsibility)
- ✅ Enhanced extensibility (plugin architecture for workflows)
- ✅ Reduced coupling (explicit dependencies, interfaces)
- ✅ Easier onboarding (clear module purposes)

**Effort**: ~3-5 days for careful refactoring with comprehensive testing

---

## Current State Analysis

### Complexity Metrics

```
Total Lines:           1,823
Total Functions:       40
Average Function Size: 45.6 lines
Longest Function:      ~200+ lines (workflow_apply)
Module Coupling:       HIGH (everything in one file)
Testability:           MEDIUM (can test, but awkward)
```

### Problem Areas

1. **God Object Anti-Pattern**: Single file does everything
2. **Hidden Dependencies**: Function calls not explicit from imports
3. **Testing Challenges**: Must import entire module to test one function
4. **Cognitive Load**: 1,800+ lines to understand for any change
5. **Merge Conflicts**: High risk with multiple developers
6. **Circular Logic**: Config and manifest logic intertwined

### Current Functional Groupings

| Category | Functions | Lines | Complexity |
|----------|-----------|-------|------------|
| Resource Management | 2 | 50 | Low |
| Workflow Discovery | 3 | 54 | Low |
| Config Persistence | 5 | 218 | Medium |
| Manifest Persistence | 5 | 226 | Medium |
| Backup Management | 4 | 118 | Medium |
| Workflow Removal | 3 | 159 | High |
| Validation | 6 | 155 | Medium |
| Initialization | 2 | 99 | Low |
| Workflow Commands | 3 | 244 | High |
| File Operations | 1 | 58 | Low |
| Settings Management | 2 | 224 | High |
| Workflow Application | 2 | 205 | Very High |
| Quality Validation | 1 | 23 | Low |
| CLI Entry Point | 1 | 79 | Medium |

---

## Proposed Architecture

### Architectural Principles

We'll use a **Clean Architecture** approach with clear dependency direction:

```
┌─────────────────────────────────────────────────┐
│              CLI Layer (Interface)               │
│         commands/, cli.py (79 lines)             │
└────────────────┬────────────────────────────────┘
                 │ depends on ↓
┌────────────────▼────────────────────────────────┐
│           Service Layer (Use Cases)              │
│  workflows/, initialization/ (~700 lines)        │
└────────────────┬────────────────────────────────┘
                 │ depends on ↓
┌────────────────▼────────────────────────────────┐
│         Infrastructure Layer (I/O)               │
│  persistence/, resources/ (~600 lines)           │
└────────────────┬────────────────────────────────┘
                 │ depends on ↓
┌────────────────▼────────────────────────────────┐
│            Core Layer (Models)                   │
│        models/, types.py (~200 lines)            │
└─────────────────────────────────────────────────┘
```

### New Directory Structure

```
src/synapse_cli/
├── __init__.py                 # Package exports only (20 lines)
├── __main__.py                 # Entry point (unchanged)
│
├── core/                       # LAYER 1: Core domain
│   ├── __init__.py
│   ├── types.py               # Type definitions, enums
│   └── models.py              # Domain models (Config, Manifest, etc.)
│
├── infrastructure/             # LAYER 2: Infrastructure
│   ├── __init__.py
│   ├── resources.py           # Resource/workflow discovery
│   ├── persistence.py         # Base persistence layer
│   ├── config_store.py        # Config read/write
│   ├── manifest_store.py      # Manifest read/write
│   ├── backup_manager.py      # Backup/restore operations
│   └── file_operations.py     # File copying, path utilities
│
├── services/                   # LAYER 3: Business logic
│   ├── __init__.py
│   ├── workflow_service.py    # Workflow operations
│   ├── settings_service.py    # Settings merging
│   ├── removal_service.py     # Cleanup operations
│   └── validation_service.py  # All validation logic
│
├── commands/                   # LAYER 4: CLI commands
│   ├── __init__.py
│   ├── init.py               # synapse init
│   ├── workflow.py           # synapse workflow
│   └── validate.py           # synapse validate-quality
│
├── cli.py                      # CLI setup and dispatch
│
└── parsers/                    # Existing parser module (unchanged)
    ├── __init__.py
    ├── task_schema_parser.py
    ├── schema_generator.py
    └── schema_validator.py
```

---

## Module Design Details

### 1. Core Layer (`core/`)

**Purpose**: Pure domain models and types, no I/O or side effects

#### `core/types.py` (~50 lines)
```python
"""Type definitions and enums."""
from enum import Enum
from typing import TypedDict, List, Dict, Optional
from pathlib import Path

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
```

#### `core/models.py` (~150 lines)
```python
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
```

---

### 2. Infrastructure Layer (`infrastructure/`)

**Purpose**: Handle all I/O operations, file system access, and external integrations

#### `infrastructure/resources.py` (~100 lines)
```python
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
        """Get the resources directory from the installed package."""
        if self._resources_dir is None:
            self._resources_dir = self._locate_resources()
        return self._resources_dir

    @property
    def workflows_dir(self) -> Path:
        """Get the workflows directory from resources."""
        if self._workflows_dir is None:
            self._workflows_dir = self.resources_dir / "workflows"
            if not self._workflows_dir.exists():
                print(f"Error: Workflows directory not found", file=sys.stderr)
                sys.exit(1)
        return self._workflows_dir

    def _locate_resources(self) -> Path:
        """Locate resources directory with fallback logic."""
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
        """Discover available workflows."""
        workflows = []
        for item in self.workflows_dir.iterdir():
            if item.is_dir() and (item / "settings.json").exists():
                workflows.append(item.name)
        return sorted(workflows)

    def get_workflow_info(self, workflow_name: str) -> Optional[WorkflowInfo]:
        """Get workflow metadata."""
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
        """Validate that a workflow exists."""
        workflow_dir = self.workflows_dir / workflow_name
        return workflow_dir.is_dir() and (workflow_dir / "settings.json").exists()

# Singleton instance
_resource_manager = ResourceManager()

def get_resource_manager() -> ResourceManager:
    """Get the global resource manager instance."""
    return _resource_manager
```

#### `infrastructure/persistence.py` (~80 lines)
```python
"""Base persistence layer."""
from pathlib import Path
from typing import Optional, TypeVar, Generic, Dict
import json
import sys

T = TypeVar('T')

class JsonStore(Generic[T]):
    """Generic JSON file storage."""

    def __init__(self, base_dir: str, filename: str):
        """
        Initialize JSON store.

        Args:
            base_dir: Directory name (e.g., ".synapse")
            filename: File name (e.g., "config.json")
        """
        self.base_dir = base_dir
        self.filename = filename

    def get_path(self, target_dir: Optional[Path] = None) -> Path:
        """Get full path to the JSON file."""
        if target_dir is None:
            target_dir = Path.cwd()
        return target_dir / self.base_dir / self.filename

    def exists(self, target_dir: Optional[Path] = None) -> bool:
        """Check if file exists."""
        return self.get_path(target_dir).exists()

    def load(self, target_dir: Optional[Path] = None) -> Optional[Dict]:
        """Load JSON file."""
        path = self.get_path(target_dir)

        if not path.exists():
            return None

        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not read {path}: {e}", file=sys.stderr)
            return None

    def save(self, data: Dict, target_dir: Optional[Path] = None) -> bool:
        """Save JSON file."""
        path = self.get_path(target_dir)

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Validate can be serialized
            json_str = json.dumps(data, indent=2)

            # Write file
            with open(path, 'w') as f:
                f.write(json_str)
                f.write('\n')
            return True
        except (TypeError, ValueError, IOError) as e:
            print(f"Error: Could not write {path}: {e}", file=sys.stderr)
            return False
```

#### `infrastructure/config_store.py` (~100 lines)
```python
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
        """Get path to config.json."""
        return self._store.get_path(target_dir)

    def load(self, target_dir: Optional[Path] = None) -> Optional[ConfigDict]:
        """Load config.json."""
        return self._store.load(target_dir)

    def save(self, config: ConfigDict, target_dir: Optional[Path] = None) -> bool:
        """Save config.json."""
        return self._store.save(config, target_dir)

    def exists(self, target_dir: Optional[Path] = None) -> bool:
        """Check if synapse is initialized."""
        return self._store.exists(target_dir)

    def update_workflow_tracking(
        self,
        workflow_name: str,
        target_dir: Optional[Path] = None
    ) -> bool:
        """Update active workflow in config."""
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
        """Clear active workflow from config."""
        config = self.load(target_dir)
        if config is None:
            return False

        if 'workflows' in config:
            config['workflows']['active_workflow'] = None

        return self.save(config, target_dir)

    def get_active_workflow(self, target_dir: Optional[Path] = None) -> Optional[str]:
        """Get the currently active workflow."""
        config = self.load(target_dir)
        if config is None:
            return None

        return config.get('workflows', {}).get('active_workflow')

# Singleton instance
_config_store = ConfigStore()

def get_config_store() -> ConfigStore:
    """Get the global config store instance."""
    return _config_store
```

#### `infrastructure/manifest_store.py` (~120 lines)
```python
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
        """Get path to manifest file."""
        return self._store.get_path(target_dir)

    def load(self, target_dir: Optional[Path] = None) -> Optional[WorkflowManifest]:
        """Load manifest file."""
        data = self._store.load(target_dir)
        if data is None:
            return None

        return WorkflowManifest.from_dict(data)

    def save(
        self,
        manifest: WorkflowManifest,
        target_dir: Optional[Path] = None
    ) -> bool:
        """Save manifest file."""
        return self._store.save(manifest.to_dict(), target_dir)

    def exists(self, target_dir: Optional[Path] = None) -> bool:
        """Check if manifest exists."""
        return self._store.exists(target_dir)

    def create_manifest(
        self,
        workflow_name: str,
        copied_files: Dict[str, List[Path]],
        hooks_added: List[Dict],
        settings_updated: List[str],
        target_dir: Optional[Path] = None
    ) -> WorkflowManifest:
        """Create a new workflow manifest."""
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
        """Delete manifest file."""
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
```

#### `infrastructure/backup_manager.py` (~150 lines)
```python
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
        """Get the backup directory path."""
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

        # Sort by modification time (newest first)
        backup_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        latest = backup_dirs[0]

        return BackupInfo(
            path=latest,
            created_at=datetime.fromtimestamp(latest.stat().st_mtime)
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
```

#### `infrastructure/file_operations.py` (~100 lines)
```python
"""File operations utilities."""
from pathlib import Path
from typing import List, Tuple
import shutil

class FileOperations:
    """Handles file copying and directory operations."""

    @staticmethod
    def copy_directory_with_conflicts(
        src_dir: Path,
        dst_dir: Path,
        force: bool = False
    ) -> Tuple[List[Path], List[Path], List[Path]]:
        """
        Copy directory contents with conflict detection.

        Args:
            src_dir: Source directory
            dst_dir: Destination directory
            force: Overwrite existing files

        Returns:
            (copied_files, skipped_files, created_dirs)
        """
        copied_files: List[Path] = []
        skipped_files: List[Path] = []
        created_dirs: List[Path] = []

        # Create destination
        if not dst_dir.exists():
            dst_dir.mkdir(parents=True)
            created_dirs.append(dst_dir)

        # Walk source directory
        for src_item in src_dir.rglob("*"):
            if src_item == src_dir:
                continue

            rel_path = src_item.relative_to(src_dir)
            dst_item = dst_dir / rel_path

            if src_item.is_dir():
                if not dst_item.exists():
                    dst_item.mkdir(parents=True)
                    created_dirs.append(dst_item)
            else:
                if dst_item.exists():
                    if force:
                        shutil.copy2(src_item, dst_item)
                        copied_files.append(dst_item)
                    else:
                        skipped_files.append(dst_item)
                else:
                    shutil.copy2(src_item, dst_item)
                    copied_files.append(dst_item)

        return copied_files, skipped_files, created_dirs

    @staticmethod
    def cleanup_empty_directories(root_dir: Path) -> None:
        """Recursively remove empty directories."""
        if not root_dir.exists() or not root_dir.is_dir():
            return

        try:
            all_dirs = []
            for dir_path in root_dir.rglob("*"):
                if dir_path.is_dir():
                    all_dirs.append(dir_path)

            # Sort by depth (deepest first)
            all_dirs.sort(key=lambda x: len(x.parts), reverse=True)

            for dir_path in all_dirs:
                if dir_path.exists() and dir_path.is_dir():
                    try:
                        if dir_path != root_dir and not any(dir_path.iterdir()):
                            dir_path.rmdir()
                    except OSError:
                        pass
        except Exception:
            pass

# Singleton instance
_file_ops = FileOperations()

def get_file_operations() -> FileOperations:
    """Get the global file operations instance."""
    return _file_ops
```

---

### 3. Services Layer (`services/`)

**Purpose**: Business logic, use cases, orchestration

#### `services/validation_service.py` (~200 lines)
```python
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
        """Check if synapse is initialized."""
        return self.config_store.exists(target_dir)

    def validate_workflow_exists(self, workflow_name: str) -> bool:
        """Check if workflow exists."""
        return self.resource_manager.validate_workflow_exists(workflow_name)

    def check_uv_available(self) -> bool:
        """Check if uv is installed."""
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
```

#### `services/settings_service.py` (~250 lines)
```python
"""Settings merging and management."""
from pathlib import Path
from typing import Optional, Dict, List, Any
import json
import re
import sys

from ..infrastructure.resources import get_resource_manager

class SettingsService:
    """Handles settings.json merging and hook path conversion."""

    def __init__(self):
        self.resource_manager = get_resource_manager()

    def convert_hook_paths_to_absolute(
        self,
        hooks_config: Dict,
        target_dir: Path
    ) -> Dict:
        """
        Convert relative .claude/ paths to absolute in hook commands.

        Args:
            hooks_config: Hooks configuration from settings.json
            target_dir: Target project directory

        Returns:
            Modified hooks_config with absolute paths
        """
        for hook_type, matchers in hooks_config.items():
            for matcher_group in matchers:
                for hook in matcher_group.get('hooks', []):
                    if 'command' in hook:
                        command = hook['command']

                        # Pattern: .claude/... paths
                        pattern = r'(^|\s)(\.claude/[^\s]+)'

                        def replace_with_absolute(match):
                            prefix = match.group(1)
                            relative_path = match.group(2)
                            absolute_path = str((target_dir / relative_path).resolve())
                            return f"{prefix}{absolute_path}"

                        hook['command'] = re.sub(pattern, replace_with_absolute, command)

        return hooks_config

    def merge_settings_json(
        self,
        workflow_name: str,
        target_dir: Path
    ) -> Dict[str, Any]:
        """
        Merge workflow settings.json with existing settings.

        Args:
            workflow_name: Workflow to apply
            target_dir: Target project directory

        Returns:
            Dictionary with merge results:
            {
                'merged': bool,
                'created': bool,
                'hooks_added': list,
                'settings_updated': list,
                'error': str or None
            }
        """
        workflow_dir = self.resource_manager.workflows_dir / workflow_name
        workflow_settings_file = workflow_dir / "settings.json"

        result = {
            'merged': False,
            'created': False,
            'hooks_added': [],
            'settings_updated': [],
            'error': None
        }

        # If no settings.json, nothing to merge
        if not workflow_settings_file.exists():
            return result

        # Load workflow settings
        try:
            with open(workflow_settings_file, 'r') as f:
                workflow_settings = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            result['error'] = f"Invalid workflow settings: {e}"
            return result

        # Convert hook paths
        if 'hooks' in workflow_settings:
            workflow_settings['hooks'] = self.convert_hook_paths_to_absolute(
                workflow_settings['hooks'],
                target_dir
            )

        # Load existing settings
        claude_dir = target_dir / ".claude"
        target_settings_file = claude_dir / "settings.json"

        claude_dir.mkdir(parents=True, exist_ok=True)

        existing_settings = {}
        if target_settings_file.exists():
            try:
                with open(target_settings_file, 'r') as f:
                    existing_settings = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                result['error'] = f"Invalid existing settings: {e}"
                return result
        else:
            result['created'] = True

        # Merge settings
        merged_settings = existing_settings.copy()

        # Special handling for hooks
        if 'hooks' in workflow_settings:
            hooks_added = self._merge_hooks(
                workflow_settings['hooks'],
                merged_settings.setdefault('hooks', {})
            )
            result['hooks_added'] = hooks_added

        # Merge other settings
        for key, value in workflow_settings.items():
            if key != 'hooks':
                if key not in merged_settings or merged_settings[key] != value:
                    merged_settings[key] = value
                    result['settings_updated'].append(key)

        # Save merged settings
        try:
            with open(target_settings_file, 'w') as f:
                json.dump(merged_settings, f, indent=2)
                f.write('\n')
        except IOError as e:
            result['error'] = f"Could not write settings: {e}"
            return result

        result['merged'] = True
        return result

    def _merge_hooks(
        self,
        workflow_hooks: Dict,
        existing_hooks: Dict
    ) -> List[Dict]:
        """
        Merge workflow hooks into existing hooks.

        Returns:
            List of hooks that were added
        """
        hooks_added = []

        for hook_type, workflow_matchers in workflow_hooks.items():
            if hook_type not in existing_hooks:
                existing_hooks[hook_type] = []

            existing_matchers = existing_hooks[hook_type]

            # Track existing commands
            existing_commands = set()
            for matcher_group in existing_matchers:
                for hook in matcher_group.get('hooks', []):
                    if 'command' in hook:
                        existing_commands.add(hook['command'])

            # Merge workflow matchers
            for workflow_matcher in workflow_matchers:
                matcher_pattern = workflow_matcher.get('matcher', '')

                # Find existing matcher group
                matching_group = None
                for existing_matcher in existing_matchers:
                    if existing_matcher.get('matcher', '') == matcher_pattern:
                        matching_group = existing_matcher
                        break

                # Create new group if needed
                if matching_group is None:
                    matching_group = {
                        'matcher': matcher_pattern,
                        'hooks': []
                    }
                    existing_matchers.append(matching_group)

                # Add workflow hooks (avoid duplicates)
                for workflow_hook in workflow_matcher.get('hooks', []):
                    command = workflow_hook.get('command', '')
                    if command and command not in existing_commands:
                        matching_group['hooks'].append(workflow_hook)
                        existing_commands.add(command)
                        hooks_added.append({
                            'hook_type': hook_type,
                            'matcher': matcher_pattern,
                            'command': command,
                            'type': workflow_hook.get('type', 'command')
                        })

        return hooks_added

    def remove_hooks_from_settings(
        self,
        hooks_to_remove: List[Dict],
        target_dir: Path
    ) -> bool:
        """
        Remove specific hooks from settings.json.

        Args:
            hooks_to_remove: List of hook definitions to remove
            target_dir: Target project directory

        Returns:
            True if successful
        """
        settings_file = target_dir / ".claude" / "settings.json"

        if not settings_file.exists():
            return True

        try:
            with open(settings_file, 'r') as f:
                settings = json.load(f)

            if 'hooks' not in settings:
                return True

            hooks = settings['hooks']

            # Commands to remove
            commands_to_remove = {
                hook.get('command', '') for hook in hooks_to_remove
                if hook.get('command')
            }

            # Remove hooks
            for hook_type, matchers in hooks.items():
                for matcher_group in matchers:
                    original_hooks = matcher_group.get('hooks', [])
                    filtered_hooks = [
                        hook for hook in original_hooks
                        if hook.get('command', '') not in commands_to_remove
                    ]
                    matcher_group['hooks'] = filtered_hooks

            # Clean up empty groups and types
            for hook_type in list(hooks.keys()):
                hooks[hook_type] = [
                    mg for mg in hooks[hook_type] if mg.get('hooks')
                ]
                if not hooks[hook_type]:
                    del hooks[hook_type]

            # Save
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
                f.write('\n')

            return True
        except (json.JSONDecodeError, IOError):
            return False

# Singleton instance
_settings_service = SettingsService()

def get_settings_service() -> SettingsService:
    """Get the global settings service instance."""
    return _settings_service
```

(Continuing in next message due to length...)

#### `services/workflow_service.py` (~300 lines)
```python
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
```

#### `services/removal_service.py` (~200 lines)
```python
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

        # Fallback to selective removal
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
                print("  Will attempt selective removal (fallback)")

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
```

---

### 4. Commands Layer (`commands/`)

**Purpose**: CLI command handlers, user interaction

#### `commands/init.py` (~120 lines)
```python
"""Synapse initialization command."""
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
import sys
import json

from ..infrastructure.resources import get_resource_manager
from ..infrastructure.config_store import get_config_store

class InitCommand:
    """Handles 'synapse init' command."""

    def __init__(self, synapse_version: str):
        self.synapse_version = synapse_version
        self.resource_manager = get_resource_manager()
        self.config_store = get_config_store()

    def execute(self, target_dir: Optional[Path] = None) -> None:
        """
        Initialize synapse in a directory.

        Args:
            target_dir: Directory to initialize (default: current)
        """
        if target_dir is None:
            target_dir = Path.cwd()

        # Check if already initialized
        if self.config_store.exists(target_dir):
            print(f"Error: Already initialized at {target_dir}", file=sys.stderr)
            print("Remove .synapse directory first.", file=sys.stderr)
            sys.exit(1)

        print(f"Initializing synapse in {target_dir}")

        # Prompt for agent selection
        agent_info = self._prompt_agent_selection()

        # Create config
        config = self._create_config(target_dir, agent_info)

        # Save config
        if self.config_store.save(config, target_dir):
            print(f"  ✓ Created config.json")
            print(f"  ✓ Configured AI agent: {agent_info['type']}")
        else:
            print(f"  Error: Could not create config", file=sys.stderr)
            sys.exit(1)

        print(f"\nSynapse initialized successfully!")
        print(f"\nDirectory structure:")
        print(f"  .synapse/")
        print(f"  └── config.json")
        print(f"\nUse 'synapse workflow <name>' to apply workflows.")

    def _prompt_agent_selection(self) -> Dict[str, str]:
        """Prompt user to select AI agent."""
        print("\nSelect your AI coding assistant:")
        print("  1. Claude Code")
        print("  2. None")
        print()

        while True:
            try:
                choice = input("Enter your choice (1 or 2): ").strip()

                if choice == "1":
                    return {
                        "type": "claude-code",
                        "description": "Claude Code AI coding assistant"
                    }
                elif choice == "2":
                    print("\nError: Synapse requires an AI assistant.", file=sys.stderr)
                    sys.exit(1)
                else:
                    print("Invalid choice. Enter 1 or 2.", file=sys.stderr)
            except (EOFError, KeyboardInterrupt):
                print("\n\nCancelled.", file=sys.stderr)
                sys.exit(1)

    def _create_config(
        self,
        target_dir: Path,
        agent_info: Dict[str, str]
    ) -> Dict:
        """Create initial config dictionary."""
        return {
            'synapse_version': self.synapse_version,
            'initialized_at': datetime.now().isoformat(),
            'project': {
                'name': target_dir.name,
                'root_directory': str(target_dir.absolute())
            },
            'agent': {
                'type': agent_info['type'],
                'description': agent_info['description']
            },
            'workflows': {
                'active_workflow': None,
                'applied_workflows': []
            },
            'quality-config': {},
            'third_party_workflow': None
        }

# Factory function
def get_init_command(synapse_version: str) -> InitCommand:
    """Get an init command instance."""
    return InitCommand(synapse_version)
```

#### `commands/workflow.py` (~200 lines)
```python
"""Workflow management commands."""
from pathlib import Path
from typing import Optional
import sys

from ..services.workflow_service import get_workflow_service
from ..services.removal_service import get_removal_service
from ..services.validation_service import get_validation_service

class WorkflowCommand:
    """Handles 'synapse workflow' commands."""

    def __init__(self, synapse_version: str):
        self.synapse_version = synapse_version
        self.workflow_service = get_workflow_service(synapse_version)
        self.removal_service = get_removal_service(synapse_version)
        self.validation_service = get_validation_service()

    def list(self) -> None:
        """List available workflows."""
        print("Available workflows:\n")

        workflows = self.workflow_service.list_workflows()

        if not workflows:
            print("No workflows found.")
            return

        for workflow in workflows:
            print(f"  {workflow.name}")
            if workflow.description:
                print(f"    {workflow.description}")
            if workflow.version:
                print(f"    Version: {workflow.version}")
            print()

        print(f"Total: {len(workflows)} workflow(s)")
        print("\nUse 'synapse workflow <name>' to apply.")

    def status(self, target_dir: Optional[Path] = None) -> None:
        """Show workflow status."""
        if target_dir is None:
            target_dir = Path.cwd()

        status = self.workflow_service.get_workflow_status(target_dir)

        if not status['active_workflow'] and not status['manifest']:
            print("No active workflow found.")
            print("\nTo apply a workflow:")
            print("  synapse workflow <name>")
            print("\nTo list workflows:")
            print("  synapse workflow list")
            return

        print("Active Workflow Status")
        print("=" * 60)

        if status['active_workflow']:
            print(f"\nActive Workflow: {status['active_workflow']}")

        if status['applied_workflows']:
            print(f"\nWorkflow History ({len(status['applied_workflows'])}):")
            print("-" * 60)
            for entry in status['applied_workflows']:
                name = entry.get('name', 'unknown')
                applied_at = entry.get('applied_at', 'unknown')
                print(f"  {name} (applied: {applied_at})")

        if status['manifest']:
            manifest = status['manifest']
            print("\n" + "=" * 60)
            print("Detailed Artifacts")
            print("=" * 60)
            print(f"\nWorkflow: {manifest.workflow_name}")
            print(f"Applied: {manifest.applied_at.isoformat()}")
            print(f"Synapse Version: {manifest.synapse_version}")

            if manifest.files_copied:
                print(f"\nFiles Copied: {len(manifest.files_copied)}")

            if manifest.hooks_added:
                print(f"Hooks Added: {len(manifest.hooks_added)}")

        print("\n" + "=" * 60)
        print("\nTo remove workflow:")
        print("  synapse workflow remove")

    def apply(
        self,
        workflow_name: str,
        target_dir: Optional[Path] = None,
        force: bool = False
    ) -> None:
        """Apply a workflow."""
        if target_dir is None:
            target_dir = Path.cwd()

        success = self.workflow_service.apply_workflow(
            workflow_name,
            target_dir,
            force
        )

        if not success:
            sys.exit(1)

    def remove(self, target_dir: Optional[Path] = None) -> None:
        """Remove current workflow."""
        if target_dir is None:
            target_dir = Path.cwd()

        # Validate preconditions
        self.validation_service.validate_removal_preconditions(target_dir)

        # Remove workflow
        success = self.removal_service.remove_workflow(target_dir)

        if not success:
            sys.exit(1)

# Factory function
def get_workflow_command(synapse_version: str) -> WorkflowCommand:
    """Get a workflow command instance."""
    return WorkflowCommand(synapse_version)
```

---

### 5. CLI Setup (`cli.py`)

**Purpose**: Argument parsing and command dispatch

#### `cli.py` (~100 lines)
```python
"""CLI setup and command dispatch."""
import argparse
from pathlib import Path
import sys

from .commands.init import get_init_command
from .commands.workflow import get_workflow_command

# Version from package
from . import __version__

def create_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Synapse - AI-first workflow system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  synapse init                      Initialize synapse
  synapse workflow list             List workflows
  synapse workflow status           Show status
  synapse workflow remove           Remove workflow
  synapse workflow <name>           Apply workflow
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize synapse")
    init_parser.add_argument(
        "directory",
        nargs="?",
        type=Path,
        default=None,
        help="Directory to initialize (default: current)"
    )

    # Workflow command
    workflow_parser = subparsers.add_parser("workflow", help="Manage workflows")
    workflow_parser.add_argument(
        "workflow_name_or_command",
        help="Workflow name or subcommand (list, status, remove)"
    )
    workflow_parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite existing files"
    )

    return parser

def dispatch_command(args: argparse.Namespace) -> None:
    """Dispatch to appropriate command handler."""
    if args.command == "init":
        cmd = get_init_command(__version__)
        cmd.execute(args.directory)

    elif args.command == "workflow":
        cmd = get_workflow_command(__version__)
        workflow_arg = args.workflow_name_or_command

        if workflow_arg == "list":
            cmd.list()
        elif workflow_arg == "status":
            cmd.status()
        elif workflow_arg == "remove":
            cmd.remove()
        else:
            # Apply workflow
            cmd.apply(workflow_arg, force=args.force)

    else:
        parser = create_parser()
        parser.print_help()
        sys.exit(1)

def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    dispatch_command(args)

if __name__ == "__main__":
    main()
```

---

### 6. Package Exports (`__init__.py`)

**Purpose**: Clean public API for the package

#### `__init__.py` (~30 lines)
```python
"""Synapse CLI - AI-first workflow system."""

__version__ = "0.3.0"

# Public API exports
from .cli import main
from .infrastructure.resources import get_resource_manager
from .infrastructure.config_store import get_config_store
from .services.workflow_service import get_workflow_service

__all__ = [
    'main',
    'get_resource_manager',
    'get_config_store',
    'get_workflow_service',
    '__version__'
]
```

---

## Dependency Graph

```
┌─────────────────────────────────────────────────┐
│                  CLI (cli.py)                    │
└─────────────────┬───────────────────────────────┘
                  │
         ┌────────┴────────┐
         │                 │
         ▼                 ▼
┌──────────────┐  ┌──────────────┐
│ Commands     │  │ Commands     │
│ init.py      │  │ workflow.py  │
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
                │
       ┌────────┴──────────────────┐
       │                           │
       ▼                           ▼
┌──────────────┐         ┌──────────────┐
│ Services     │         │ Services     │
│ workflow     │◄────────┤ removal      │
│ validation   │         │ settings     │
└──────┬───────┘         └──────┬───────┘
       │                        │
       └────────┬───────────────┘
                │
    ┌───────────┴─────────────┐
    │                         │
    ▼                         ▼
┌──────────────┐    ┌──────────────┐
│Infrastructure│    │Infrastructure│
│ resources    │    │ config_store │
│ backup_mgr   │    │ manifest     │
│ file_ops     │    └──────┬───────┘
└──────┬───────┘           │
       │                   │
       └────────┬──────────┘
                │
                ▼
       ┌──────────────┐
       │     Core     │
       │   models.py  │
       │   types.py   │
       └──────────────┘

DEPENDENCY RULES:
- Commands depend on Services
- Services depend on Infrastructure
- Infrastructure depends on Core
- Core has NO dependencies
- NO circular dependencies
```

---

## Migration Strategy

### Phase 1: Create Infrastructure (Week 1, Day 1-2)

**Goal**: Set up new modules without breaking existing code

1. **Create new directory structure**
   ```bash
   mkdir -p src/synapse_cli/{core,infrastructure,services,commands}
   touch src/synapse_cli/{core,infrastructure,services,commands}/__init__.py
   ```

2. **Create Core layer** (no dependencies on existing code)
   - `core/types.py`
   - `core/models.py`
   - Write comprehensive unit tests

3. **Create Infrastructure layer**
   - `infrastructure/persistence.py` (base class)
   - `infrastructure/resources.py`
   - `infrastructure/config_store.py`
   - `infrastructure/manifest_store.py`
   - `infrastructure/backup_manager.py`
   - `infrastructure/file_operations.py`
   - Write unit tests for each

**Testing**: Each new module must have tests BEFORE moving logic

### Phase 2: Extract Services (Week 1, Day 3-4)

**Goal**: Move business logic to services

1. **Create service modules**
   - `services/validation_service.py`
   - `services/settings_service.py`
   - `services/workflow_service.py`
   - `services/removal_service.py`

2. **Copy (not move) functions from `__init__.py`**
   - Adapt to use Infrastructure layer
   - Keep originals in `__init__.py` for now
   - Add delegation in `__init__.py`:
     ```python
     def workflow_apply(name: str, force: bool = False) -> None:
         """DEPRECATED: Use WorkflowService.apply_workflow()"""
         from .services.workflow_service import get_workflow_service
         service = get_workflow_service(__version__)
         service.apply_workflow(name, force=force)
     ```

3. **Write comprehensive tests**
   - Test each service independently
   - Test integration between services

**Testing**: Both old and new code paths must work

### Phase 3: Create Commands Layer (Week 1, Day 5)

**Goal**: Extract command handlers

1. **Create command modules**
   - `commands/init.py`
   - `commands/workflow.py`

2. **Create new CLI**
   - `cli.py`

3. **Update `__main__.py`** to use new CLI

4. **Keep old `main()` as fallback**

**Testing**: Run all CLI commands, verify identical behavior

### Phase 4: Switch Over (Week 2, Day 1)

**Goal**: Make new code the default

1. **Update `__init__.py`**
   - Keep only public API exports
   - Remove all function implementations
   - Add deprecation warnings

2. **Update all imports**
   - Change from `from synapse_cli import workflow_apply`
   - To: `from synapse_cli import get_workflow_service`

3. **Run full test suite**

**Testing**: All tests must pass, no regressions

### Phase 5: Cleanup (Week 2, Day 2-3)

**Goal**: Remove dead code, polish

1. **Remove old functions** from `__init__.py`

2. **Remove deprecation warnings**

3. **Update documentation**

4. **Final polish**
   - Type hints everywhere
   - Docstrings complete
   - Examples updated

5. **Performance check**
   - Ensure no performance regression
   - Profile import times

**Testing**: Full regression test suite

---

## Testing Strategy

### Unit Tests

Each module gets comprehensive unit tests:

```python
# tests/unit/infrastructure/test_config_store.py
import pytest
from pathlib import Path
from synapse_cli.infrastructure.config_store import ConfigStore

class TestConfigStore:
    """Test ConfigStore functionality."""

    @pytest.fixture
    def config_store(self):
        return ConfigStore()

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temp directory with .synapse/"""
        synapse_dir = tmp_path / ".synapse"
        synapse_dir.mkdir()
        return tmp_path

    def test_load_nonexistent_returns_none(self, config_store, temp_dir):
        """Test loading non-existent config returns None."""
        result = config_store.load(temp_dir)
        assert result is None

    def test_save_and_load_roundtrip(self, config_store, temp_dir):
        """Test save and load roundtrip."""
        config = {
            'synapse_version': '0.3.0',
            'project': {'name': 'test'}
        }

        assert config_store.save(config, temp_dir)

        loaded = config_store.load(temp_dir)
        assert loaded == config

    def test_update_workflow_tracking(self, config_store, temp_dir):
        """Test workflow tracking update."""
        # Create initial config
        config = {
            'synapse_version': '0.3.0',
            'workflows': {}
        }
        config_store.save(config, temp_dir)

        # Update tracking
        assert config_store.update_workflow_tracking(
            'test-workflow',
            temp_dir
        )

        # Verify
        loaded = config_store.load(temp_dir)
        assert loaded['workflows']['active_workflow'] == 'test-workflow'

    # ... more tests
```

### Integration Tests

Test interactions between modules:

```python
# tests/integration/test_workflow_application.py
import pytest
from pathlib import Path
from synapse_cli.services.workflow_service import get_workflow_service

class TestWorkflowApplication:
    """Test complete workflow application."""

    @pytest.fixture
    def synapse_version(self):
        return "0.3.0"

    @pytest.fixture
    def initialized_project(self, tmp_path, synapse_version):
        """Create initialized project."""
        from synapse_cli.commands.init import get_init_command

        cmd = get_init_command(synapse_version)
        # Create mock init
        # ...
        return tmp_path

    def test_apply_workflow_creates_manifest(
        self,
        initialized_project,
        synapse_version
    ):
        """Test applying workflow creates manifest."""
        service = get_workflow_service(synapse_version)

        # Apply workflow
        success = service.apply_workflow(
            'feature-planning',
            initialized_project
        )

        assert success

        # Verify manifest exists
        from synapse_cli.infrastructure.manifest_store import get_manifest_store
        manifest_store = get_manifest_store(synapse_version)

        manifest = manifest_store.load(initialized_project)
        assert manifest is not None
        assert manifest.workflow_name == 'feature-planning'

    # ... more tests
```

### Test Coverage Goals

- **Unit Tests**: >90% coverage per module
- **Integration Tests**: Cover all major workflows
- **End-to-End Tests**: CLI command execution
- **Regression Tests**: All existing tests must pass

---

## Risk Analysis

### High Risks

1. **Breaking Changes During Migration**
   - **Mitigation**: Parallel code paths, deprecation warnings
   - **Detection**: Comprehensive test suite
   - **Recovery**: Keep old code until fully tested

2. **Import Time Regression**
   - **Mitigation**: Lazy imports, singleton patterns
   - **Detection**: Performance benchmarks
   - **Recovery**: Optimize critical paths

3. **Circular Dependencies**
   - **Mitigation**: Strict layer enforcement, dependency graph
   - **Detection**: Import analysis tools
   - **Recovery**: Use dependency injection

### Medium Risks

4. **Incomplete Test Coverage**
   - **Mitigation**: Write tests before refactoring
   - **Detection**: Coverage reports
   - **Recovery**: Manual testing of gaps

5. **Module Interface Changes**
   - **Mitigation**: Semantic versioning, changelog
   - **Detection**: API compatibility checks
   - **Recovery**: Maintain compatibility layer

### Low Risks

6. **Developer Confusion**
   - **Mitigation**: Clear documentation, examples
   - **Detection**: Code review feedback
   - **Recovery**: Additional documentation

---

## Implementation Roadmap

### Week 1: Core Refactoring

| Day | Tasks | Deliverables | Tests |
|-----|-------|--------------|-------|
| 1 | Core layer | types.py, models.py | Unit tests |
| 2 | Infrastructure base | persistence.py, resources.py | Unit tests |
| 3 | Infrastructure stores | config_store.py, manifest_store.py | Unit tests |
| 4 | Infrastructure ops | backup_manager.py, file_operations.py | Unit tests |
| 5 | Services layer | validation, settings, workflow | Unit + integration |

### Week 2: Integration & Cleanup

| Day | Tasks | Deliverables | Tests |
|-----|-------|--------------|-------|
| 1 | Commands layer | init.py, workflow.py, cli.py | Integration tests |
| 2 | Switch over | Update __init__.py, deprecate old | Regression tests |
| 3 | Cleanup | Remove dead code, documentation | All tests pass |
| 4-5 | Buffer | Handle unexpected issues | Final validation |

---

## Code Examples

### Before: Monolithic Function

```python
# Current: __init__.py (lines 1578-1717)
def workflow_apply(name: str, force: bool = False) -> None:
    """Apply a workflow to the current project."""
    target_dir = Path.cwd()

    # Validate all preconditions (fail-fast)
    validate_workflow_preconditions(name, target_dir)

    # Get workflow info for display
    info = get_workflow_info(name)
    print(f"Applying workflow: {name}")
    # ... 140 more lines ...
```

### After: Modular Approach

```python
# New: commands/workflow.py
class WorkflowCommand:
    def apply(self, workflow_name: str, force: bool = False):
        """Apply a workflow."""
        success = self.workflow_service.apply_workflow(
            workflow_name,
            force=force
        )
        if not success:
            sys.exit(1)

# New: services/workflow_service.py
class WorkflowService:
    def apply_workflow(self, workflow_name: str, force: bool = False):
        """Apply workflow with full orchestration."""
        # Validate
        self.validation_service.validate_workflow_preconditions(
            workflow_name
        )

        # Get info
        info = self.resource_manager.get_workflow_info(workflow_name)

        # Create backup
        backup = self.backup_manager.create_backup()

        # Copy files
        results = self._apply_workflow_directories(...)

        # Merge settings
        merge_result = self.settings_service.merge_settings_json(...)

        # Create manifest
        manifest = self.manifest_store.create_manifest(...)

        # Update config
        self.config_store.update_workflow_tracking(...)

        return True
```

### Benefits of Modular Approach

1. **Testability**: Each component tested independently
2. **Reusability**: Services can be used by other commands
3. **Maintainability**: Changes localized to specific modules
4. **Clarity**: Clear separation of concerns
5. **Extensibility**: Easy to add new workflows or commands

---

## Conclusion

### Summary

This refactoring transforms a monolithic 1,823-line file into a clean, layered architecture with:

- **8 focused modules** organized by responsibility
- **~200-300 lines per module** (manageable size)
- **Clear dependency direction** (no circular deps)
- **Comprehensive testing** at each layer
- **Backward compatibility** during migration
- **Improved maintainability** for future development

### Next Steps

1. **Review this proposal** with team
2. **Approve architecture** and module boundaries
3. **Create implementation branch**
4. **Follow migration strategy** (phases 1-5)
5. **Continuous testing** throughout
6. **Documentation updates** as we go

### Success Criteria

- ✅ All existing tests pass
- ✅ No performance regression
- ✅ >90% test coverage maintained
- ✅ Clear module boundaries
- ✅ Zero circular dependencies
- ✅ Documentation complete
- ✅ Team can navigate codebase easily

---

**Estimated Effort**: 2-3 weeks (with buffer)  
**Risk Level**: Medium (mitigated by thorough testing)  
**Impact**: High (significantly improved codebase quality)
