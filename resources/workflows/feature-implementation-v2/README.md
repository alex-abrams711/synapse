# Feature Implementation Workflow v2 (Option 6)

**Simplified QA verification with user control over fix timing**

## Overview

This workflow implements a radically simplified approach to quality verification with multi-layer protection:

- **Dumb Hooks**: Simple checkers that enforce workflow rules
- **Smart Agent**: Performs actual verification with full tool access
- **User Control**: Can stop with failures and decide when to fix them
- **Protection Layers**: Prevents work bypass and unauthorized field updates

**Hook System:**
1. **UserPromptSubmit**: Reminds agent of workflow rules
2. **PreToolUse**: Blocks source edits without active_tasks set
3. **PostToolUse**: Blocks unauthorized UV field modifications
4. **Stop**: Validates QA status before allowing completion

## Key Innovation: Three-Category QA Status

```
[Not Started]        → NOT VERIFIED → Hook blocks (Exit 2)
[Passed]/[Complete]  → VERIFIED SUCCESS → Hook allows (Exit 1)
[Failed - {reason}]  → VERIFIED FAILURE → Hook allows (Exit 1)
```

**Why this matters:**
- Old approach: Can't stop until everything passes (stuck in fix loop)
- Option 6: Can stop after verification regardless of outcome
- Failed tasks stay tracked until user decides to address them

## Architecture

### 1. Stop Hook (`hooks/stop_qa_check.py`)

**What it does:**
- Reads `active_tasks` from config
- Checks QA Status field for each active task
- Blocks if ANY task has `[Not Started]`
- Allows if ALL tasks are verified (including failures)

