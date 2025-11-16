# Synapse

AI-first workflow system with quality gates and workflow automation for Claude Code.

## What is Synapse?

Synapse provides standardized workflows, quality gates, and automation for Claude Code projects. It includes automated quality enforcement hooks, schema-driven task parsing, and reusable workflow commands.

**Tech Stack:** Python 3.9+, Claude Code integration

**Capabilities:**
- Simplified QA verification with user-controlled fix timing
- Automated quality gate enforcement
- Schema-driven task format detection
- Multi-layer protection against bypassing quality checks
- Stop with failures - fix issues on your schedule

## Installation

**From source (current setup):**
```bash
cd /Users/aabrams/Workspace/AI/synapse
pip install -e .
```

**From PyPI (when published):**
```bash
pip install synapse
# or
uv tool install synapse
```

## Usage

**Initialize in your project:**
```bash
synapse init
```

This creates a `.synapse/` directory with:
- `config.json` - project configuration and workflow tracking

**Initialize in specific directory:**
```bash
synapse init /path/to/project
```

## Workflows

Synapse includes pre-built workflows that apply standardized configurations to your Claude Code project:

**List available workflows:**
```bash
synapse workflow list
```

**Apply a workflow:**
```bash
synapse workflow feature-implementation  # QA verification with quality gates
synapse workflow feature-planning           # Task breakdown and planning
```

**Check workflow status:**
```bash
synapse workflow status
```

**Remove current workflow:**
```bash
synapse workflow remove
```

Workflows automatically configure:
- Quality gate hooks for automated verification
- Project-specific commands (like `/sense` for quality configuration)
- Settings optimized for your development workflow
- Multi-layer protection system (UserPromptSubmit, PreToolUse, PostToolUse, Stop hooks)

## Quality Configuration & Third-Party Integration

After applying a workflow, use the `/sense` command in Claude Code to analyze your project and configure quality standards:

```bash
/sense
```

The sense command provides comprehensive project analysis including:
- **Quality Configuration**: Detects linting, testing, and coverage tools and adds thresholds to `.synapse/config.json`
- **Third-Party Workflow Detection**: Automatically discovers and catalogs task management systems like:
  - **OpenSpec** (`openspec/changes/*/tasks.md`)
  - **GitHub Spec Kit** (`specs/###-feature/tasks.md`)
  - **Custom Workflows** (any `tasks.md` files across your project)

### Third-Party Workflow Integration

Synapse intelligently detects existing workflow frameworks in your project:

1. **Known Patterns**: Instantly recognizes OpenSpec and Spec Kit structures
2. **Generic Discovery**: Finds any `tasks.md` files throughout your project
3. **Smart Analysis**: Uses AI to understand unknown directory patterns
4. **Interactive Fallback**: Asks for clarification when patterns are ambiguous

Detected workflows are stored in `.synapse/config.json` under `third_party_workflow` with:
- Workflow type
- Active tasks file path
- Task format schema for parsing
- Active tasks array for tracking work in progress

This allows Synapse to work seamlessly alongside other workflow management systems while maintaining its own quality gates and verification workflows.

## Architecture

Synapse follows a clean layered architecture with clear separation of concerns:

### Modular Architecture

**CLI Layer** (`cli.py`)
- Entry point using Click for command parsing
- Routes commands to appropriate handlers
- Handles global options and error presentation

**Commands Layer** (`commands/`)
- `init.py` - Project initialization command handler
- `workflow.py` - Workflow management command handlers (list, status, apply, remove)
- Thin layer that coordinates services and presents results

**Services Layer** (`services/`)
- `workflow_service.py` - Core workflow application, removal, and status logic
- `settings_service.py` - Settings merging and management
- `validation_service.py` - Workflow validation and verification
- `removal_service.py` - Cleanup and rollback operations
- Contains business logic, orchestrates infrastructure components

**Infrastructure Layer** (`infrastructure/`)
- `config_store.py` - Config file reading/writing with schema validation
- `manifest_store.py` - Manifest tracking for applied workflows
- `backup_manager.py` - Backup creation and restoration
- `file_operations.py` - Safe file copying with validation
- `resources.py` - Workflow resource discovery and loading
- `persistence.py` - Generic file I/O operations
- Low-level operations, no business logic

**Core Layer** (`core/`)
- `models.py` - Data models (WorkflowManifest, ConfigFile, etc.)
- `types.py` - Type definitions and constants
- Shared domain models used across all layers

**Parsers Layer** (`parsers/`)
- `task_schema_parser.py` - Third-party task format detection
- `schema_generator.py` - Schema generation from task files
- `schema_validator.py` - Schema validation logic

### Workflow System

Synapse uses a simplified two-stage verification approach:
- **Hooks**: Simple checkers (~400 lines) that enforce workflow rules
- **Agent**: Performs actual verification with full tool access

Synapse applies workflow-specific configurations through:
- **File Copying**: Hooks and commands from `resources/workflows/<name>/` to `.claude/`
- **Settings Merging**: Combines workflow settings.json with existing `.claude/settings.json`
- **Tracking**: Maintains workflow manifest in `.synapse/workflow-manifest.json` for precise removal
- **Backup/Restore**: Creates backups before applying workflows for safe rollback

### Testing Strategy

