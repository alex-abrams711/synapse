# Synapse User Guide

This guide explains how to use Synapse's QA verification system for Claude Code projects.

---

## Overview

Synapse implements a two-stage architecture for QA verification:

1. **Hook (Simple)**: Checks if QA verification has been done for active tasks
2. **Agent (Smart)**: Performs the actual verification using all available tools

**Key Feature:** The hook enforces verification (blocks if QA Status = [Not Started]) but allows you to stop with failures (allows if QA Status = [Failed - reason]). This gives you full control over when to fix vs. defer issues.

---

## Core Philosophy

**"The hook should be dumb, the agent should be smart."**

**Hooks are limited:**
- Restricted execution environment
- No conversation context
- Prone to timeouts
- Can't ask questions

**Agents are powerful:**
- Full tool access (bash, grep, read, playwright, etc.)
- Complete conversation context
- Can ask clarifying questions
- Can provide detailed reports

**Solution:**
- Hook: Simple status checker (~400 lines) - only reads config and checks QA Status
- Agent: Smart verifier - runs all quality checks, analyzes results, updates status

---

## Three-Category QA Status System

```
[Not Started]        → NOT VERIFIED   → Hook blocks (Exit 2)
[Passed]/[Complete]  → VERIFIED SUCCESS → Hook allows (Exit 1)
[Failed - {reason}]  → VERIFIED FAILURE → Hook allows (Exit 1)
```

**The Innovation:** Failed tasks are treated as **verified**. The task has been checked; it just didn't pass. Failed tasks stay tracked in `active_tasks` until you decide to fix them. This means you can stop working after verification, even if some tests failed.

**Why this matters:** You control when to fix issues. No more being stuck in a fix loop - verify everything, then decide what to address now vs. later.

---

## Configuration

Your `.synapse/config.json` contains the workflow configuration:

```json
{
  "third_party_workflow": {
    "type": "openspec",
    "active_tasks_file": "tasks.md",
    "active_tasks": ["T001", "T002"],
    "task_format_schema": {
      "version": "2.0",
      "patterns": {...},
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
  }
}
```

**Key Fields:**
- `type`: Workflow system (openspec, spec-kit, custom)
- `active_tasks_file`: Path to your tasks file
- `active_tasks`: Array of task codes being worked on (e.g., ["T001", "T002"])
- `task_format_schema`: Schema defining how to parse your tasks

---

## Exit Codes

| Exit Code | Meaning | Use Case |
|-----------|---------|----------|
| **0** | ✅ Success | All active tasks verified OR no active tasks |
| **1** | ⚠️ Warning | Show message to user (allow stop) |
| **2** | ❌ Block | Verification required, cannot stop |

**When hooks block (Exit 2):**
- No active tasks set when needed
- Task file doesn't exist
- Active task code not found in task file
- Task missing QA Status field
- Any active task has QA Status = [Not Started]

**When hooks allow (Exit 0 or 1):**
- All tasks in `active_tasks` have verified QA Status (passed OR failed)
- OR `active_tasks` is empty

---

## Active Tasks Management

**Agent Responsibilities:**
1. **Starting work:** Set `active_tasks: ["T001", "T002"]` in config
2. **During work:** Keep active_tasks up-to-date
3. **After verification:** Update QA Status based on results
4. **Completing work:** Clear `active_tasks: []`

**Hook Responsibilities:**
1. Check QA Status for each active task
2. Block if any task is `[Not Started]`
3. Allow if all tasks are verified (even failures)

**UserPromptSubmit Hook:**
- Runs on every user message
- Reminds agent of active_tasks management requirements
- Shows workflow for handling failures
- Explains QA Status values

---

## Workflow: All Tasks Pass

```
1. User: "Implement feature X"
2. Agent: Sets active_tasks: ["T001", "T002"]
3. Agent: Implements the feature
4. Agent: Tries to stop → Hook blocks (Exit 2)
5. Agent: Receives directive with verification instructions
6. Agent: Runs all quality checks (lint, test, typecheck, coverage, build)
7. Agent: All checks pass
8. Agent: Updates QA Status: [Passed] for both tasks
9. Agent: Tries to stop → Hook allows (Exit 1)
10. Agent: Presents completion report to user
11. Agent: Clears active_tasks: []
12. Agent: Stops successfully
```

---

## Workflow: Some Tasks Fail

