# Synapse Architecture

This document provides a comprehensive overview of the Synapse system architecture, design decisions, and component interactions.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow](#data-flow)
4. [Technology Stack](#technology-stack)
5. [Design Decisions](#design-decisions)
6. [Testing Strategy](#testing-strategy)

---

## System Overview

### Purpose

Synapse is an AI-first workflow system that integrates with Claude Code to provide automated quality enforcement and workflow management for development projects.

### Core Value Proposition

- **Simplified QA Verification**: Option 6 architecture with "dumb hooks, smart agent" approach
- **Quality Gate Enforcement**: Multi-layer protection preventing work bypass
- **Schema-Driven Flexibility**: Format-agnostic task parsing
- **User Control**: Stop with failures, fix on your schedule

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User / Claude Code                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ├─────┬──────────────────────────────────┐
                     │     │                                  │
          ┌──────────▼─┐  ┌▼────────────┐     ┌─────────────▼──┐
          │  Synapse   │  │   Hooks     │     │    Agent       │
          │    CLI     │  │  (Quality   │     │  (Claude Code) │
          │            │  │   Gates)    │     │                │
          └──────┬─────┘  └─────┬───────┘     └────────┬───────┘
                 │              │                       │
                 │              │    ┌──────────────────┘
                 │              │    │
          ┌──────▼──────────────▼────▼───┐
          │      .synapse/config.json     │
          │   (Source of Truth)           │
          └───────────────────────────────┘
```

---

## Component Architecture

### 1. CLI Layer

**File**: `src/synapse_cli/__init__.py` (1823 lines)

**Responsibilities:**
- Project initialization (`synapse init`)
- Workflow management (list, apply, remove, status)
- Configuration management
- Backup/restore operations
- File copying and merging

**Key Functions:**
```python
main()                    # Entry point, command routing
init_project()            # Initialize .synapse directory
workflow_list()           # Discover available workflows
workflow_apply()          # Apply workflow to project
workflow_remove()         # Remove workflow, restore backup
workflow_status()         # Show active workflow state
```

**Design Pattern**: Command pattern with argparse routing

---

### 2. Workflow Layer

**Location**: `resources/workflows/`

**Available Workflows:**
- `feature-implementation-v2/` - Option 6 QA verification
- `feature-planning/` - Task breakdown and formatting

**Workflow Structure:**
```
workflow-name/
├── hooks/               # Hook scripts
│   ├── stop_qa_check.py
│   ├── active-tasks-enforcer.py
│   ├── task-edit-validator.py
│   └── user-prompt-reminder.sh
├── commands/            # Slash commands (optional)
│   └── synapse/
│       └── sense.md
├── settings.json        # Hook configuration
└── README.md           # Workflow documentation
```

---

### 3. Hook System

**Integration Point**: `.claude/settings.json`

**Hook Types:**

#### UserPromptSubmit Hook
**File**: `user-prompt-reminder.sh`
- Runs on every user message
- Reminds agent of workflow rules
- Explains active_tasks management
- Exit 0 always (informational only)

#### PreToolUse Hook
**File**: `active-tasks-enforcer.py` (~150 lines)
- Intercepts Edit/Write operations
- Checks if source files require active_tasks
- Blocks code edits without tracked work
- Exit 0 = allow, Exit 2 = block

#### PostToolUse Hook
**File**: `task-edit-validator.py`
- Detects User Verification field modifications
- Blocks unauthorized UV updates
- Allows DS and QA field edits
- Exit 0 = allow, Exit 2 = block

#### Stop Hook
**File**: `stop_qa_check.py` (~535 lines)
- Validates QA Status for active tasks
- Blocks if any task is [Not Started]
- Allows if all tasks verified (including failures)
- Exit 1 = allow with report, Exit 2 = block

---

### 4. Configuration System

**Source of Truth**: `.synapse/config.json`

**Schema Structure:**
```json
{
  "synapse_version": "0.1.0",
  "initialized_at": "ISO 8601 timestamp",
  "agent": {
    "type": "claude_code",
    "description": "Selected AI assistant"
  },
  "project": {
    "name": "project-name",
    "description": "Project description",
    "root_directory": "/absolute/path"
  },
  "workflows": {
    "active_workflow": "feature-implementation-v2",
    "applied_workflows": [
      {
        "name": "feature-implementation-v2",
        "applied_at": "2024-11-14T10:30:00Z"
      }
    ]
  },
  "quality-config": {
    "mode": "single|monorepo",
    "projectType": "python|node|rust|...",
    "commands": {
      "lint": "ruff check .",
      "test": "pytest",
      "typecheck": "mypy .",
      "coverage": "pytest --cov",
      "build": "python -m build"
    },
    "thresholds": {
      "coverage": {
        "lines": 80,
        "branches": 75
      }
    }
  },
  "third_party_workflow": {
    "type": "openspec|spec-kit|custom",
    "active_tasks_file": "tasks.md",
    "active_tasks": ["T001", "T002"],
    "task_format_schema": {
      "version": "2.0",
      "patterns": {
        "task": "regex",
        "subtask": "regex",
        "status_field": "regex"
      },
      "field_mapping": {
        "dev_status": "DS",
        "qa": "QA",
        "user_verification": "UV"
      },
      "status_semantics": {
        "states": {
          "qa": {
            "not_verified": ["Not Started"],
            "verified_success": ["Complete", "Passed"],
            "verified_failure_pattern": "^Failed - .*"
          }
        }
      }
    }
  },
  "settings": {
    "auto_backup": true,
    "strict_validation": true,
    "uv_required": true
  }
}
```

**Canonical Schema**: `resources/schemas/synapse-config-schema.json` (565 lines)

---

### 5. Task Schema Parser

**Files**:
- `src/synapse_cli/parsers/task_schema_parser.py` (296 lines)
- `src/synapse_cli/parsers/schema_generator.py`
- `src/synapse_cli/parsers/schema_validator.py`

**Responsibilities:**
- Parse task files using schema patterns
- Extract task codes, descriptions, status fields
- Normalize status values to semantic states
- Generate schemas from actual task files

**Key Classes:**
```python
class TaskSchemaParser:
    def __init__(self, schema: Dict)
    def parse_tasks_file(self, file_path: str) -> List[ParsedTask]
    def validate_schema(self) -> bool

class ParsedTask:
    task_code: str
    description: str
    dev_status: str      # Semantic state
    qa_status: str       # Semantic state
    uv_status: str       # Semantic state
    raw_status: Dict     # Original values
```

**Innovation**: Format-agnostic parsing supporting OpenSpec, GitHub Spec Kit, custom formats

---

## Data Flow

### Workflow Application Flow

```
User: synapse workflow feature-implementation-v2
  │
  ├─> CLI validates preconditions
  │     - .synapse directory exists
  │     - Workflow exists in resources/
  │
  ├─> CLI creates backup
  │     - Backup .claude/ → .synapse/backups/TIMESTAMP/
  │
  ├─> CLI copies workflow files
  │     - resources/workflows/NAME/hooks/ → .claude/hooks/
  │     - resources/workflows/NAME/commands/ → .claude/commands/
  │
  ├─> CLI merges settings
  │     - Merge settings.json → .claude/settings.json
  │     - Convert hook paths to absolute
  │
  ├─> CLI creates manifest
  │     - Save file list to .synapse/workflow-manifest.json
  │
  └─> CLI updates config
        - Set active_workflow in .synapse/config.json
        - Add to applied_workflows history
```

### Stop Hook Verification Flow

```
Agent tries to stop
  │
  ├─> Stop hook executes
  │     - Load .synapse/config.json
  │     - Extract third_party_workflow.active_tasks
  │
  ├─> Hook parses task file
  │     - Use task_format_schema patterns
  │     - Find each active task by code
  │
  ├─> Hook checks QA Status
  │     - For each active task:
  │       - Extract QA Status value
  │       - Categorize: not_verified, verified_success, verified_failure
  │
  ├─> Hook decides exit code
  │     - If ANY task is not_verified → Exit 2 (block)
  │     - If ALL tasks verified → Exit 1 (allow, show report)
  │
  └─> Claude Code interprets exit code
        - Exit 2: Show directive, prevent stop
        - Exit 1: Show report, allow stop
```

### Agent Verification Flow

```
Agent receives verification directive
  │
  ├─> Agent runs quality checks
  │     - Execute commands from quality-config
  │     - Lint, test, typecheck, coverage, build
  │
  ├─> Agent collects results
  │     - Parse command outputs
  │     - Identify failures with details
  │
  ├─> Agent updates task file
  │     - For passed tasks: QA Status = [Passed]
  │     - For failed tasks: QA Status = [Failed - {reason}]
  │
  ├─> Agent tries to stop (hook allows - all verified)
  │
  ├─> Agent presents results to user
  │     - Show pass/fail breakdown
  │     - Ask: "Fix failed tasks?"
  │
  └─> Agent updates active_tasks
        - If user says NO: Remove passed, keep failed
        - If user says YES: Fix issues, set [Not Started], re-verify
```

---

## Technology Stack

### Core Technologies

**Language**: Python 3.9+

**Why Python:**
- Standard library provides all needed functionality
- Excellent file system and JSON handling
- Cross-platform compatibility
- Easy subprocess management
- No compilation needed

### Dependencies

**Runtime**: None (pure standard library)

**Development**:
```toml
pytest>=7.0.0        # Testing framework
pytest-cov>=4.0.0    # Coverage reporting
```

**Philosophy**: Minimal dependencies reduce installation issues and maintenance burden

### Build System

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project.scripts]
synapse = "synapse_cli:main"
```

### File System Layout

```
synapse/
├── src/synapse_cli/              # Core CLI code
│   ├── __init__.py              # Main CLI (1823 lines)
│   ├── __main__.py              # Entry point
│   └── parsers/                 # Schema parsing
│       ├── task_schema_parser.py
│       ├── schema_generator.py
│       └── schema_validator.py
├── resources/                    # Packaged workflows
│   ├── schemas/                 # JSON schemas
│   ├── settings/                # Config templates
│   └── workflows/               # Workflow definitions
├── legacy/                      # Pre-Option 6 code
├── tests/                       # Test suite
│   ├── test_stop_qa_check.py
│   ├── integration/
│   ├── e2e/
│   └── legacy/
├── docs/                        # Documentation
└── pyproject.toml               # Package configuration
```

---

## Design Decisions

### 1. "Dumb Hooks, Smart Agent"

**Decision**: Hooks check status only; agents perform verification

**Rationale**:
- Hooks have limited execution environment
- Hooks lack conversation context
- Hooks are prone to timeouts
- Agents have full tool access
- Agents can ask clarifying questions
- Agents can generate detailed reports

**Result**:
- Compact hook code (~400 lines)
- Fast execution (0.2-0.5s)
- Token-efficient verification
- Reliable quality enforcement

### 2. Three-Category QA Status

**Decision**: Treat failures as verified state

**Categories**:
- `[Not Started]` - Not verified → Block
- `[Passed]`/`[Complete]` - Verified success → Allow
- `[Failed - {reason}]` - Verified failure → Allow

**Rationale**:
- User controls fix timing (not forced into fix loop)
- Failed tasks stay tracked for later
- Enforces verification without forcing fixes
- Flexibility without compromising quality

**Result**:
- Users can stop after verification
- Failed tasks remain visible
- More flexible workflow

### 3. Single Workflow Per Project

**Decision**: `third_party_workflow` (object) not array

**Rationale**:
- Simpler configuration
- Clear active workflow
- Easier to reason about
- Most projects use one task format

**Note**: Sense command prompts user to choose if multiple workflows detected

### 4. Schema-Driven Task Parsing

**Decision**: Dynamically parse tasks using schema patterns

**Rationale**:
- Support any task format (OpenSpec, Spec Kit, custom)
- No hardcoded format assumptions
- Auto-generate schemas from actual files
- Semantic state normalization

**Result**:
- Works with multiple workflow systems
- Format-agnostic
- Easy to add new formats

### 5. Multi-Layer Protection

**Decision**: Four complementary hooks (defense in depth)

**Layers**:
1. UserPromptSubmit: Remind workflow rules
2. PreToolUse: Block work without tracking
3. PostToolUse: Prevent UV tampering
4. Stop: Verify QA completion

**Rationale**:
- Single hooks can be bypassed
- Multiple layers provide redundancy
- Each layer has specific purpose
- Comprehensive coverage

### 6. Backup Before Apply

**Decision**: Always create backup before workflow changes

**Rationale**:
- Safe rollback capability
- Preserve user customizations
- Enable workflow switching
- Recover from errors

**Implementation**:
- Timestamped backups in `.synapse/backups/`
- Manifest tracking for precise removal
- Automatic cleanup of empty directories

---

## Testing Strategy

### Test Organization

```
tests/
├── test_stop_qa_check.py              # Option 6: Stop hook tests (15 tests)
├── test_schema_generator.py           # Schema generation
├── test_task_schema_parser.py         # Parser tests
├── test_edge_cases.py                 # Edge cases
├── integration/
│   └── test_full_workflow.py          # Full workflow scenarios (6 tests)
├── e2e/
│   └── test_full_verification_loop.py # End-to-end tests
└── legacy/                            # Pre-Option 6 tests
```

### Test Categories

**Pytest Markers**:
```python
markers = [
    "legacy: Tests for legacy implementation",
    "option6: Tests for Option 6 implementation",
    "shared: Tests for shared infrastructure",
    "integration: Integration tests",
]
```

### Test Coverage

**Unit Tests** (~15 tests for stop hook):
- Empty active_tasks
- Task file missing
- Task not found
- Missing QA Status field
- All tasks verified (success)
- All tasks verified (with failures)
- Partial verification
- Malformed task files
- Invalid schemas
- Exit code validation

**Integration Tests** (~6 scenarios):
- Complete workflow (all pass)
- Workflow with failures (user fixes)
- Workflow with failures (user defers)
- Resume failed tasks
- Monorepo support
- Schema-driven parsing

**Edge Case Tests**:
- Unicode in task descriptions
- Empty files
- Very large files (100+ tasks)
- Malformed JSON
- Missing fields
- Unknown status values

### Running Tests

```bash
# All tests
pytest tests/

# Option 6 only
pytest tests/test_stop_qa_check.py -v

# With coverage
pytest tests/ --cov=resources --cov=synapse_cli --cov-report=html

# Specific marker
pytest tests/ -m option6
```

---

## Performance Characteristics

### CLI Operations

- **Init**: < 100ms (create directory, copy template)
- **Workflow list**: < 50ms (directory scan)
- **Workflow apply**: < 500ms (file copy, merge, backup)
- **Workflow remove**: < 300ms (restore backup)

### Hook Execution

- **UserPromptSubmit**: < 10ms (echo script)
- **PreToolUse**: < 50ms (file classification check)
- **PostToolUse**: < 50ms (diff detection)
- **Stop**: < 200ms (config load, task parse, status check)

**Timeout Protection**: All hooks have 60-second maximum

### Agent Verification

- **Quality checks**: Depends on project size (1-5 minutes typical)
- **Full tool access**: No artificial limitations
- **Context-aware**: Uses conversation history

### Performance Metrics

| Metric | Value |
|--------|-------|
| Hook execution | 0.2-0.5s |
| Token efficiency | 60-70% optimized |
| Context usage | Single context |
| Hook code size | ~400 lines |

---

## Security Considerations

### Hook Execution Safety

**Timeout Protection**:
```python
import signal

def timeout_handler(signum, frame):
    print("ERROR: Hook timed out", file=sys.stderr)
    sys.exit(2)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(60)  # 60 second maximum
```

**Exit Code Strategy**:
- Exit 0: Success/Allow
- Exit 1: Warning/Show message
- Exit 2: Block operation
- No other codes used

**Input Validation**:
- JSON schema validation for configs
- Regex pattern compilation testing
- File path sanitization
- Error handling for malformed inputs

### File Operations

**Safe File Copying**:
- Check source exists before copying
- Create directories if needed
- Preserve permissions
- Handle symlinks correctly

**Backup Safety**:
- Timestamped backups prevent overwrites
- Verify backup creation before proceeding
- Clean up old backups (keep last 5)

**Config Validation**:
- JSON structure validation
- Required field checking
- Type validation
- Pattern matching validation

---

## Extension Points

### Adding New Workflows

1. Create workflow directory in `resources/workflows/`
2. Add required files (hooks/, settings.json, README.md)
3. Document hook behavior and exit codes
4. Add tests for new workflow
5. Update workflow discovery logic if needed

### Adding New Hook Types

1. Implement hook script (bash or Python)
2. Add to workflow's settings.json
3. Document expected behavior
4. Add exit code handling
5. Test integration with Claude Code

### Adding New Task Formats

1. Create schema with patterns for new format
2. Test schema with actual task files
3. Add to sense command detection logic
4. Document format in schema docs
5. Add integration tests

---

## Troubleshooting

### Common Issues

**Hook doesn't execute:**
- Check `.claude/settings.json` has correct path
- Verify hook file is executable (`chmod +x`)
- Check hook path is absolute (not relative)
- Review `.synapse/logs/` for errors

**Config validation fails:**
- Validate JSON syntax: `python -c "import json; json.load(open('.synapse/config.json'))"`
- Check required fields present
- Verify schema version matches

**Task parsing errors:**
- Test schema patterns against actual task file
- Check regex escaping (use raw strings)
- Verify capture group names match schema
- Review field_mapping codes

**Workflow application fails:**
- Check source workflow exists
- Verify write permissions in `.claude/`
- Review backup creation logs
- Ensure no conflicting files

### Debug Mode

Enable verbose logging:
```bash
export SYNAPSE_DEBUG=1
synapse workflow apply feature-implementation-v2
```

### Manual Hook Testing

Test hooks independently:
```bash
# Test stop hook
python3 resources/workflows/feature-implementation-v2/hooks/stop_qa_check.py

# Check exit code
echo $?
```

---

## Future Considerations

### Potential Enhancements

1. **Automatic active_tasks detection**: Write hook to auto-populate from Dev Status
2. **Task history tracking**: Store verification history in config
3. **CI/CD integration**: Check pipeline status in hooks
4. **Parallel validation**: Run quality checks concurrently
5. **ML-based prioritization**: Rank issues by importance
6. **Incremental validation**: Only check changed files

### Architectural Evolution

Current trajectory suggests continued agent empowerment:
- Further simplification of hooks
- Enhanced agent tool access
- Improved context awareness

---

## References

- **User Guide**: `docs/USER_GUIDE.md`
- **PRD**: `docs/PRD.md`
- **Workflow READMEs**: `resources/workflows/*/README.md`
- **Canonical Schema**: `resources/schemas/synapse-config-schema.json`
- **Test Suite**: `tests/`

---

**Document Status**: Living document, updated with system changes

**Last Updated**: November 14, 2024

**Version**: 1.0