Synapse includes comprehensive test coverage across three levels:

**Unit Tests** (`tests/unit/`)
- Test individual components in isolation
- Mock external dependencies
- Fast execution, focused on single units of logic
- Coverage: Commands, services, infrastructure, parsers

**Integration Tests** (`tests/integration/`)
- Test complete workflows using real services
- Use temporary directories for file operations
- Verify interactions between multiple components
- Coverage: Workflow application, removal, switching

**E2E Tests** (`tests/e2e/`)
- Test CLI commands via subprocess invocation
- Simulate actual user interaction
- Verify end-to-end behavior from CLI to file system
- Coverage: All CLI commands, error handling, interactive prompts

### Configuration Schema
The `.synapse/config.json` file stores project configuration with these key sections:

```json
{
  "synapse_version": "0.1.0",
  "project": { "name": "project-name", "root_directory": "/path" },
  "workflows": {
    "active_workflow": "feature-implementation",
    "applied_workflows": [...]
  },
  "quality-config": {
    "projectType": "python|node|rust|...",
    "commands": { "test": "pytest", "lint": "flake8", ... },
    "thresholds": { "coverage": { "lines": 80 }, ... }
  },
  "third_party_workflow": {
    "type": "openspec|spec-kit|custom",
    "active_tasks_file": "tasks.md",
    "active_tasks": ["T001", "T002"],
    "task_format_schema": {
      "version": "2.0",
      "patterns": {...},
      "field_mapping": {...},
      "status_semantics": {...}
    }
  }
}
```

### Project Structure

**User Project Structure** (created by Synapse):
```
.synapse/                 # Synapse configuration
├── config.json         # Project settings and workflow tracking
├── workflow-manifest.json  # Applied workflow artifacts
└── commands/synapse/sense.md  # Quality analysis command

.claude/                 # Claude Code integration (created by workflows)
├── hooks/              # Quality gate scripts (stop, pre-tool-use, post-tool-use, etc.)
├── commands/           # Additional slash commands
└── settings.json       # Claude Code hook configuration
```

**Synapse Codebase Structure**:
```
src/synapse_cli/
├── cli.py                      # CLI entry point
├── __main__.py                 # Python module entry
├── commands/                   # Command handlers
│   ├── init.py                # Init command
│   └── workflow.py            # Workflow commands
├── services/                   # Business logic layer
│   ├── workflow_service.py    # Workflow operations
│   ├── settings_service.py    # Settings management
│   ├── validation_service.py  # Validation logic
│   └── removal_service.py     # Cleanup operations
├── infrastructure/             # Low-level operations
│   ├── config_store.py        # Config persistence
│   ├── manifest_store.py      # Manifest tracking
│   ├── backup_manager.py      # Backup/restore
│   ├── file_operations.py     # File copying
│   ├── resources.py           # Resource loading
│   └── persistence.py         # Generic I/O
├── core/                       # Domain models
│   ├── models.py              # Data classes
│   └── types.py               # Type definitions
└── parsers/                    # Schema parsing
    ├── task_schema_parser.py  # Task detection
    ├── schema_generator.py    # Schema generation
    └── schema_validator.py    # Validation

resources/workflows/            # Workflow templates
├── feature-implementation/  # QA workflow
│   ├── hooks/                 # Stop, PreToolUse, PostToolUse
│   ├── commands/              # Slash commands
│   └── settings.json          # Hook configuration
└── feature-planning/          # Planning workflow
    ├── hooks/
    ├── commands/
    └── settings.json

tests/
├── unit/                      # Unit tests (mocked dependencies)
├── integration/               # Integration tests (real services)
└── e2e/                       # End-to-end CLI tests
```

That's it. Claude Code automatically detects and uses the `.synapse/` directory for enhanced AI-assisted development with quality enforcement and third-party workflow awareness.

## Development

### Running Tests

Synapse includes 42 comprehensive tests across three levels:

```bash
# Run all tests
pytest

# Run specific test levels
pytest tests/unit/           # Unit tests (16 tests)
pytest tests/integration/    # Integration tests (11 tests)
pytest tests/e2e/           # E2E tests (15 tests)

# Run with coverage
pytest --cov=src/synapse_cli --cov-report=html

# Run specific test file
pytest tests/unit/commands/test_workflow.py -v
```

### Architectural Principles

The codebase follows these design principles:

1. **Layered Architecture**: Clear separation between CLI, Commands, Services, and Infrastructure
2. **Dependency Direction**: Dependencies flow downward (CLI → Commands → Services → Infrastructure → Core)
3. **Single Responsibility**: Each module has one clear purpose
4. **Testability**: Services and infrastructure are easily mockable for unit tests
5. **Type Safety**: Full type hints throughout the codebase
6. **Immutability**: Data models use frozen dataclasses where appropriate

### Contributing Guidelines

When adding new features:

1. **Follow the layers**: Put code in the appropriate layer
   - Business logic → Services
   - File operations → Infrastructure
   - Command handling → Commands
   - Data structures → Core

2. **Write tests at all levels**:
   - Unit tests for isolated logic
   - Integration tests for workflows
   - E2E tests for user-facing commands

3. **Maintain type safety**: Add type hints to all functions

4. **Update documentation**: Keep README and docstrings current

