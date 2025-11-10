# Simplified Stop Hook Approach (Option 6)

## Overview

This document outlines a simplified, two-stage architecture for QA verification in the feature-implementation-v2 workflow:

1. **Hook (Simple)**: Checks if QA verification has been done for active tasks
2. **Agent (Smart)**: Performs the actual verification using all available tools

This approach eliminates the complexity of having the hook run quality checks directly.

**Implementation Approach**: Option 6 - Hybrid approach where:
- Hook enforces verification (blocks if QA Status = [Not Started])
- Hook allows stop with failures (allows if QA Status = [Failed - reason])
- Agent asks user about fixing failures
- User has full control over when to fix vs. defer
- Failed tasks stay tracked in active_tasks until resolved

---

## Implementation Strategy: Fresh Start

**This is a complete rewrite, not an in-place migration.**

### Directory Structure

**Current state:**
```
/synapse
  ├── resources/
  │   ├── schemas/
  │   ├── workflows/
  │   └── ...
```

**New structure:**
```
/synapse
  ├── legacy/
  │   └── resources/          # Existing implementation moved here
  │       ├── schemas/
  │       ├── workflows/
  │       └── ...
  ├── resources/              # Fresh implementation of Option 6
  │   ├── schemas/
  │   │   └── synapse-config-schema.json  (new structure)
  │   └── workflows/
  │       ├── feature-implementation-v2/  (new workflow)
  │       └── feature-planning/          (updated for new format)
```

### Rationale

- **Clean slate**: Build Option 6 from scratch without migration complexity
- **Preservation**: Keep existing implementation for reference
- **No breaking changes mid-stream**: Old and new don't conflict
- **Clear separation**: Legacy vs new approach
- **Easier testing**: Can test new approach independently

### Migration Path for Users

Users running old workflows can:
1. Continue using `legacy/resources/` workflows (no immediate impact)
2. When ready, switch to new `resources/` workflows (fresh config)
3. No forced migration - opt-in when ready

---

## Exit Code Strategy

| Exit Code | Meaning | Use Case |
|-----------|---------|----------|
| **0** | ✅ Success | All active tasks verified, allow stop |
| **1** | ⚠️ Warning | Reserved for future use |
| **2** | ❌ Block | Verification required, agent must verify tasks |

### Exit Code Scenarios

**Exit 0 - Allow Stop:**
- All tasks in `active_tasks` have QA Status verified

**Exit 1 - Warning (Allow Stop):**
- Reserved for future use (currently unused)

**Exit 2 - Block (Verification Required):**
- No active tasks set in config (empty or missing `active_tasks` field)
- Task file doesn't exist (when active_tasks is set)
- Active task code not found in task file
- Task missing QA Status field (treat as needs verification, warn in directive)
- Any active task has QA Status ≠ verified

---

## Architecture Decisions

### Task Scope Discovery
**Decision**: Phase/section-based with config.json tracking

Use `.synapse/config.json` as source of truth for which tasks are actively being worked on.

**BREAKING CHANGE**: Single workflow per project (no array):
```json
{
  "third_party_workflow": {
    "type": "openspec",
    "active_tasks_file": "tasks.md",
    "active_tasks": ["T001", "T002"],
    "task_format_schema": {...}
  }
}
```

**Note**: Changed from `third_party_workflows.detected` (array) to `third_party_workflow` (object).
If multiple workflows are detected by sense command, user must choose one.

### Task Format
**Decision**: Use new task code format with schema-driven parsing

```markdown
[ ] - T001 - Task description
  [ ] - T001-ST001 - Subtask description
  [ ] - T001-DS - Dev Status: [Complete]
  [ ] - T001-QA - QA Status: [Not Started]
  [ ] - T001-UV - User Verification Status: [Not Started]
```

Hook reads `task_format_schema` from config to parse tasks dynamically.

### QA Verification Field
**Decision**: Check QA Status field with three semantic categories

Hook checks: `T001-QA - QA Status: [value]`

Values come from schema:
```json
"status_semantics": {
  "states": {
    "qa": {
      "not_verified": ["Not Started"],
      "verified_success": ["Complete", "Passed"],
      "verified_failure_pattern": "^Failed - .*"
    }
  }
}
```

**Status meanings:**
- `[Not Started]` - Not verified yet → Hook blocks (Exit 2)
- `[Passed]` or `[Complete]` - Verified successfully → Hook allows stop (Exit 0)
- `[Failed - {reason}]` - Verified but failed → Hook allows stop (Exit 0)

The `Failed` status includes a reason (e.g., `[Failed - lint errors line 45]`) to help agent understand what needs fixing.

### Exit 2 Directive Content
**Decision**: Comprehensive directive (Option D)

Include:
- Active tasks needing verification
- Quality commands from config.json
- Full verification process steps
- Completion report format template

### Verification Success Report
**Decision**: Agent-generated with format directive

Required sections:
- Tasks verified
- Quality metrics
- Implementation summary

Format: Structured markdown
Output: Presented to user only (not saved)

### Failure Handling
**Decision**: Always ask user before fixing (Option A)

When verification finds failures:
1. Show which tasks passed/failed
2. Present detailed failure information
3. Propose fix plan
4. Ask: "Would you like me to proceed with the plan to fix the found issues?"
5. Wait for user approval before fixing

### Partial Verification
**Decision**: Mark passed tasks immediately (Option A)

