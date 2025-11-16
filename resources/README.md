# Synapse Workflows (Option 6)

This directory contains the new Option 6 implementation of Synapse workflows, featuring simplified QA verification and user-controlled fix timing.

## Directory Structure

```
resources/
├── schemas/
│   └── synapse-config-schema.json         # Config validation schema
├── workflows/
│   ├── feature-implementation/         # Option 6 implementation workflow
│   │   ├── hooks/
│   │   │   ├── stop_qa_check.py          # Simple QA status checker (~400 lines)
│   │   │   └── user-prompt-reminder.sh   # Active tasks management reminder
│   │   ├── settings.json                  # Hook configuration
│   │   └── README.md                      # Detailed workflow documentation
│   └── feature-planning/                  # Task breakdown workflow
│       ├── agents/
│       │   └── writer.md                  # Task writing specialist
│       ├── hooks/
│       │   ├── writer-post-tool-use.py   # Format validation
│       │   └── user-prompt-reminder.sh   # Workflow reminder
│       ├── settings.json                  # Hook configuration
│       └── README.md                      # Workflow documentation
└── README.md (this file)
```

## Workflows

### Feature Implementation

**Purpose:** Simplified QA verification with user control

**Key Features:**
- Dumb hook (checks status only)
- Smart agent (runs quality checks)
- Three-category QA Status semantics
- User controls fix timing

**Use when:** Implementing features with quality verification

**Documentation:** [workflows/feature-implementation/README.md](workflows/feature-implementation/README.md)

### Feature Planning

**Purpose:** Break down features into well-structured tasks

**Key Features:**
- Writer sub-agent for task creation
- Mandatory formatting validation
- Task code generation (T001, T002, etc.)
- Quality gate inclusion

**Use when:** Planning new features or work items

**Documentation:** [workflows/feature-planning/README.md](workflows/feature-planning/README.md)

## Quick Start

### 1. Configure Your Project

Ensure your `.synapse/config.json` has the new structure:

```json
{
  "third_party_workflow": {
    "type": "openspec",
    "active_tasks_file": "tasks.md",
    "active_tasks": [],
    "task_format_schema": {
      "version": "2.0",
      "patterns": { /* ... */ },
      "field_mapping": { /* ... */ },
      "status_semantics": { /* ... */ }
    }
  }
}
```

### 2. Plan Your Feature

Use the feature-planning workflow:

```
Call the writer agent to break down your feature into tasks
```

Result: Formatted tasks with codes in `tasks.md`

### 3. Implement Features

Use the feature-implementation workflow:

1. Set `active_tasks` in config when starting work
2. Implement tasks
3. Try to stop → hook blocks with verification directive
4. Run quality checks
5. Update QA Status based on results
6. Handle failures (fix now or later)
7. Clear `active_tasks` when done

### 4. Understand Exit Codes

**Exit 0:** All active tasks verified → Allow stop
**Exit 2:** Verification required → Block stop, provide directive

## Core Concepts

### Active Tasks Management

**Agent responsibilities:**
- Set `active_tasks: ["T001", "T002"]` when starting work
- Clear `active_tasks: []` when done
- Update QA Status after verification

**Hook responsibilities:**
- Check QA Status for each active task
- Block if any task is `[Not Started]`
- Allow if all tasks are verified

### QA Status Semantics (Option 6)

```
[Not Started]        → NOT VERIFIED → Hook blocks
[Passed]/[Complete]  → VERIFIED SUCCESS → Hook allows
[Failed - {reason}]  → VERIFIED FAILURE → Hook allows
```

**Why this works:**
- User can stop after verification regardless of outcome
- Failed tasks stay in `active_tasks` for later
- User decides when to fix failures

### Task Format

Tasks use codes for tracking:

```markdown
[ ] - T001 - Task description
  [ ] - T001-ST001 - Subtask
  [ ] - T001-DS - Dev Status: [Complete]
  [ ] - T001-QA - QA Status: [Passed]
  [ ] - T001-UV - User Verification Status: [Not Started]
```

## Testing

**Unit tests:** `tests/test_stop_qa_check.py`
- 15 tests covering all edge cases
- Schema-driven parsing
- Exit code validation

**Integration tests:** `tests/integration/test_full_workflow.py`
- 6 full workflow scenarios
- Option 6 behavior verification
- Fix-and-reverify cycles

Run tests:
```bash
pytest tests/test_stop_qa_check.py -v
pytest tests/integration/test_full_workflow.py -v
```

## Design Philosophy

**"The hook should be dumb, the agent should be smart."**

### Why?

**Hooks are unreliable:**
- Limited execution environment
- No conversation context
- Prone to timeouts
- Hard to debug

**Agents are powerful:**
- Full tool access
- Conversation context
- Can ask questions
- Can provide detailed reports

### Solution

**Hook:** Simple status checker (~400 lines)
- Only reads config and task file
- Only checks QA Status values
- Only returns exit codes

**Agent:** Smart verifier (unlimited)
- Runs all quality checks
- Analyzes results
- Updates status fields
- Handles failures
- Reports to user

## Common Workflows

### All Tasks Pass

```
1. Start: Set active_tasks
2. Implement: Write code
3. Stop attempt: Hook blocks
4. Verify: Run checks, all pass
5. Update: Mark [Passed]
6. Stop attempt: Hook allows
7. Clean: Clear active_tasks
```

### Some Tasks Fail

```
1. Start: Set active_tasks
2. Implement: Write code
3. Stop attempt: Hook blocks
4. Verify: Run checks, some fail
5. Update: Mark [Passed] or [Failed - ...]
6. Stop attempt: Hook allows
7. User choice:
   a. Fix now: Fix, mark [Not Started], re-verify
   b. Fix later: Remove passed from active_tasks, keep failed
```

### Resume Failed Tasks

```
1. Context: active_tasks has failed task
2. User: "Fix T002"
3. Agent: Fixes issues
4. Agent: Marks [Not Started]
5. Stop attempt: Hook blocks
6. Verify: Re-run checks
7. Update: Mark [Passed]
8. Clean: Clear active_tasks
```

## Getting Help

**Troubleshooting:**
1. Check workflow README files
2. Review test cases for examples
3. Run hooks manually for debugging
4. Check `.synapse/logs/` for errors

**Common issues:**
- Hook blocks unexpectedly → Check `active_tasks` values
- Hook allows but shouldn't → Check QA Status values
- Task not found → Verify task codes match
- Schema errors → Validate regex patterns

**Resources:**
- [Feature Implementation README](workflows/feature-implementation/README.md)
- [Feature Planning README](workflows/feature-planning/README.md)
- [Migration Guide](../MIGRATION_GUIDE.md)

## Contributing

When adding new workflows to this directory:

1. Follow the Option 6 design philosophy
2. Keep hooks simple and focused
3. Empower agents with tools and context
4. Provide clear exit codes and directives
5. Include comprehensive tests
6. Document thoroughly

## Version

**Synapse Option 6** - Simplified QA verification with user control

**Status:** Active development, production ready

**Compatibility:** Requires new config structure (see schema)