```
1. Agent: Sets active_tasks: ["T001", "T002", "T003"]
2. Agent: Implements all three tasks
3. Agent: Tries to stop → Hook blocks (Exit 2)
4. Agent: Runs verification:
   - T001: ✅ All checks pass
   - T002: ❌ Lint errors on lines 45, 67
   - T003: ✅ All checks pass
5. Agent: Updates tasks:
   - T001: QA Status: [Passed]
   - T002: QA Status: [Failed - lint: unused variable line 45, missing semicolon line 67]
   - T003: QA Status: [Passed]
6. Agent: Tries to stop → Hook allows (Exit 1, all verified)
7. Agent: Shows results to user:
   ✅ T001 - PASSED
   ❌ T002 - FAILED (lint errors)
   ✅ T003 - PASSED
8. Agent: Asks "Would you like me to fix the failed tasks?"

IF USER SAYS NO:
9. Agent: Removes passed tasks from active_tasks: ["T002"]
10. Agent: Stops (T002 remains tracked for later)

IF USER SAYS YES:
9. Agent: Keeps failed task: active_tasks: ["T002"]
10. Agent: Fixes lint errors
11. Agent: Sets QA Status: [Not Started] (needs re-verification)
12. Agent: Tries to stop → Hook blocks (Exit 2)
13. Agent: Re-runs verification → T002 passes
14. Agent: Updates QA Status: [Passed]
15. Agent: Clears active_tasks: []
16. Agent: Stops successfully
```

---

## Continuing Work on Failed Tasks

**Next session after leaving T002 failed:**

```
User: "Please continue with the remaining work"

Agent observes:
- active_tasks: ["T002"]
- T002 has QA Status: [Failed - lint errors...]

Agent understands T002 needs fixing

Agent fixes the issues
Agent sets QA Status: [Not Started] (needs re-verification)
Agent tries to stop → Hook blocks (Exit 2)
Agent verifies T002 → Passes
Agent updates QA Status: [Passed]
Agent clears active_tasks: []
Agent stops successfully
```

---

## Multi-Layer Protection System

The system includes four complementary hooks for defense-in-depth protection:

1. **UserPromptSubmit Hook:** Reminds agent of workflow rules on every message
2. **PreToolUse Hook:** Blocks source edits without active_tasks set
3. **PostToolUse Hook:** Blocks unauthorized User Verification field modifications
4. **Stop Hook:** Validates QA status before allowing completion

This defense-in-depth approach ensures quality gates can't be bypassed.

---

## Hook Architecture

**Stop Hook File:** `resources/workflows/feature-implementation/hooks/stop_qa_check.py`

**What it does:**
1. Load `.synapse/config.json`
2. Extract `third_party_workflow.active_tasks`
3. Parse task file using `task_format_schema`
4. For each active task, check QA Status field
5. Categorize: not_verified, verified_success, or verified_failure
6. Exit 0 if all verified, Exit 2 if any not verified

**What it does NOT do:**
- Run quality checks (agent's job)
- Execute tests or linting (agent's job)
- Fix anything (agent's job)
- Make decisions (user's job)

**Size:** ~400 lines

**Dependencies:** Python 3.8+ standard library only

---

## Benefits

**Simplicity:**
- Hook has single responsibility: check QA status
- No quality check execution in hook
- No subprocess management or timeouts

**Reliability:**
- Fewer moving parts = fewer failure points
- No file system traversal
- Schema-driven parsing supports any format

**User Experience:**
- Stop with failures - you control fix timing
- Clear progress indication
- Failed tasks stay tracked across sessions
- Explicit approval required for fixes

**Agent Empowerment:**
- Full tool access (playwright, grep, read, bash, etc.)
- Context-aware verification
- Can explain what it's checking and why
- Generates detailed reports

**Performance:**
- 60-70% fewer tokens
- 70-80% faster execution
- Single context (not multiple)
- Compact hook code

---

## Troubleshooting

### Hook blocks unexpectedly

**Check:**
1. Is `active_tasks` empty when it should have tasks?
2. Do task codes in `active_tasks` match task file exactly?
3. Does each task have a QA Status field?
4. Are any tasks still `[Not Started]`?

**Solution:**
- Set `active_tasks` when starting work
- Ensure task codes match: `["T001", "T002"]`
- Add QA Status fields to all tasks
- Mark verified tasks as `[Passed]` or `[Failed - reason]`

### Hook allows stop but you want verification

**Cause:** QA Status is `[Failed - ...]` (which allows stop)

**Fix:** Set QA Status to `[Not Started]` if you want the hook to block

### Task codes not found

**Cause:** Mismatch between `active_tasks` codes and task file codes

**Fix:**
```json
"active_tasks": ["T001", "T002"]  // Must match task file exactly
```

### Schema parsing errors

**Cause:** Task format doesn't match schema patterns

**Fix:** Check your `task_format_schema.patterns` match your actual task format

---

## Getting Help

**Debug commands:**

```bash
# Validate config JSON
python3 -c "import json; json.load(open('.synapse/config.json'))"

# Test hook manually
python3 resources/workflows/feature-implementation/hooks/stop_qa_check.py

# View hook output
python3 resources/workflows/feature-implementation/hooks/stop_qa_check.py 2>&1 | less
```

**Common fixes:**
- Check `.synapse/config.json` structure
- Verify hook paths in `.claude/settings.json`
- Ensure hooks are executable (`chmod +x`)
- Review `.synapse/logs/` for errors

---

## Further Reading

- [ARCHITECTURE.md](ARCHITECTURE.md) - System internals and design decisions
- [Feature Implementation README](../resources/workflows/feature-implementation/README.md) - Workflow details
- [Feature Planning README](../resources/workflows/feature-planning/README.md) - Task planning workflow