When results are mixed:
- ✅ T001 passes → Mark QA Status: [Complete] immediately
- ❌ T002 fails → Leave QA Status unchanged
- ✅ T003 passes → Mark QA Status: [Complete] immediately

Show progress, only failed tasks need attention.

### State Recovery (Agent Restart) - UPDATED Option 6
**Decision**: Failed tasks with [Failed] status treated as verified (allows stop)

QA Status has three semantic categories:
- **Not Verified**: `[Not Started]` - Hook blocks (Exit 2)
- **Verified Success**: `[Passed]`, `[Complete]` - Hook allows stop (Exit 0)
- **Verified Failure**: `[Failed - {reason}]` - Hook allows stop (Exit 0)

**Hook logic:**
```
IF active_tasks is empty:
  → Exit 0 (no work)

IF active_tasks is non-empty:
  IF ANY task has QA Status = [Not Started] or missing:
    → Exit 2 (must verify these tasks)

  IF ALL tasks have QA Status ∈ {[Passed], [Complete], [Failed - *]}:
    → Exit 0 (all verified, allow stop even with failures)
```

**Agent workflow with failures:**
1. Verifies T001, T002, T003
2. T001 passes → `QA Status: [Passed]`
3. T002 fails → `QA Status: [Failed - lint errors line 45, 67]`
4. T003 passes → `QA Status: [Passed]`
5. Hook allows stop (all verified)
6. Agent reports results and asks user about fixing T002
7. **If user says "no":**
   - Agent removes passed tasks: `active_tasks: ["T002"]` (keep failed only)
   - Agent stops (hook allows - T002 verified as failed)
8. **Next session:** User asks to continue
9. Agent sees `active_tasks: ["T002"]` with `QA Status: [Failed - ...]`
10. Agent fixes T002, sets `QA Status: [Not Started]` (needs re-verification)
11. Agent tries to stop → Hook blocks (Exit 2, must verify)
12. Agent verifies → `QA Status: [Passed]`
13. Agent clears `active_tasks: []`

---

## Implementation Plan

### Part 0: Directory Restructuring

**Move existing implementation to legacy:**

```bash
# Create legacy directory
mkdir -p legacy

# Move current resources to legacy
mv resources legacy/resources

# Create new resources directory structure
mkdir -p resources/schemas
mkdir -p resources/workflows/feature-implementation-v2/hooks
mkdir -p resources/workflows/feature-implementation-v2/agents
mkdir -p resources/workflows/feature-planning/hooks
mkdir -p resources/workflows/feature-planning/agents
```

**Result:**
```
/synapse
  ├── legacy/resources/     # Old implementation (preserved)
  └── resources/            # New Option 6 implementation (fresh start)
```

---

### Part 1: Schema Creation

**File**: `resources/schemas/synapse-config-schema.json`

**BREAKING CHANGE**: Replace `third_party_workflows` (array) with `third_party_workflow` (object):

```json
{
  "third_party_workflow": {
    "type": "object",
    "properties": {
      "type": {
        "type": "string",
        "description": "Workflow type (e.g., 'openspec', 'custom')"
      },
      "active_tasks_file": {
        "type": "string",
        "description": "Path to task file relative to project root"
      },
      "active_tasks": {
        "type": "array",
        "items": {
          "type": "string",
          "pattern": "^T\\d{3,}$"
        },
        "default": [],
        "description": "Task codes currently being worked on (e.g., ['T001', 'T002'])"
      },
      "task_format_schema": {
        "type": "object",
        "description": "Schema defining task format and status semantics"
      }
    },
    "required": ["type", "active_tasks_file", "task_format_schema"]
  }
}
```

**Migration Note**: Sense command must detect if multiple workflows exist and prompt user to choose one.

---

### Part 2: New Simple Stop Hook

**File**: `resources/workflows/feature-implementation-v2/hooks/stop_qa_check.py`

**Purpose**: Simple hook that ONLY checks QA status of active tasks

#### Hook Logic Flow

```python
1. Load .synapse/config.json

2. Extract configuration:
   - workflow = config.third_party_workflow (single object, not array)
   - active_tasks = workflow.get("active_tasks", [])
   - task_file = workflow.active_tasks_file
   - schema = workflow.task_format_schema

3. Edge case handling:
   IF active_tasks is empty or missing:
     → Exit 2 with directive: "No active tasks set. Update third_party_workflow.active_tasks in config.json"

   IF task_file doesn't exist:
     → Exit 2 with directive: "Task file '{task_file}' not found. Cannot verify active tasks."

4. For each task in active_tasks:
   a. Parse task file using schema.patterns
   b. Find task by code (e.g., "T001")

   IF task not found in file:
     → Exit 2 with directive: "Task {code} in active_tasks not found in {task_file}.
        Either add task to file or remove from active_tasks."

   c. Find QA Status field using schema.status_semantics.field_mapping["qa"]

   IF QA Status field missing:
     → Mark task as needing verification (Exit 2 path)
     → Include warning in directive: "Task {code} missing QA Status field"

   d. Extract QA Status value
   e. Determine verification status:
      - IF value in schema.status_semantics.states.qa.not_verified:
          → Task needs verification (Exit 2 path)
      - IF value in schema.status_semantics.states.qa.verified_success:
          → Task is verified (Exit 0 path)
      - IF value matches schema.status_semantics.states.qa.verified_failure_pattern:
          → Task is verified as failed (Exit 0 path)
      - ELSE:
          → Unknown status, treat as needs verification (Exit 2 path)

5. Results:
   IF ALL tasks have verified QA Status (success OR failure):
     → Exit 0 (success, allow stop - all tasks verified)

   ELSE (at least one task needs verification):
     → Exit 2 with full verification directive (only list unverified tasks)
```

