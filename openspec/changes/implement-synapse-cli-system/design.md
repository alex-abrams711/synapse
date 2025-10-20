# Design Document: Synapse CLI System

**Change ID**: `implement-synapse-cli-system`
**Last Updated**: 2025-10-20

---

## Architecture Overview

Synapse is a single-module Python CLI tool that applies workflow patterns to Claude Code through file operations and configuration management.

### System Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Synapse CLI                           │
│                                                          │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────────┐│
│  │   Main     │  │   File Ops   │  │    Settings     ││
│  │  Command   │→│   Manager    │→│     Manager     ││
│  │   Parser   │  │              │  │                 ││
│  └────────────┘  └──────────────┘  └─────────────────┘│
│         ↓                ↓                  ↓           │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────────┐│
│  │   State    │  │    Backup    │  │    Resource     ││
│  │  Tracker   │  │   Manager    │  │    Loader       ││
│  └────────────┘  └──────────────┘  └─────────────────┘│
└─────────────────────────────────────────────────────────┘
                        ↓ writes to
         ┌──────────────────────────────────────┐
         │        .claude/ directory             │
         │  ┌──────────┬──────────┬──────────┐ │
         │  │ agents/  │  hooks/  │commands/ │ │
         │  └──────────┴──────────┴──────────┘ │
         │        settings.json                 │
         └──────────────────────────────────────┘
                        ↑
                  read by Claude Code
```

## Key Design Decisions

### 1. Single Module Structure

**Decision**: Implement entire CLI in `src/synapse_cli/__init__.py` with minimal `__main__.py` entry point.

**Rationale**:
- Reduces complexity for a focused tool
- All logic easily discoverable in one place
- Simplifies testing and maintenance
- Avoids over-engineering for current scope

**Trade-offs**:
- File may grow large (acceptable for ~1000-1500 lines)
- Less modular (acceptable given focused scope)

**Alternatives Considered**:
- Multi-file module structure (rejected: premature optimization)
- Separate subpackages (rejected: unnecessary complexity)

### 2. Resource Distribution via setuptools

**Decision**: Package workflows in `resources/` directory using setuptools `package_data`.

**Rationale**:
- Standard Python packaging approach
- Works with pip, pipx, and editable installs
- Resources bundled in distribution files (wheel/sdist)
- Cross-platform compatible

**Implementation**:
```python
# In __init__.py
import pkg_resources

def get_resources_dir():
    return pkg_resources.resource_filename('synapse_cli', 'resources')
```

**Trade-offs**:
- Requires `MANIFEST.in` configuration
- Resources read-only after installation (acceptable: workflows shouldn't be modified)

### 3. JSON-Based Configuration

**Decision**: Use plain JSON for all configuration files (no YAML, TOML, or custom formats).

**Rationale**:
- Python stdlib support (no dependencies)
- Human-readable and editable
- Claude Code uses JSON for settings
- Simple validation with `json.load()`

**Schema Examples**:
```json
// .synapse/config.json
{
  "synapse_version": "0.1.0",
  "project": { "name": "...", "root_directory": "..." },
  "workflows": {
    "active_workflow": "feature-planning",
    "applied_workflows": [...]
  }
}

// .synapse/workflow-manifest.json
{
  "workflow_name": "feature-planning",
  "files_copied": [...],
  "hooks_added": [...],
  "settings_updated": [...]
}
```

### 4. Backup Strategy

**Decision**: Create timestamped backups of entire `.claude/` directory before any modification.

**Rationale**:
- Simple and reliable
- Complete rollback capability
- No complex diff tracking needed
- Disk space trade-off acceptable for safety

**Structure**:
```
.synapse/backups/
  └── 20251020_143022/
      └── claude/
          ├── agents/
          ├── hooks/
          ├── commands/
          └── settings.json
```

**Trade-offs**:
- More disk space (mitigated: backups are small text files)
- Slower than incremental backups (acceptable: operations are rare)

### 5. Settings Merge Algorithm

**Decision**: Deep merge workflow settings into existing `.claude/settings.json` with array appending for hooks.

**Algorithm**:
```python
def deep_merge(base, overlay):
    """Merge overlay into base, appending arrays instead of replacing."""
    result = base.copy()
    for key, value in overlay.items():
        if key in result:
            if isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            elif isinstance(result[key], list) and isinstance(value, list):
                # Append to arrays (for hooks)
                result[key] = result[key] + value
            else:
                result[key] = value
        else:
            result[key] = value
    return result
