# Developer Guide

This guide helps developers understand and contribute to the Synapse CLI codebase.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Development Setup](#development-setup)
- [Code Organization](#code-organization)
- [Adding New Features](#adding-new-features)
- [Testing Guidelines](#testing-guidelines)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

## Architecture Overview

Synapse follows a **layered architecture** with clear separation of concerns. Each layer has specific responsibilities and dependencies flow in one direction (downward).

### Dependency Flow

```
CLI (cli.py)
    ↓
Commands (commands/)
    ↓
Services (services/)
    ↓
Infrastructure (infrastructure/) ← Core (core/)
    ↓
Parsers (parsers/)
```

**Key Principle**: Higher layers depend on lower layers, never the reverse. Core models are shared across all layers.

### Layer Responsibilities

**CLI Layer** (`cli.py`)
- Single entry point using Click framework
- Defines command structure and options
- Minimal logic - delegates to Commands layer
- Example: `@click.command()` decorators

**Commands Layer** (`commands/`)
- Thin orchestration layer
- Coordinates multiple services
- Handles user interaction (prompts, output)
- No business logic - just coordination
- Example: `WorkflowCommand.status()` calls `WorkflowService.get_workflow_status()`

**Services Layer** (`services/`)
- Contains all business logic
- Orchestrates infrastructure components
- Implements workflows and operations
- Returns data structures, not formatted output
- Example: `WorkflowService.apply_workflow()` orchestrates validation, backup, file copying, manifest creation

**Infrastructure Layer** (`infrastructure/`)
- Low-level operations (file I/O, persistence)
- No business logic
- Single responsibility per module
- Highly testable and mockable
- Example: `ConfigStore.read()` reads and validates config files

**Core Layer** (`core/`)
- Shared data models and types
- No dependencies on other layers
- Frozen dataclasses for immutability
- Type definitions and constants
- Example: `WorkflowManifest`, `ConfigFile`

**Parsers Layer** (`parsers/`)
- Schema parsing and validation
- Task format detection
- Independent of other layers
- Example: `TaskSchemaParser.detect_workflow_type()`

## Development Setup

### Prerequisites

- Python 3.9+
- pip or uv package manager

### Installation

```bash
# Clone repository
git clone <repo-url>
cd synapse

# Install in development mode
pip install -e .

# Or with uv
uv pip install -e .

# Install test dependencies
pip install -e ".[dev]"
```

### Verify Installation

```bash
# Run CLI
synapse --help

# Run tests
pytest

# Run with coverage
pytest --cov=src/synapse_cli --cov-report=html
```

## Code Organization

### Directory Structure

```
src/synapse_cli/
├── cli.py                      # Click CLI entry point
├── __main__.py                 # Python module entry
├── commands/                   # Command handlers
│   ├── __init__.py
│   ├── init.py                # Init command
│   └── workflow.py            # Workflow commands
├── services/                   # Business logic
│   ├── __init__.py
│   ├── workflow_service.py    # Core workflow logic
│   ├── settings_service.py    # Settings management
│   ├── validation_service.py  # Validation
│   └── removal_service.py     # Cleanup
├── infrastructure/             # Low-level operations
│   ├── __init__.py
│   ├── config_store.py        # Config persistence
│   ├── manifest_store.py      # Manifest tracking
│   ├── backup_manager.py      # Backup/restore
│   ├── file_operations.py     # File copying
│   ├── resources.py           # Resource loading
│   └── persistence.py         # Generic I/O
├── core/                       # Domain models
│   ├── __init__.py
│   ├── models.py              # Data classes
│   └── types.py               # Type definitions
└── parsers/                    # Schema parsing
    ├── __init__.py
    ├── task_schema_parser.py
    ├── schema_generator.py
    └── schema_validator.py
```

### Key Files

**cli.py** - Main CLI entry point
- Defines all commands using Click decorators
- Routes to appropriate command handlers
- Minimal logic

**commands/workflow.py** - Workflow command handlers
- `list()` - Lists available workflows
- `status()` - Shows current workflow status
- `apply()` - Applies a workflow
- `remove()` - Removes current workflow

**services/workflow_service.py** - Core workflow logic
- `apply_workflow()` - Orchestrates workflow application
- `remove_workflow()` - Orchestrates workflow removal
- `get_workflow_status()` - Returns workflow state

**infrastructure/config_store.py** - Config file management
- `read()` - Reads and validates config
- `write()` - Writes config with validation
- `update_active_workflow()` - Updates workflow tracking

**core/models.py** - Data structures
- `WorkflowManifest` - Tracks applied workflow artifacts
- `ConfigFile` - Project configuration structure
- `WorkflowMetadata` - Workflow information

## Adding New Features

### Example: Adding a New Command

Let's add a `synapse config show` command to display configuration.

#### Step 1: Define CLI Command (cli.py)

```python
@cli.group()
def config():
    """Configuration management commands."""
    pass

@config.command("show")
def config_show():
    """Show current configuration."""
    from synapse_cli.commands.config import ConfigCommand

    config_cmd = ConfigCommand()
    config_cmd.show()
```

#### Step 2: Create Command Handler (commands/config.py)

```python
from synapse_cli.infrastructure.config_store import ConfigStore

class ConfigCommand:
    def __init__(self):
        self.config_store = ConfigStore()

    def show(self, target_dir: Path = Path.cwd()):
        """Display configuration."""
        try:
            config = self.config_store.read(target_dir)
            # Format and display config
            print(f"Synapse Version: {config.synapse_version}")
            print(f"Active Workflow: {config.workflows.get('active_workflow')}")
        except FileNotFoundError:
            print("No .synapse directory found. Run 'synapse init' first.")
```

#### Step 3: Add Tests

**Unit Test** (tests/unit/commands/test_config.py):
```python
import pytest
from unittest.mock import Mock
from synapse_cli.commands.config import ConfigCommand

def test_show_displays_config(mock_config_store):
    cmd = ConfigCommand()
    cmd.config_store = mock_config_store

    mock_config_store.read.return_value = Mock(
        synapse_version="0.1.0",
        workflows={'active_workflow': 'feature-planning'}
    )

    cmd.show()

    mock_config_store.read.assert_called_once()
```

**E2E Test** (tests/e2e/test_config_commands.py):
```python
import subprocess
import sys

def test_config_show_command(tmp_path):
    """Test config show displays configuration."""
    # Initialize project
    subprocess.run([sys.executable, "-m", "synapse_cli", "init"],
                   cwd=tmp_path, check=True)

    # Run config show
    result = subprocess.run(
        [sys.executable, "-m", "synapse_cli", "config", "show"],
        cwd=tmp_path,
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "Synapse Version" in result.stdout
```

### Example: Adding a New Service

Let's add a service to export workflow history.

#### Step 1: Define Service Interface (services/export_service.py)

```python
from pathlib import Path
from typing import Dict, Any
from synapse_cli.infrastructure.config_store import ConfigStore
from synapse_cli.infrastructure.manifest_store import ManifestStore

class ExportService:
    """Service for exporting workflow data."""

    def __init__(self):
        self.config_store = ConfigStore()
        self.manifest_store = ManifestStore()

    def export_history(self, target_dir: Path) -> Dict[str, Any]:
        """Export workflow history to dictionary."""
        config = self.config_store.read(target_dir)
        manifest = self.manifest_store.read(target_dir)

        return {
            'active_workflow': config.workflows.get('active_workflow'),
            'applied_workflows': config.workflows.get('applied_workflows', []),
            'manifest': manifest.to_dict() if manifest else None
        }
```

#### Step 2: Add Unit Tests

```python
import pytest
from unittest.mock import Mock
from synapse_cli.services.export_service import ExportService

def test_export_history(mock_config_store, mock_manifest_store):
    service = ExportService()
    service.config_store = mock_config_store
    service.manifest_store = mock_manifest_store

    mock_config_store.read.return_value = Mock(
        workflows={'active_workflow': 'test-workflow'}
    )
    mock_manifest_store.read.return_value = Mock(
        to_dict=lambda: {'workflow_name': 'test-workflow'}
    )

    result = service.export_history(Path.cwd())

    assert result['active_workflow'] == 'test-workflow'
    assert result['manifest']['workflow_name'] == 'test-workflow'
```

## Testing Guidelines

### Test Levels

Synapse uses a three-level testing strategy:

#### 1. Unit Tests (`tests/unit/`)

**Purpose**: Test individual components in isolation

**Characteristics**:
- Mock all external dependencies
- Fast execution (< 1 second total)
- Test single units of logic
- High coverage of edge cases

**Example**:
```python
def test_workflow_service_apply_creates_manifest(mock_file_ops, mock_config_store):
    service = WorkflowService()
    service.file_operations = mock_file_ops
    service.config_store = mock_config_store

    service.apply_workflow("test-workflow", Path.cwd())

    mock_file_ops.copy_files.assert_called_once()
    mock_config_store.update_active_workflow.assert_called_once()
```

#### 2. Integration Tests (`tests/integration/`)

**Purpose**: Test complete workflows with real services

**Characteristics**:
- Use real services (no mocks for service layer)
- Use temporary directories for file operations
- Test interactions between components
- Verify end-to-end workflows

**Example**:
```python
def test_apply_workflow_creates_manifest(test_project_dir):
    """Test that applying a workflow creates a manifest file."""
    service = WorkflowService()

    # Apply workflow
    service.apply_workflow("feature-planning", test_project_dir)

    # Verify manifest exists
    manifest_path = test_project_dir / ".synapse" / "workflow-manifest.json"
    assert manifest_path.exists()

    # Verify manifest contents
    manifest_store = ManifestStore()
    manifest = manifest_store.read(test_project_dir)
    assert manifest.workflow_name == "feature-planning"
```

#### 3. E2E Tests (`tests/e2e/`)

**Purpose**: Test CLI commands as users would invoke them

**Characteristics**:
- Use subprocess to invoke CLI
- Test actual user interaction
- Verify CLI output and exit codes
- Test error handling and edge cases

**Example**:
```python
def test_workflow_apply_success(tmp_path):
    """Test successful workflow application via CLI."""
    # Initialize project
    subprocess.run([sys.executable, "-m", "synapse_cli", "init"],
                   cwd=tmp_path, check=True)

    # Apply workflow
    result = subprocess.run(
        [sys.executable, "-m", "synapse_cli", "workflow", "feature-planning"],
        cwd=tmp_path,
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "Applied workflow: feature-planning" in result.stdout
```

### Testing Best Practices

1. **Write tests first** - TDD helps design better APIs
2. **Test at all levels** - Unit + Integration + E2E
3. **Mock external dependencies** - File system, network, etc. in unit tests
4. **Use fixtures** - Share test setup code via pytest fixtures
5. **Test error paths** - Don't just test happy paths
6. **Keep tests independent** - Each test should be runnable in isolation
7. **Use descriptive names** - Test names should explain what they verify

### Running Tests

```bash
# Run all tests
pytest

# Run specific level
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run specific file
pytest tests/unit/commands/test_workflow.py

# Run specific test
pytest tests/unit/commands/test_workflow.py::TestWorkflowCommand::test_list_workflows

# Run with coverage
pytest --cov=src/synapse_cli --cov-report=html

# Run with verbose output
pytest -v

# Run with debugging
pytest -vv --pdb
```

## Common Patterns

### Pattern 1: Service Initialization

Services typically initialize their dependencies in `__init__`:

```python
class WorkflowService:
    def __init__(self):
        self.config_store = ConfigStore()
        self.manifest_store = ManifestStore()
        self.file_operations = FileOperations()
        self.backup_manager = BackupManager()
```

For testing, dependencies can be replaced:

```python
def test_workflow_service():
    service = WorkflowService()
    service.config_store = Mock()  # Replace with mock
```

### Pattern 2: Error Handling

Use try/except at the command level, return data from services:

```python
# Command layer (handles errors, displays messages)
def apply_workflow(self, workflow_name: str):
    try:
        result = self.workflow_service.apply_workflow(workflow_name)
        print(f"Applied workflow: {workflow_name}")
    except ValueError as e:
        print(f"Error: {e}")
    except FileNotFoundError:
        print("Project not initialized. Run 'synapse init' first.")

# Service layer (raises exceptions, returns data)
def apply_workflow(self, workflow_name: str) -> bool:
    if not self._validate_workflow(workflow_name):
        raise ValueError(f"Invalid workflow: {workflow_name}")

    # Business logic here
    return True
```

### Pattern 3: Path Handling

Always use `Path` objects, not strings:

```python
from pathlib import Path

def read_config(self, target_dir: Path = Path.cwd()) -> ConfigFile:
    config_path = target_dir / ".synapse" / "config.json"
    # Use Path methods
```

### Pattern 4: Type Hints

Always provide type hints:

```python
from typing import Dict, List, Optional
from pathlib import Path

def get_workflow_status(
    self,
    target_dir: Path = Path.cwd()
) -> Dict[str, Any]:
    """Get current workflow status.

    Args:
        target_dir: Directory to check for workflow

    Returns:
        Dictionary with workflow status information
    """
    pass
```

### Pattern 5: Dataclass Models

Use frozen dataclasses for immutability:

```python
from dataclasses import dataclass, field
from typing import List

@dataclass(frozen=True)
class WorkflowManifest:
    """Manifest tracking applied workflow artifacts."""
    workflow_name: str
    applied_at: str
    synapse_version: str
    files_copied: List[str] = field(default_factory=list)
    hooks_added: List[str] = field(default_factory=list)
```

### Pattern 6: Resource Loading

Use `ResourceLoader` for accessing workflow files:

```python
from synapse_cli.infrastructure.resources import ResourceLoader

resource_loader = ResourceLoader()
workflow_dir = resource_loader.get_workflow_directory("feature-planning")
hooks_dir = workflow_dir / "hooks"
```

## Troubleshooting

### Common Issues

#### Issue: "Module not found" errors

**Cause**: Package not installed in development mode

**Solution**:
```bash
pip install -e .
```

#### Issue: Tests pass individually but fail when run together

**Cause**: Tests sharing state or side effects

**Solution**: Ensure tests are independent. Use fixtures and tmp_path:
```python
def test_example(tmp_path):
    # Use tmp_path for file operations
    config_path = tmp_path / ".synapse" / "config.json"
```

#### Issue: Type checking errors with mypy

**Cause**: Missing type hints or incorrect types

**Solution**: Add type hints to all functions:
```bash
# Run mypy
mypy src/synapse_cli
```

#### Issue: Coverage not reaching target

**Cause**: Untested code paths

**Solution**: Run coverage to identify gaps:
```bash
pytest --cov=src/synapse_cli --cov-report=html
# Open htmlcov/index.html to see gaps
```

### Debugging Tips

1. **Use pytest's `-vv` flag** for detailed output
2. **Use `--pdb` flag** to drop into debugger on failures
3. **Add print statements** in tests (they're captured by pytest)
4. **Use `capsys` fixture** to test printed output
5. **Mock carefully** - ensure mocks match real behavior

### Getting Help

- Check existing tests for examples
- Review architecture documentation in README.md
- Look at similar features for patterns
- Ask questions in issues or pull requests

## Contributing Workflow

1. **Fork and clone** the repository
2. **Create a feature branch**: `git checkout -b feature/my-feature`
3. **Make changes** following the architectural guidelines
4. **Write tests** at all three levels
5. **Run tests**: `pytest`
6. **Run linting**: `ruff check src/`
7. **Commit changes**: Follow conventional commits format
8. **Push and create PR**: Describe changes clearly

### Commit Message Format

Use conventional commits:

```
feat: add config show command
fix: correct manifest path in workflow removal
docs: update architecture documentation
test: add integration tests for workflow switching
refactor: extract backup logic to separate service
```

## Additional Resources

- [README.md](README.md) - User documentation
- [Architecture Decision Records](docs/adr/) - Design decisions
- [API Documentation](docs/api/) - Generated API docs

---

**Questions?** Open an issue or reach out to the maintainers.