#### Exit 2 Directive Format

```markdown
## QA Verification Required

### Active Tasks Needing Verification
{FOR EACH task where QA not verified}
- {task_code}: {task_description}
{END FOR}

### Quality Commands (from config.json)
{IF quality-config.mode == "single"}
- lint: {quality-config.commands.lint}
- test: {quality-config.commands.test}
- typecheck: {quality-config.commands.typecheck}
- coverage: {quality-config.commands.coverage}
- build: {quality-config.commands.build}
{ELSE IF quality-config.mode == "monorepo"}
{FOR EACH project in quality-config.projects}
**{project_name}:**
- lint: {project.commands.lint}
- test: {project.commands.test}
- typecheck: {project.commands.typecheck}
- coverage: {project.commands.coverage}
- build: {project.commands.build}
{END FOR}
{END IF}

### Verification Process

Follow these steps to verify the active tasks:

1. **Run Quality Checks**
   - Execute all quality commands listed above
   - Capture results for each check (lint, test, typecheck, coverage, build)
   - Note any failures or warnings

2. **Review Implementation**
   - For each task, review the code changes made
   - Verify the implementation matches task requirements
   - Check for edge cases and error handling
   - Ensure code quality standards are met

3. **Test Functionality**
   - Test the implemented features manually
   - If this is a web application, use the playwright MCP to test UI/UX
   - Verify all acceptance criteria are satisfied
   - Test error conditions and boundary cases

4. **Update Task Status**
   - For tasks that PASS all checks: Update QA Status to [Complete] or [Passed]
   - For tasks that FAIL: Leave QA Status unchanged

5. **Handle Failures**
   - If ANY task has failures, document them clearly
   - Create a detailed fix plan
   - Present the plan to the user with the question:
     **"Would you like me to proceed with the plan to fix the found issues?"**
   - Wait for user approval before attempting fixes
   - DO NOT proceed with fixes without explicit user approval

6. **Present Completion Report**
   - If ALL tasks pass verification, generate and present the completion report
   - Use the format template below

### Completion Report Format

When all tasks pass verification, present a report following this structure:

```markdown
## ✅ QA Verification Complete - All Tasks Passed

### Tasks Verified
- T001: {task_description} - PASSED
- T002: {task_description} - PASSED

### Quality Metrics
- Lint: ✅ {status/issue count}
- Tests: ✅ {passed}/{total} passed
- Type Check: ✅ {status}
- Coverage: ✅ {percentage}% (threshold: {threshold}%)
- Build: ✅ {status}

### Implementation Summary
{Brief narrative description of what was implemented, key changes made,
 and how the implementation meets the requirements. Include any notable
 technical decisions or approaches used.}
```

**Note:** This is a template. Adapt the actual report based on what was verified
and include relevant details from your verification process.
```

#### Implementation Details

**Key Features:**
- **Timeout**: 60 seconds maximum (prevent hanging)
- **Early logging**: Print startup message immediately for debugging
- **Defensive parsing**: Handle malformed tasks gracefully
- **Schema-driven**: All patterns and values come from task_format_schema

**Dependencies:**
- Python 3.8+
- Standard library only (json, sys, os, re, pathlib)
- No external packages required

---

### Part 3: Hook Integration

**File**: `resources/workflows/feature-implementation-v2/settings.json`

Add UserPromptSubmit hook and Stop hook:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/user-prompt-reminder.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run .claude/hooks/stop_qa_check.py"
          }
        ]
      }
    ]
  }
}
```

**Note**: Remove or archive `stop_validation.py` (the complex version)

---

### Part 4: UserPromptSubmit Hook

**File**: `resources/workflows/feature-implementation-v2/hooks/user-prompt-reminder.sh`

**Purpose**: Remind agent of active_tasks management requirements on every user message

```bash
#!/bin/bash
# UserPromptSubmit Hook - Active Tasks Management Reminder
# Reminds agent of mandatory workflow requirements on every user prompt

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "ACTIVE TASKS MANAGEMENT RULES (third_party_workflow.active_tasks)"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "1. STARTING WORK:"
echo "   - SET active_tasks to task codes you're working on (e.g., [\"T001\", \"T002\"])"
echo "   - Example: active_tasks: [\"T001\", \"T002\", \"T003\"]"
echo ""
echo "2. DURING VERIFICATION:"
echo "   - Run ALL quality checks for each active task"
echo "   - Mark QA Status based on results:"
echo "     • [Passed] - All checks passed"
echo "     • [Failed - {reason}] - Include specific failure details"
echo "   - NEVER mark as [Passed] without actually running checks"
echo ""
echo "3. AFTER VERIFICATION WITH FAILURES:"
echo "   - Present results to user with pass/fail breakdown"
echo "   - ASK: 'Would you like me to fix the failed tasks?'"
echo "   - If user says NO:"
echo "     → REMOVE passed tasks from active_tasks"
echo "     → KEEP failed tasks in active_tasks"
echo "     → Stop (hook allows stop with [Failed] status)"
echo "   - If user says YES:"
echo "     → KEEP failed tasks in active_tasks"
echo "     → Fix issues"
echo "     → SET QA Status back to [Not Started] (needs re-verification)"
echo "     → Re-run verification"
echo ""
echo "4. AFTER ALL TASKS PASS:"
echo "   - Generate completion report"
echo "   - CLEAR active_tasks to [] (empty array)"
echo "   - Stop (hook allows stop)"
echo ""
echo "5. CONTINUING WORK ON FAILED TASKS:"
echo "   - If you see active_tasks with [Failed] status:"
echo "     → User wants these fixed"
echo "     → Fix the issues"
echo "     → SET QA Status to [Not Started]"
echo "     → Verify again"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "QA STATUS VALUES:"
echo "═══════════════════════════════════════════════════════════════"
echo "  [Not Started]          - Not verified (hook BLOCKS stop)"
echo "  [Passed] or [Complete] - Verified successfully (hook allows stop)"
echo "  [Failed - {reason}]    - Verified with failures (hook allows stop)"
echo ""
echo "═══════════════════════════════════════════════════════════════"
```

---

### Part 5: Agent Behavior

The main agent in feature-implementation-v2 workflow responds to hook exit codes:

#### Exit 0: Success
```
Agent receives: Exit code 0
Agent action: Stop successfully, work is complete
```

#### Exit 2: Verification Required
```
Agent receives: Exit code 2 + verification directive