```

**Rationale**:
- Preserves existing settings
- Allows multiple workflows to coexist
- Hooks array grows without replacing existing hooks
- Predictable behavior

**Trade-offs**:
- No duplicate detection (acceptable: manifest tracks what we added)
- No conflict resolution (acceptable: --force handles overwrites)

### 6. Hook Execution Model

**Decision**: Python hooks execute via `uv run`, shell hooks execute directly.

**Rationale**:
- uv provides isolated environments for Python hooks
- No need to manage virtual environments manually
- PEP 723 inline dependencies keep hooks self-contained
- Shell hooks remain simple for basic operations

**Example Hook Configuration**:
```json
{
  "hooks": {
    "userPromptSubmit": [
      {
        "command": ".claude/hooks/user-prompt-submit-reminder.sh"
      }
    ],
    "preToolUse": [
      {
        "command": "uv run .claude/hooks/task_implementer_pretool_gate.py"
      }
    ]
  }
}
```

### 7. State Tracking Approach

**Decision**: Maintain two files for state:
1. `.synapse/config.json` - Project configuration and active workflow
2. `.synapse/workflow-manifest.json` - Detailed tracking of applied changes

**Rationale**:
- Separation of concerns: config vs. operational state
- Manifest enables precise rollback
- Config provides user-facing project information
- Both are simple, readable JSON

**Manifest Tracks**:
- Every file copied (path + type)
- Every hook added (hook type + command)
- Every settings section modified
- Timestamp and CLI version

### 8. Workflow File Organization

**Decision**: Workflows store files in subdirectories matching Claude Code structure.

**Structure**:
```
resources/workflows/feature-planning/
  ├── agents/
  │   └── task-writer.md
  ├── hooks/
  │   └── user-prompt-submit-reminder.sh
  ├── commands/synapse/
  │   └── sense.md
  └── settings.json

resources/workflows/feature-implementation/
  ├── agents/
  │   ├── implementer.md
  │   └── verifier.md
  ├── hooks/
  │   ├── user-prompt-submit-reminder.sh
  │   ├── task_implementer_pretool_gate.py
  │   ├── task_implementer_quality_gate.py
  │   └── task_verifier_completion.py
  ├── commands/synapse/
  │   └── sense.md
  └── settings.json
```

**Rationale**:
- Direct mapping to `.claude/` structure
- Easy to understand and maintain
- Simple copy operations
- Self-documenting organization

## Component Design

### CLI Command Structure

```
synapse
├── init [directory]           # Initialize .synapse/ in project
├── workflow
│   ├── list                   # Show available workflows
│   ├── status                 # Show active workflow and files
│   ├── remove                 # Remove active workflow
│   ├── feature-planning [--force]      # Apply planning workflow
│   └── feature-implementation [--force] # Apply implementation workflow
```

### File Operations Module

**Responsibilities**:
- Copy files from resources to `.claude/`
- Set executable permissions on shell scripts
- Skip existing files (unless --force)
- Track copied files for manifest

**Key Functions**:
```python
def copy_workflow_files(workflow_name, force=False) -> list[dict]:
    """Copy all workflow files to .claude/ directory."""

def make_executable(file_path):
    """Set executable permission on file."""

def ensure_directory(path):
    """Create directory if it doesn't exist."""
```

### Settings Manager

**Responsibilities**:
- Load/parse JSON files
- Deep merge settings
- Validate JSON structure
- Write atomically (temp file + rename)

**Key Functions**:
```python
def merge_settings(workflow_settings) -> list[str]:
    """Merge workflow settings into .claude/settings.json."""

def validate_json(data, schema=None):
    """Validate JSON structure."""

def atomic_write_json(path, data):
    """Write JSON file atomically."""
```

### Backup Manager

**Responsibilities**:
- Create timestamped backups
- Restore from backup
- Clean up old backups (optional)

**Key Functions**:
```python
def create_backup() -> str:
    """Create timestamped backup of .claude/ directory."""

def restore_backup(backup_path):
    """Restore .claude/ from backup."""

def list_backups() -> list[str]:
    """List available backups."""
```

### State Tracker

**Responsibilities**:
- Read/write config.json
- Read/write manifest.json
- Track applied workflows
- Update active workflow

**Key Functions**:
```python
def update_config(workflow_name):
    """Update active workflow in config."""

def create_manifest(workflow_name, files, hooks, settings):
    """Create workflow manifest."""

def get_active_workflow() -> str:
    """Get currently active workflow."""
```

## Data Flow

### Workflow Application Flow

```
1. User runs: synapse workflow feature-planning

2. Validate:
   - Check .synapse/ exists
   - Check workflow exists in resources
   - Check for conflicts (unless --force)

3. Create backup:
   - Timestamp: 20251020_143022
   - Copy entire .claude/ to .synapse/backups/20251020_143022/