**What it does NOT do:**
- Run quality checks (agent's job)
- Execute tests or linting (agent's job)
- Fix anything (agent's job)
- Make decisions (user's job)

**Exit Codes:**
- `1` - All active tasks verified (allow stop, show verification report to user)
- `2` - Verification required (block stop, provide directive)

### 2. UserPromptSubmit Hook (`hooks/user-prompt-reminder.sh`)

**What it does:**
- Reminds agent to set `active_tasks` when starting work
- Reminds agent to clear `active_tasks` when done
- Shows workflow for handling failures
- Explains QA Status values
- **Reminds agent NEVER to update UV fields**

**Runs on:** Every user message

### 3. PreToolUse Hook (`hooks/active-tasks-enforcer.py`)

**What it does:**
- Intercepts Edit and Write tool calls BEFORE they execute
- Checks if active_tasks is set in config
- Identifies "source files" vs "config/docs files"
- Blocks source file edits if active_tasks is empty
- Allows config/docs/task file edits without active_tasks

**File Detection Logic:**
- **Always Allowed** (no active_tasks needed):
  - .synapse/config.json, .claude/ (workflow config)
  - README.md, docs/, CHANGELOG.md (documentation)
  - tasks.md, openspec/changes/ (task files)
  - .gitignore, .env.example (dev environment)
- **Requires active_tasks** (source files):
  - Code files: .py, .js, .ts, .tsx, .go, .rs, .java, etc.
  - Style files: .css, .scss, .sass, etc.
  - Files in quality-config project paths
  - Shell scripts: .sh, .bash

**Exit Codes:**
- `0` - Success: active_tasks set OR not a source file (allow operation)
- `2` - Block: Editing source code without active_tasks set

**Why this is needed:**
- Prevents work bypass: Can't do work without tracking it
- Ensures QA verification: Stop hook can validate tracked work
- Closes loophole: Empty active_tasks + code changes = no verification

**Runs on:** Before Edit or Write tool use

### 4. PostToolUse Hook (`hooks/task-edit-validator.py`)

**What it does:**
- Intercepts Edit and Write tool calls targeting task files
- Detects changes to User Verification (UV) status fields
- Blocks edits that modify UV field values
- Allows all other task file modifications (DS, QA, descriptions, subtasks)

**What it does NOT do:**
- Block legitimate task updates (DS/QA fields are agent-editable)
- Block new task creation (UV defaults to `[Not Started]` are allowed)
- Interfere with non-task file edits

**Exit Codes:**
- `0` - Success: No UV field modifications (allow operation)
- `2` - Block: UV field modification detected (provide detailed error)

**Why this is needed:**
- UV fields are for user approval only
- Agents should never mark tasks as user-verified
- Maintains clear separation between technical validation (agent) and user acceptance (user)

**Runs on:** After Edit or Write tool use

## Workflow Examples

### Example 1: All Tasks Pass

```
1. Agent starts work on T001, T002
   → Sets active_tasks: ["T001", "T002"]

2. Agent tries to stop
   → Hook blocks (Exit 2): "Tasks need verification"

3. Agent runs quality checks
   → All checks pass
   → Updates QA Status: [Passed]

4. Agent tries to stop
   → Hook allows (Exit 1): Shows verification report with all tasks passed

5. Agent clears active_tasks: []
   → Stops successfully
```

### Example 2: Some Tasks Fail (Option 6 Advantage)

```
1. Agent starts work on T001, T002, T003
   → Sets active_tasks: ["T001", "T002", "T003"]

2. Agent verifies all tasks
   → T001: [Passed]
   → T002: [Failed - lint errors on line 45, 67]
   → T003: [Passed]

3. Agent tries to stop
   → Hook allows (Exit 1): Shows verification report with pass/fail breakdown

4. Agent asks user: "Would you like me to fix the failed tasks?"

5a. User says "No"
   → Agent removes passed tasks from active_tasks
   → Keeps: ["T002"]
   → Stops successfully
   → User can fix T002 later

5b. User says "Yes"
   → Agent fixes issues in T002
   → Sets QA Status back to [Not Started]
   → Re-verifies
   → Updates to [Passed]
   → Clears active_tasks: []
   → Stops
```

### Example 3: Resuming Failed Tasks

```
1. User returns to project with active_tasks: ["T002"]
   → T002 has QA Status: [Failed - lint errors]

2. Hook allows stop (already verified as failed)

3. User asks agent to fix T002

4. Agent fixes issues
   → Sets QA Status: [Not Started] (needs re-verification)

5. Agent tries to stop
   → Hook blocks (Exit 2): "T002 needs verification"

6. Agent re-verifies
   → Updates QA Status: [Passed]

7. Agent clears active_tasks: []
   → Stops successfully
```

## Agent Responsibilities

### Starting Work

```json
// In .synapse/config.json
{
  "third_party_workflow": {
    "active_tasks": ["T001", "T002"],  // Set when starting
    "active_tasks_file": "tasks.md",
    // ...
  }
}
```

### During Verification

Run ALL quality checks for each task:

```bash
# From config.json quality-config.commands
ruff check .
pytest
mypy .
pytest --cov
python -m build
```

Mark QA Status based on results:
- **All pass**: `[Passed]` or `[Complete]`
- **Any fail**: `[Failed - {specific details}]`
  - Include which checks failed
  - Include error messages
  - Include line numbers

### After Verification

**If all tasks passed:**
```markdown
1. Generate completion report
2. Clear active_tasks to []
3. Stop
```

**If any tasks failed:**
```markdown
1. Present results to user with pass/fail breakdown
2. Ask: "Would you like me to fix the failed tasks?"
3. If NO:
   - Remove passed tasks from active_tasks
   - Keep failed tasks
   - Stop
4. If YES:
   - Fix issues
   - Set QA Status back to [Not Started]
   - Re-verify
```

## Task File Format

Tasks must include QA Status field with task code:

```markdown
[ ] - T001 - Implement user login
  [ ] - T001-ST001 - Create POST /api/auth/login
  [ ] - T001-DS - Dev Status: [Not Started]
  [ ] - T001-QA - QA Status: [Not Started]
  [ ] - T001-UV - User Verification Status: [Not Started]

[ ] - T002 - Implement user registration
  [ ] - T002-ST001 - Create POST /api/auth/register
  [ ] - T002-DS - Dev Status: [Complete]
  [ ] - T002-QA - QA Status: [Passed]
  [ ] - T002-UV - User Verification Status: [Not Started]
```

**QA Status values:**
- `[Not Started]` - Not verified (hook blocks)
- `[Passed]` or `[Complete]` - Verified successfully (hook allows)
- `[Failed - {reason}]` - Verified with failures (hook allows)

### Status Field Ownership

Each task has three status fields with different ownership rules:

**Dev Status (DS)** - Agent updates
- Agent sets to `[In Progress]` when starting work
- Agent sets to `[Complete]` when implementation is done
- Tracks development progress

**QA Status (QA)** - Agent updates
- Agent runs quality checks (lint, test, typecheck, coverage, build)
- Agent sets to `[Passed]` or `[Complete]` if all checks pass
- Agent sets to `[Failed - {specific reason}]` if checks fail
- Must include failure details (which checks, error messages, line numbers)

**User Verification (UV)** - USER ONLY ⚠️
- **Agents must NEVER update this field**
- Only users can mark tasks as `[Verified]`
- Used for final user acceptance and sign-off
- Allows users to review and approve work independently
- **Enforced by PostToolUse hook** - attempts to modify UV fields will be blocked

This separation ensures:
- Agents handle technical validation (DS, QA)
- Users maintain final approval authority (UV)
- Clear audit trail of who verified what

## Configuration

### Required Fields

```json
{
  "third_party_workflow": {
    "type": "openspec",
    "active_tasks_file": "tasks.md",
    "active_tasks": [],
    "task_format_schema": {
      "version": "2.0",
      "patterns": {
        "task": "regex pattern",
        "status_field": "regex pattern"
      },
      "field_mapping": {
        "qa": "QA"
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
  }
}
```

## Exit 2 Directive

When the hook blocks, it provides a comprehensive directive including:

1. **Active Tasks Needing Verification**
   - List of tasks and reasons

2. **Quality Commands** (from config.json)
   - All configured quality check commands

3. **Verification Process**
   - Step-by-step instructions
   - How to run checks
   - How to update status
   - How to handle failures

4. **Completion Report Format**
   - Template for success reporting

## Testing

Unit tests: `tests/test_stop_qa_check.py` (15 tests)
Integration tests: `tests/integration/test_full_workflow.py` (6 tests)

Run tests:
```bash
pytest tests/test_stop_qa_check.py -v
pytest tests/integration/test_full_workflow.py -v
```

## Troubleshooting

### Hook blocks but tasks show [Passed]

Check that task codes in `active_tasks` exactly match codes in task file.

### Hook allows stop but I want it to block

Ensure QA Status is `[Not Started]`, not `[Failed - ...]`.

### Agent forgot to set active_tasks

UserPromptSubmit hook reminds agent on every message. Check hook is configured.

### Failed task keeps blocking

Failed tasks allow stop. If blocking, QA Status is likely `[Not Started]` or missing.

## Philosophy

**The hook should be dumb, the agent should be smart.**

- Hooks are unreliable execution environments
- Agents have full context and tools
- Users should control fix timing
- Verification state should persist

This workflow embraces these principles for a robust, flexible verification system.