Agent performs verification:
  1. Run quality commands from directive
  2. Review implementations against task requirements
  3. Test functionality (use playwright MCP if web app)
  4. Collect results for all checks

  FOR EACH task in verification:
    IF task passes all checks:
      → Mark: QA Status = [Passed]
    ELSE:
      → Mark: QA Status = [Failed - {specific failure details}]
      → Include: which checks failed, error messages, line numbers, etc.

  5. Attempt to stop (hook will allow - all tasks now verified)

  IF any failures found:
    - Present results with pass/fail breakdown
    - Show detailed failure information for each failed task
    - ASK: "Would you like me to fix the failed tasks?"
    - Wait for user response

    IF user approves fixing:
      → Keep failed tasks in active_tasks
      → Remove passed tasks from active_tasks
      → Fix the issues
      → Set fixed tasks QA Status back to [Not Started]
      → Attempt to stop (hook blocks - unverified tasks exist)
      → Re-run verification (loop back to step 1)

    IF user denies fixing:
      → Remove passed tasks from active_tasks
      → Keep failed tasks in active_tasks (signals pending work)
      → Stop (hook allows - failed tasks are verified as failed)

  ELSE (all checks pass):
    - Mark all verified tasks: QA Status = [Passed]
    - Generate completion report using template from directive
    - Present report to user
    - Clear active_tasks: Set third_party_workflow.active_tasks = []
    - Attempt to stop (should now exit 0 - no active tasks)

Note: Directive only lists tasks with QA Status = [Not Started] or missing.
      Tasks with [Passed], [Complete], or [Failed] are already verified.