4. Copy files:
   - agents/*.md → .claude/agents/
   - hooks/* → .claude/hooks/ (set executable on .sh)
   - commands/synapse/* → .claude/commands/synapse/

5. Merge settings:
   - Load workflow settings.json
   - Load .claude/settings.json (or create empty)
   - Deep merge with array appending
   - Validate result
   - Write atomically

6. Update state:
   - Add to config.json applied_workflows[]
   - Set config.json active_workflow
   - Create workflow-manifest.json with file list

7. Report success:
   - List copied files
   - List added hooks
   - Show settings changes
```

### Workflow Removal Flow

```
1. User runs: synapse workflow remove

2. Validate:
   - Check .synapse/ exists
   - Check manifest exists
   - Confirm with user

3. Restore from backup:
   - Find latest backup
   - Delete current .claude/ contents
   - Copy backup → .claude/

4. Update state:
   - Remove from config.json applied_workflows[]
   - Clear config.json active_workflow
   - Delete workflow-manifest.json

5. Report success:
   - List removed files
   - Confirm restoration
```

## Error Handling Strategy

### Categories

1. **User Errors** (exit code 1):
   - Invalid command syntax
   - Missing required arguments
   - Workflow not found

2. **State Errors** (exit code 2):
   - .synapse/ not initialized
   - No workflow active
   - Manifest missing/corrupted

3. **System Errors** (exit code 3):
   - File permission denied
   - Disk full
   - JSON parse error

4. **Validation Errors** (exit code 4):
   - File conflicts without --force
   - Invalid JSON schema
   - Corrupted backup

### Error Recovery

- **Atomic Operations**: Use temp files + rename for all writes
- **Rollback**: Restore from backup on any failure during application
- **Validation**: Check all inputs before making changes
- **Clear Messages**: Provide actionable error messages with suggested fixes

## Testing Strategy

### Unit Tests
- Settings merge logic
- JSON validation
- Path operations
- State tracking

### Integration Tests
- Full workflow application
- Workflow removal
- Backup/restore
- Settings merge with existing files
- Error scenarios

### Manual Tests
- Install via pip/pipx
- Run in real project
- Verify Claude Code integration
- Test hook execution

## Performance Considerations

- **File Operations**: Small files (~KB), performance not critical
- **JSON Parsing**: Config files <1MB, negligible impact
- **Backups**: Copy operations fast for text files
- **No Network**: All operations local, no latency concerns

**Expected Performance**:
- Workflow application: <1 second
- Workflow removal: <1 second
- Backup creation: <500ms

## Security Considerations

### File Permissions
- Respect user's umask
- Set executable only on .sh files
- Don't modify permissions on existing files

### Path Traversal
- Validate all file paths
- Use `os.path.abspath()` to resolve paths
- Reject paths containing `..`

### JSON Injection
- Use stdlib `json` module (no eval)
- Validate structure before merging
- Sanitize user-provided values

### Secrets
- Never log file contents
- Don't store credentials
- Warn if sensitive files detected (e.g., .env)

## Future Extensibility

### Designed For
- Adding new workflows (just add to resources/)
- Version upgrades (track CLI version in manifest)
- Additional commands (argparse subparsers)

### Not Designed For
- Plugin architecture
- Remote workflow repositories
- Multi-project management
- Custom workflow creation by users

## Dependencies Justification

### Required
- **Python 3.9+**: Minimum for modern features, wide adoption
- **setuptools**: Standard packaging, entry points, resource management

### Runtime (User's System)
- **uv**: Required for Python hook execution in workflows
- **Playwright**: Optional, only needed if using verifier agent

### Development
- **pytest**: Testing framework
- **ruff**: Linting
- **mypy**: Type checking

## Deployment

### Installation Methods
```bash
# Via pip
pip install synapse-cli

# Via pipx (recommended)
pipx install synapse-cli

# Editable install (development)
pip install -e .
```

### Distribution
- **PyPI**: Primary distribution channel
- **wheel**: Binary distribution format
- **sdist**: Source distribution for compatibility

---

## Alternatives Considered

### Alternative 1: Configuration DSL
**Rejected**: Too complex for simple file copying and settings merge.

### Alternative 2: Git-based Workflow Sharing
**Rejected**: Adds complexity, not needed for two bundled workflows.

### Alternative 3: Interactive TUI
**Rejected**: CLI simpler for automation and CI/CD integration.

### Alternative 4: Plugin Architecture
**Rejected**: Overengineering for current scope.

## Open Technical Questions

1. **Q**: Should we validate Python hook syntax before copying?
   **A**: No - let uv/Python handle syntax errors at runtime.

2. **Q**: Maximum backup retention?
   **A**: Keep last 10 backups, user can manually clean `.synapse/backups/`.

3. **Q**: Should sense command detect existing Synapse installations?
   **A**: Yes - should detect and warn about version mismatches.

4. **Q**: Handle corrupt manifest files?
   **A**: Attempt recovery from backup, otherwise require manual cleanup.

---

## References

- PRD: `/Users/alexabrams/Workspace/synapse/PRD.md`
- Project Context: `openspec/project.md`
- Claude Code Documentation: (user's existing knowledge)
- Python Packaging: https://packaging.python.org/