```

---

### Part 6: Active Tasks Management

#### When Agent Starts Work

Agent must update `config.json` when beginning work on tasks:

```json
{
  "third_party_workflow": {
    "type": "openspec",
    "active_tasks_file": "tasks.md",
    "active_tasks": ["T001", "T002"],
    "task_format_schema": {...}
  }
}
```

**Trigger points:**
- User assigns tasks to agent
- Agent starts implementing a feature
- Beginning of work session

**Workflow integration:**
- UserPromptSubmit hook reminds agent on every user message
- Optional: Consider adding a write hook on tasks.md to auto-detect from Dev Status

#### When Agent Completes Work

After all tasks are verified and QA Status marked complete, agent should clear active tasks:

```json
{
  "third_party_workflow": {
    "type": "openspec",
    "active_tasks_file": "tasks.md",
    "active_tasks": [],
    "task_format_schema": {...}
  }
}
```

This ensures:
- Next stop attempt will exit 0 (no active tasks to verify)
- Clean state for next work session
- No stale task references

---

## Adoption Path (Not a Migration)

**This is a new implementation in parallel with the existing one.**

### For New Users

1. Install Synapse CLI
2. Run `/synapse:sense` in your project
3. Select new Option 6 workflow
4. Start working with `active_tasks` approach

### For Existing Users

**Option A: Continue with legacy workflows**
- No changes required
- Workflows reference `legacy/resources/`
- Stable, existing behavior

**Option B: Adopt new Option 6 workflows**
1. Complete any in-progress work with old workflows
2. Run updated `/synapse:sense` to generate new config
   - New config uses `third_party_workflow` (object, not array)
   - If multiple workflows detected, choose one
3. Update tasks.md to use task code format (T001, T002, etc.)
4. Start using new `resources/` workflows
5. Enjoy simplified, more reliable QA verification

### Breaking Changes (New Workflows Only)

These ONLY apply if adopting new workflows:
- Config structure: `third_party_workflow` (object) replaces `third_party_workflows.detected` (array)
- Requires `active_tasks` field in config
- Task format requires task codes (T001, T002, etc.)
- QA Status has three categories: [Not Started], [Passed], [Failed - reason]
- Only one workflow per project
- UserPromptSubmit hook provides continuous guidance

### No Forced Migration

- **Legacy workflows continue to work**
- Users opt-in when ready
- Both systems can coexist during transition
- Can test new approach in a separate project first

---

## Benefits of This Approach

### Simplicity
- Hook is <200 lines of code (vs 1000+ lines)
- Single responsibility: Check QA status only
- No quality check execution in hook
- No subprocess management in hook
- No timeout complexity in hook

### Reliability
- Fewer moving parts = fewer failure points
- No file system traversal (no hanging)
- No external command execution (no timeout issues)
- Schema-driven parsing (flexible format support)

### Maintainability
- Easy to understand logic
- Clear separation of concerns
- Simple to debug (just check config + parse tasks)
- Easy to extend (add more status fields if needed)

### Agent Empowerment
- Agent uses all available tools (playwright, grep, read, etc.)
- Agent can provide context-aware verification
- Agent can explain what it's checking and why
- Agent generates better reports with context

### User Experience
- Clear progress indication (partial task verification)
- Explicit approval for fixes
- Comprehensive completion reports
- Better error messages and guidance

---

## Future Enhancements (Optional)

### Automatic Active Tasks Detection
Add a write hook on `tasks.md` that:
- Detects tasks with `Dev Status: [In Progress]`
- Auto-updates `third_party_workflow.active_tasks` in config
- Provides safety net if agent forgets to set active tasks

### Task History Tracking
Track verification history within workflow:
```json
{
  "third_party_workflow": {
    "type": "openspec",
    "active_tasks": ["T001", "T002"],
    "verification_history": [
      {
        "timestamp": "2025-01-15T10:30:00Z",
        "tasks": ["T001", "T002"],
        "result": "success",
        "metrics": {...}
      }
    ]
  }
}
```

### Integration with CI/CD
Hook could check CI/CD pipeline status:
- Wait for GitHub Actions to complete
- Verify deployment succeeded
- Check production metrics

---

## Testing Strategy

### Unit Tests for Hook

Test cases for `stop_qa_check.py`:

1. **Empty active_tasks** → Exit 2
2. **Task file missing** → Exit 1
3. **Task not found in file** → Exit 1
4. **Task missing QA Status** → Exit 2
5. **All tasks verified** → Exit 0
6. **Some tasks not verified** → Exit 2
7. **Malformed task file** → Graceful error handling
8. **Invalid schema** → Exit 1 with clear error

### Integration Tests

Test full workflow:

1. Agent starts work → Sets active_tasks
2. Agent attempts stop → Hook blocks (Exit 2)
3. Agent runs verification → Finds failures
4. Agent asks user → User approves fixes
5. Agent fixes and re-verifies → All pass
6. Agent marks QA Status → Updates tasks.md
7. Agent clears active_tasks → Updates config
8. Agent attempts stop → Hook allows (Exit 0)

### Edge Case Tests

1. Multiple tasks, partial verification
2. Monorepo with multiple projects
3. Task format variations (old vs new)
4. Schema without certain fields
5. Concurrent edits to tasks.md
6. Very large task files (100+ tasks)

---

## Implementation Tasks

This section provides an incremental task list for implementing the simplified stop hook approach.

**NOTE**: This is a fresh implementation, not a migration. Existing resources/ will be moved to legacy/resources/.

### Tasks

[x] - T000 - Directory restructuring
  [x] - T000-ST001 - Create legacy/ directory
  [x] - T000-ST002 - Move resources/ to legacy/resources/
  [x] - T000-ST003 - Create new resources/schemas/ directory
  [x] - T000-ST004 - Create new resources/workflows/feature-implementation-v2/ structure
  [x] - T000-ST005 - Create new resources/workflows/feature-planning/ structure
  [x] - T000-ST006 - Verify git tracking for new directories
  [ ] - T000-DS - Dev Status: [Complete]
  [ ] - T000-QA - QA Status: [Passed]
  [ ] - T000-UV - User Verification Status: [Not Started]

  *Quality Standards: Maintain lint, typecheck, test, coverage, and successful build throughout implementation*

[x] - T001 - Create new schema from scratch
  [x] - T001-ST001 - Create resources/schemas/synapse-config-schema.json with third_party_workflow (object, not array)
  [x] - T001-ST002 - Define third_party_workflow structure with active_tasks field
  [x] - T001-ST003 - Define task_format_schema with task code patterns (T001, T002, etc.)
  [x] - T001-ST004 - Add Dev Status and QA Status fields to status_semantics
  [x] - T001-ST005 - Add QA Status three-category semantics (not_verified, verified_success, verified_failure_pattern)
  [x] - T001-ST006 - Validate schema with JSON schema validator
  [ ] - T001-DS - Dev Status: [Complete]
  [ ] - T001-QA - QA Status: [Passed]
  [ ] - T001-UV - User Verification Status: [Not Started]

  *Quality Standards: Maintain lint, typecheck, test, coverage, and successful build throughout implementation*

[x] - T002 - Create stop_qa_check.py hook
  [x] - T002-ST001 - Implement config loading and workflow extraction
  [x] - T002-ST002 - Implement task file parsing using schema patterns
  [x] - T002-ST003 - Implement QA status checking logic
  [x] - T002-ST004 - Implement exit code 0 logic (all verified)
  [x] - T002-ST005 - Implement exit code 1 logic (warnings/errors)
  [x] - T002-ST006 - Implement exit code 2 logic (verification required)
  [x] - T002-ST007 - Generate comprehensive verification directive for exit 2
  [x] - T002-ST008 - Add timeout protection (60 seconds max)
  [x] - T002-ST009 - Add early logging for debugging
  [x] - T002-ST010 - Add defensive error handling
  [ ] - T002-DS - Dev Status: [Complete]
  [ ] - T002-QA - QA Status: [Passed]
  [ ] - T002-UV - User Verification Status: [Not Started]

  *Quality Standards: Maintain lint, typecheck, test, coverage, and successful build throughout implementation*

[x] - T003 - Create user-prompt-reminder.sh hook
  [x] - T003-ST001 - Create hooks/user-prompt-reminder.sh in feature-implementation-v2
  [x] - T003-ST002 - Add active_tasks management reminders
  [x] - T003-ST003 - Add verification requirements reminders
  [x] - T003-ST004 - Make script executable (chmod +x)
  [ ] - T003-DS - Dev Status: [Complete]
  [ ] - T003-QA - QA Status: [Passed]
  [ ] - T003-UV - User Verification Status: [Not Started]

  *Quality Standards: Maintain lint, typecheck, test, coverage, and successful build throughout implementation*

[x] - T004 - Update workflow settings.json
  [x] - T004-ST001 - Add UserPromptSubmit hook to feature-implementation-v2/settings.json
  [x] - T004-ST002 - Update Stop hook path to hooks/stop_qa_check.py
  [x] - T004-ST003 - Verify hook paths use relative paths
  [x] - T004-ST004 - Test hook execution
  [ ] - T004-DS - Dev Status: [Complete]
  [ ] - T004-QA - QA Status: [Passed]
  [ ] - T004-UV - User Verification Status: [Not Started]

  *Quality Standards: Maintain lint, typecheck, test, coverage, and successful build throughout implementation*

[x] - T005 - Create unit tests for stop_qa_check.py
  [x] - T005-ST001 - Test empty active_tasks returns exit 2
  [x] - T005-ST002 - Test task file missing returns exit 2
  [x] - T005-ST003 - Test task not found in file returns exit 2
  [x] - T005-ST004 - Test task missing QA Status returns exit 2 with warning
  [x] - T005-ST005 - Test all tasks verified returns exit 0
  [x] - T005-ST006 - Test some tasks not verified returns exit 2
  [x] - T005-ST007 - Test malformed task file graceful handling
  [x] - T005-ST008 - Test invalid schema graceful handling
  [x] - T005-ST009 - Verify exit 2 directive contains all required sections
  [x] - T005-ST010 - Test partial verification (some tasks already verified)
  [ ] - T005-DS - Dev Status: [Complete]
  [ ] - T005-QA - QA Status: [Passed]
  [ ] - T005-UV - User Verification Status: [Not Started]

  *Quality Standards: Maintain lint, typecheck, test, coverage, and successful build throughout implementation*

[x] - T006 - Create integration test with sample project
  [x] - T006-ST001 - Create test project with config.json (new structure)
  [x] - T006-ST002 - Create sample tasks.md with task codes
  [x] - T006-ST003 - Test hook with no active tasks (expect exit 0)
  [x] - T006-ST004 - Set active_tasks and test unverified tasks (expect exit 2)
  [x] - T006-ST005 - Mark tasks as QA Complete and test (expect exit 0)
  [x] - T006-ST006 - Test partial verification (mixed results)
  [x] - T006-ST007 - Test all edge cases (missing files, invalid codes, etc.)
  [ ] - T006-DS - Dev Status: [Complete]
  [ ] - T006-QA - QA Status: [Passed]
  [ ] - T006-UV - User Verification Status: [Not Started]

  *Quality Standards: Maintain lint, typecheck, test, coverage, and successful build throughout implementation*

[x] - T007 - Update feature-planning workflow to use new task format
  [x] - T007-ST001 - Copy writer.md agent to new resources/workflows/feature-planning
  [x] - T007-ST002 - Copy and update writer-post-tool-use.py hook for Option 6 QA statuses
  [x] - T007-ST003 - Copy settings.json and user-prompt-reminder.sh
  [x] - T007-ST004 - Make hooks executable
  [ ] - T007-DS - Dev Status: [Complete]
  [ ] - T007-QA - QA Status: [Passed]
  [ ] - T007-UV - User Verification Status: [Not Started]

  *Quality Standards: Maintain lint, typecheck, test, coverage, and successful build throughout implementation*

[x] - T008 - Update sense command for new config structure
  [x] - T008-ST001 - Update sense command to generate third_party_workflow (object) instead of array
  [x] - T008-ST002 - Add detection for multiple workflows with user prompt to choose one
  [x] - T008-ST003 - Ensure active_tasks field is included in generated config
  [x] - T008-ST004 - Include complete task_format_schema with Option 6 patterns
  [ ] - T008-DS - Dev Status: [Complete]
  [ ] - T008-QA - QA Status: [Passed]
  [ ] - T008-UV - User Verification Status: [Not Started]

  *Quality Standards: Maintain lint, typecheck, test, coverage, and successful build throughout implementation*

[ ] - T009 - Verify legacy workflows still functional
  [ ] - T009-ST001 - Test legacy/resources/workflows/feature-implementation still works
  [ ] - T009-ST002 - Test legacy/resources/workflows/feature-planning still works
  [ ] - T009-ST003 - Add README.md to legacy/ explaining preservation
  [ ] - T009-ST004 - Document that legacy workflows are stable and supported
  [ ] - T009-DS - Dev Status: [Not Started]
  [ ] - T009-QA - QA Status: [Not Started]
  [ ] - T009-UV - User Verification Status: [Not Started]

  *Quality Standards: Maintain lint, typecheck, test, coverage, and successful build throughout implementation*

[x] - T010 - Update documentation
  [x] - T010-ST001 - Create feature-implementation-v2 README with comprehensive workflow docs
  [x] - T010-ST002 - Create feature-planning README with validation details
  [x] - T010-ST003 - Create migration guide for legacy users
  [x] - T010-ST004 - Create legacy README explaining preservation
  [x] - T010-ST005 - Create resources README with quick start
  [x] - T010-ST006 - Document all workflows, exit codes, and examples
  [ ] - T010-DS - Dev Status: [Complete]
  [ ] - T010-QA - QA Status: [Passed]
  [ ] - T010-UV - User Verification Status: [Not Started]

  *Quality Standards: Maintain lint, typecheck, test, coverage, and successful build throughout implementation*

### Dependencies
- T000 is independent (first step - directory restructuring)
- T001 depends on T000 (need new resources/ structure before creating schema)
- T002 depends on T001 (hook needs schema to parse config)
- T003 is independent (can be done in parallel with T002, but needs T000)
- T004 depends on T002, T003 (settings needs both hooks created)
- T005 depends on T002 (tests require hook implementation)
- T006 depends on T002, T004 (integration tests need hook + settings)
- T007 depends on T000 (feature-planning workflow in new resources/)
- T008 depends on T001 (sense command needs new schema)
- T009 depends on T006 (verify new hook works, old hooks stay in legacy/)
- T010 depends on all others (document after implementation complete)

### Notes
- Tasks can be worked on in parallel where dependencies allow
- Each task includes Dev Status, QA Status, and User Verification Status
- Quality standards must be maintained throughout (lint, typecheck, test, coverage, build)
- Stop hook should be tested incrementally as it's built

---

## Design Decisions Summary

This section documents all finalized design decisions:

### 1. Exit Code Strategy (Q1)
**Decision**: Exit 2 (block) for missing task files when active_tasks is set
- Task file must exist if there are active tasks to verify
- More robust than allowing stop with warning

### 2. Agent Prompt Integration (Q2)
**Decision**: UserPromptSubmit hook + optional write hook as safety net
- Hook runs on every user message
- Reminds agent to manage active_tasks
- Pattern borrowed from feature-implementation workflow

### 3. State Recovery and Failure Handling (Q3) - Option 6
**Decision**: Failed tasks treated as verified (allows stop)

- **Three QA Status categories:**
  - `[Not Started]` - Not verified → Hook blocks (Exit 2)
  - `[Passed]` or `[Complete]` - Verified success → Hook allows stop (Exit 0)
  - `[Failed - {reason}]` - Verified failure → Hook allows stop (Exit 0)

- **Agent workflow with failures:**
  - Verify all tasks, mark each as [Passed] or [Failed - reason]
  - Hook allows stop (all verified)
  - Agent asks user: "Would you like me to fix the failed tasks?"
  - If NO: Remove passed tasks from active_tasks, keep failed tasks, stop
  - If YES: Fix issues, set QA Status to [Not Started], re-verify

- **Benefits:**
  - Enforces verification (can't skip)
  - User has control over fixes
  - Failed tasks stay tracked in active_tasks
  - Natural workflow for continuing work later

### 4. Multi-Workflow Support (Q4)
**Decision**: Single workflow only (breaking change)
- Changed from `third_party_workflows.detected` (array) to `third_party_workflow` (object)
- Sense command detects multiple workflows and asks user to choose one
- Simpler, cleaner design

### 5. Task Code Not Found (Q5)
**Decision**: Exit 2 (block) with specific directive
- If task code in active_tasks isn't found in file, block stop
- Directive tells agent to either add task to file or remove from active_tasks
- Ensures consistency between config and task file

### 6. Missing QA Status Field (Q6)
**Decision**: Exit 2 with warning in directive
- Block verification but call out the missing field explicitly
- Agent knows to add QA Status field to task
- Better error messaging

### 7. Auto-Clearing active_tasks (Q7)
**Decision**: Manual clearing with reminder in UserPromptSubmit hook
- Keep it explicit and in agent control
- Hook reminds agent on every message
- More predictable than automatic clearing

---

## Summary

This simplified approach provides:
- ✅ Clear separation between hook (check) and agent (verify)
- ✅ Simple, maintainable hook code (~200 lines vs 1000+)
- ✅ Reliable exit code strategy (only Exit 0 and Exit 2)
- ✅ Schema-driven flexibility
- ✅ Agent empowerment with full tool access
- ✅ Better user experience with explicit approval
- ✅ Comprehensive reporting
- ✅ Single workflow per project (cleaner config)
- ✅ UserPromptSubmit hook for agent guidance

The key insight: **The hook should be dumb, the agent should be smart.**

---

## Option 6 Walkthrough Example

This example demonstrates the complete workflow with failure handling and active_tasks management.

### Scenario: Agent working on three tasks (T001, T002, T003)

**Initial state:**
```json
{
  "third_party_workflow": {
    "active_tasks": ["T001", "T002", "T003"]
  }
}
```

Tasks in tasks.md:
```markdown
[ ] - T001 - Add user authentication
  [ ] - T001-QA - QA Status: [Not Started]

[ ] - T002 - Implement dashboard
  [ ] - T002-QA - QA Status: [Not Started]

[ ] - T003 - Add error handling
  [ ] - T003-QA - QA Status: [Not Started]
```

---

### Step 1: Agent tries to stop

**Hook checks:**
- active_tasks = ["T001", "T002", "T003"]
- All three have QA Status = [Not Started]
- **Exit 2** - Must verify tasks

**Agent receives:** Verification directive listing T001, T002, T003

---

### Step 2: Agent runs verification

Agent runs quality checks for all three tasks:
- T001: ✅ All checks pass
- T002: ❌ Lint errors on lines 45, 67
- T003: ✅ All checks pass

Agent updates tasks.md:
```markdown
[ ] - T001 - Add user authentication
  [ ] - T001-QA - QA Status: [Passed]

[ ] - T002 - Implement dashboard
  [ ] - T002-QA - QA Status: [Failed - lint errors: unused variable line 45, missing semicolon line 67]

[ ] - T003 - Add error handling
  [ ] - T003-QA - QA Status: [Passed]
```

---

### Step 3: Agent tries to stop again

**Hook checks:**
- active_tasks = ["T001", "T002", "T003"]
- T001: [Passed] ✅ verified
- T002: [Failed - ...] ✅ verified (as failed)
- T003: [Passed] ✅ verified
- **Exit 0** - All verified, allow stop

---

### Step 4: Agent presents results and asks user

```
## QA Verification Results

✅ T001 - Add user authentication - PASSED
❌ T002 - Implement dashboard - FAILED
   - Lint error: Unused variable 'data' on line 45
   - Lint error: Missing semicolon on line 67
✅ T003 - Add error handling - PASSED

Would you like me to fix the failed tasks?
```

---

### Step 5a: User says "No"

Agent updates config.json (removes passed tasks, keeps failed):
```json
{
  "third_party_workflow": {
    "active_tasks": ["T002"]
  }
}
```

Agent stops successfully.

**Next session:**
User: "Please continue with the remaining work"

Agent sees:
- active_tasks = ["T002"]
- T002 has QA Status: [Failed - ...]
- Agent understands T002 needs fixing
- Agent fixes the lint errors
- Agent updates: QA Status: [Not Started] (needs re-verification)
- Agent tries to stop → Hook blocks (T002 not verified)
- Agent runs verification → T002 passes
- Agent updates: QA Status: [Passed]
- Agent clears: active_tasks = []
- Agent stops → Hook allows (no active tasks)

---

### Step 5b: User says "Yes"

Agent updates config.json (removes only passed tasks):
```json
{
  "third_party_workflow": {
    "active_tasks": ["T002"]
  }
}
```

Agent fixes lint errors in T002.

Agent updates tasks.md:
```markdown
[ ] - T002 - Implement dashboard
  [ ] - T002-QA - QA Status: [Not Started]
```

Agent tries to stop:
- **Hook blocks (Exit 2)** - T002 has QA Status: [Not Started]

Agent re-runs verification:
- T002: ✅ All checks pass

Agent updates tasks.md:
```markdown
[ ] - T002 - Implement dashboard
  [ ] - T002-QA - QA Status: [Passed]
```

Agent tries to stop:
- **Hook allows (Exit 0)** - T002 verified as passed

Agent presents completion report:
```
## ✅ QA Verification Complete - All Tasks Passed

### Tasks Verified
- T001: Add user authentication - PASSED
- T002: Implement dashboard - PASSED (fixed and re-verified)
- T003: Add error handling - PASSED

### Quality Metrics
- Lint: ✅ 0 errors
- Tests: ✅ 45/45 passed
- Type Check: ✅ No errors
- Coverage: ✅ 87% (threshold: 80%)
- Build: ✅ Success
```

Agent clears active_tasks:
```json
{
  "third_party_workflow": {
    "active_tasks": []
  }
}
```

Agent stops successfully → Hook allows (Exit 0, no active tasks).

---

### Key Observations

1. **Hook enforces verification** - Can't stop with [Not Started] tasks
2. **Hook allows informed decisions** - Can stop with [Failed] tasks
3. **User has control** - Can choose to fix now or later
4. **active_tasks tracks pending work** - Failed tasks stay until resolved
5. **Re-verification is automatic** - Fixing triggers [Not Started] → blocks stop
6. **Clean completion** - All passed → clear active_tasks → stop

This is the **Option 6 workflow** in action.

---

## Final Summary

### What We're Building

A **fresh implementation** of QA verification with:
- **Directory**: New `resources/` (old moved to `legacy/resources/`)
- **Config**: `third_party_workflow` object (single workflow per project)
- **Hook**: Simple stop_qa_check.py (~200 lines)
- **Status**: Three-category QA Status ([Not Started], [Passed], [Failed - reason])
- **Control**: UserPromptSubmit hook guides agent through active_tasks management
- **User Power**: Can stop with failures and decide later whether to fix

### Why Fresh Start?

- ✅ No migration complexity
- ✅ Legacy workflows preserved and functional
- ✅ Clean slate for Option 6 architecture
- ✅ Users opt-in when ready
- ✅ Both systems coexist during transition

### Next Steps

1. **T000**: Restructure directories (resources → legacy/resources, create new resources/)
2. **T001**: Create new schema with third_party_workflow structure
3. **T002**: Build simple stop_qa_check.py hook
4. **T003**: Create comprehensive UserPromptSubmit reminder hook
5. **T004-T010**: Complete implementation with tests, integration, and docs

### The Core Innovation

**Option 6 solves the blocking problem:**
- Old approach: Can't stop until everything passes (user stuck)
- Option 6: Can stop after verification, user chooses when to fix (user control)

**The secret:** Treat `[Failed - reason]` as a **verified state**, not unverified.

---

**Document Status**: Complete design specification for Option 6 implementation
**Ready for**: Implementation starting with T000 (directory restructuring)
