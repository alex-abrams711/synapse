# Synapse User Guide: Simplified QA Verification

This comprehensive guide covers both the architecture of Synapse's simplified QA verification system and how to migrate from legacy workflows.

> **Technical Note**: This architecture is internally called "Option 6" - the sixth design iteration that achieved the right balance of simplicity and reliability.

---

## Part 1: Understanding the Architecture

### Overview

Synapse implements a simplified, two-stage architecture for QA verification:

1. **Hook (Simple)**: Checks if QA verification has been done for active tasks
2. **Agent (Smart)**: Performs the actual verification using all available tools

This approach eliminates the complexity of having the hook run quality checks directly.

**Key Innovation:** The hook enforces verification (blocks if QA Status = [Not Started]) but allows stop with failures (allows if QA Status = [Failed - reason]). This gives users full control over when to fix vs. defer issues.

---

### The Core Philosophy

**"The hook should be dumb, the agent should be smart."**

**Why?**

**Hooks are limited:**
- Restricted execution environment
- No conversation context
- Prone to timeouts
- Hard to debug
- Can't ask questions

**Agents are powerful:**
- Full tool access (grep, read, bash, playwright, etc.)
- Complete conversation context
- Can ask clarifying questions
- Can provide detailed reports
- Can make informed decisions

**Solution:**
- Hook: Simple status checker (~400 lines) - only reads config and checks QA Status values
- Agent: Smart verifier (unlimited) - runs all quality checks, analyzes results, updates status

---

### Three-Category QA Status System

This is the core innovation that makes the system work:

```
[Not Started]        → NOT VERIFIED   → Hook blocks (Exit 2)
[Passed]/[Complete]  → VERIFIED SUCCESS → Hook allows (Exit 1)
[Failed - {reason}]  → VERIFIED FAILURE → Hook allows (Exit 1)
```

**Why this matters:**

| Approach | Behavior | Problem |
|----------|----------|---------|
| **Old (Legacy)** | Can't stop until everything passes | User stuck in fix loop |
| **New (Current)** | Can stop after verification regardless of outcome | User controls fix timing |

**The secret:** Treat `[Failed - reason]` as a **verified state**, not unverified. The task has been checked; it just didn't pass. Failed tasks stay tracked in `active_tasks` until the user decides to address them.

---

### Configuration Structure

**Breaking Change from Legacy:** Single workflow per project (cleaner design)

**Old Format (Legacy):**
```json
{
  "third_party_workflows": {
    "detected": [
      {
        "type": "openspec",
        "active_tasks_file": "tasks.md",
        "task_format_schema": {...}
      }
    ]
  }
}
```

**New Format (Current):**
```json
{
  "third_party_workflow": {
    "type": "openspec",
    "active_tasks_file": "tasks.md",
    "active_tasks": ["T001", "T002"],
    "task_format_schema": {
      "version": "2.0",
      "patterns": {...},
      "field_mapping": {...},
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

**Key changes:**
- `third_party_workflows.detected` (array) → `third_party_workflow` (object)
- Added required `active_tasks` field for tracking work in progress
- One workflow per project (simpler, cleaner)

---

### Exit Code Strategy

| Exit Code | Meaning | Use Case |
|-----------|---------|----------|
| **0** | ✅ Success | All active tasks verified OR no active tasks |
| **1** | ⚠️ Warning | Show message to user (allow stop) |
| **2** | ❌ Block | Verification required, cannot stop |

**Exit Code Scenarios:**

**Exit 0 - Allow Stop:**
- All tasks in `active_tasks` have verified QA Status (success OR failure)
- OR `active_tasks` is empty

**Exit 1 - Warning (Allow Stop):**
- Used for verification reports
- All tasks verified, show completion message to user

**Exit 2 - Block (Verification Required):**
- No active tasks set when needed
- Task file doesn't exist
- Active task code not found in task file
- Task missing QA Status field
- Any active task has QA Status = [Not Started]

---

### Active Tasks Management

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

### Workflow Example: All Tasks Pass

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

### Workflow Example: Some Tasks Fail

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

### Continuing Work on Failed Tasks

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

### Hook Architecture Details

**File:** `resources/workflows/feature-implementation-v2/hooks/stop_qa_check.py`

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

**Size:** ~400 lines (vs 1000+ in legacy)

**Dependencies:** Python 3.8+ standard library only

---

### Multi-Layer Protection System

The system includes four complementary hooks for defense-in-depth protection:

1. **UserPromptSubmit Hook:** Reminds agent of workflow rules on every message
2. **PreToolUse Hook:** Blocks source edits without active_tasks set (prevents bypass)
3. **PostToolUse Hook:** Blocks unauthorized User Verification field modifications
4. **Stop Hook:** Validates QA status before allowing completion

This defense-in-depth approach ensures quality gates can't be bypassed.

---

### Benefits of the Simplified Architecture

**Simplicity:**
- Hook is ~400 lines (vs 1000+)
- Single responsibility: check QA status only
- No quality check execution in hook
- No subprocess management or timeouts

**Reliability:**
- Fewer moving parts = fewer failure points
- No file system traversal (no hanging)
- No external command execution (no timeout issues)
- Schema-driven parsing (flexible format support)

**User Experience:**
- Stop with failures (user controls fix timing)
- Clear progress indication (partial verification)
- Failed tasks stay tracked across sessions
- Explicit approval required for fixes

**Agent Empowerment:**
- Full tool access (playwright, grep, read, bash, etc.)
- Context-aware verification
- Can explain what it's checking and why
- Generates better reports with context

**Performance:**
- 60-70% fewer tokens used
- 70-80% faster execution
- 66% less context overhead (1 context vs 3)
- 60% less hook code

---

---

## Part 2: Migrating from Legacy Workflows

### Should You Migrate?

**Consider migrating if:**
- ✅ You want simpler, more reliable QA verification
- ✅ You want control over when to fix failures
- ✅ You want to track failed tasks across sessions
- ✅ You're starting a new feature or project phase

**Stay with legacy if:**
- ❌ You have in-progress work with the current system
- ❌ You prefer the existing workflow behavior
- ❌ You don't want to update your config structure

**Note:** Both systems are fully supported. There's no pressure to migrate.

---

### What's Different

| Aspect | Legacy | Current |
|--------|--------|----------|
| **Config structure** | `third_party_workflows.detected[]` (array) | `third_party_workflow` (object) |
| **Active tasks** | Automatic detection | Manual `active_tasks` field |
| **QA Status values** | [Not Started], [In Progress], [Complete] | [Not Started], [Passed], [Failed - reason] |
| **Hook complexity** | ~1000+ lines | ~400 lines |
| **Hook duty** | Run quality checks | Check status only |
| **Stop with failures** | No (blocks until fixed) | Yes (allows after verification) |
| **Failed task tracking** | Lost on stop | Preserved in active_tasks |
| **Agent tools** | Limited | Full access |
| **Context overhead** | High (3 contexts) | Low (1 context) |
| **Fix timing** | Immediate (forced) | User's choice |

---

### Migration Steps

#### Step 1: Complete In-Progress Work

Before migrating, finish any active features using the legacy workflow.

```bash
# If you have uncommitted changes
git add .
git commit -m "Complete feature X before migration"
```

#### Step 2: Backup Current Config

```bash
cp .synapse/config.json .synapse/config.json.backup
```

#### Step 3: Update Config Structure

**Manual approach:**

1. Read your current `.synapse/config.json`
2. Find the `third_party_workflows.detected` array
3. Take the first (or preferred) workflow object
4. Restructure to single object format
5. Add `active_tasks: []` field
6. Save as `third_party_workflow` (singular, object)

**Before:**
```json
{
  "third_party_workflows": {
    "detected": [
      {
        "type": "openspec",
        "active_tasks_file": "tasks.md",
        "task_format_schema": {...}
      }
    ]
  }
}
```

**After:**
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

#### Step 4: Update Task Format (If Needed)

Check your tasks.md for required format:

```markdown
[ ] - T001 - Task description
  [ ] - T001-DS - Dev Status: [Not Started]
  [ ] - T001-QA - QA Status: [Not Started]
  [ ] - T001-UV - User Verification Status: [Not Started]
```

If your tasks don't have codes, use the feature-planning workflow's writer agent to regenerate them.

#### Step 5: Update Workflow References

Update your workflow configuration:

```json
{
  "workflows": {
    "active_workflow": "feature-implementation-v2"
  }
}
```

#### Step 6: Test the New Workflow

1. Create a simple test task
2. Set `active_tasks` to that task code
3. Try to stop (should block)
4. Mark QA Status as `[Passed]`
5. Try to stop (should allow)
6. Clear `active_tasks`

#### Step 7: Learn the New Workflow

Read:
- `resources/workflows/feature-implementation-v2/README.md`
- `resources/workflows/feature-planning/README.md`

Understand:
- When to set `active_tasks`
- How to handle failures
- Exit code meanings
- Three-category QA Status system

---

### Common Migration Issues

#### Issue: Hook blocks but I cleared active_tasks

**Cause:** `active_tasks` still has task codes

**Fix:**
```json
{
  "third_party_workflow": {
    "active_tasks": []  // Must be empty array, not [""]
  }
}
```

#### Issue: Hook allows stop but I want verification

**Cause:** QA Status is `[Failed - ...]` (which allows stop in current system)

**Fix:** Set QA Status to `[Not Started]` if you want the hook to block

#### Issue: Task codes not found

**Cause:** Mismatch between `active_tasks` codes and task file codes

**Fix:** Ensure codes match exactly:
```json
"active_tasks": ["T001", "T002"]  // Must match task file exactly
```

#### Issue: Schema parsing errors

**Cause:** Task format doesn't match schema patterns

**Fix:** Check your `task_format_schema.patterns` match your actual task format

---

### Rollback Plan

If you need to rollback:

1. Restore backup config:
```bash
cp .synapse/config.json.backup .synapse/config.json
```

2. Switch back to legacy workflow in settings

3. Continue using `legacy/resources/workflows/`

---

### Gradual Migration Options

You don't have to migrate everything at once:

**Option A: Per-feature migration**
- Use legacy for current feature
- Use new workflows for next feature
- Migrate at natural boundaries

**Option B: Hybrid approach**
- Use feature-planning (works with both)
- Use legacy feature-implementation for now
- Switch to new workflows when comfortable

**Option C: Trial run**
- Create a test branch
- Try new workflows on that branch
- Decide based on experience

---

### Getting Help

**If migration fails:**

1. Check logs in `.synapse/logs/`
2. Verify config structure matches schema
3. Test hook manually: `python3 resources/workflows/feature-implementation-v2/hooks/stop_qa_check.py`
4. Review troubleshooting section

**Common debugging commands:**

```bash
# Validate config JSON
python3 -c "import json; json.load(open('.synapse/config.json'))"

# Check hook execution
python3 resources/workflows/feature-implementation-v2/hooks/stop_qa_check.py

# View hook directive
python3 resources/workflows/feature-implementation-v2/hooks/stop_qa_check.py 2>&1 | less
```

---

### Why Migrate?

**Reliability:**
- Simpler hooks = fewer failure points
- Schema-driven parsing = flexible formats
- Clear exit codes = predictable behavior

**Control:**
- Stop with failures
- Fix on your schedule
- Track failed tasks across sessions

**Performance:**
- 60-70% fewer tokens
- 70-80% faster execution
- 66% less context overhead

**Maintainability:**
- ~400 lines vs 1000+
- Clear separation: hook checks, agent verifies
- Easier to debug and extend

**Future-proof:**
- New features built on current architecture
- Active development and testing
- Community feedback incorporated

---

## Comparison Summary

| Aspect | Legacy | Current |
|--------|--------|----------|
| **Philosophy** | Hook does everything | Hook checks, agent verifies |
| **Complexity** | High (~1000+ lines) | Low (~400 lines) |
| **User control** | Forced immediate fixes | Choose when to fix |
| **Failed tasks** | Lost on stop | Tracked across sessions |
| **Performance** | Slower, high tokens | Faster, low tokens |
| **Reliability** | Complex, timeout-prone | Simple, robust |
| **Flexibility** | Rigid format | Schema-driven |

---

## Conclusion

The current architecture represents a fundamental improvement based on lessons learned from the legacy implementation. The key insight—"the hook should be dumb, the agent should be smart"—leads to a more reliable, maintainable, and user-friendly system.

Migration is optional but recommended for new work. Both systems will continue to be supported. Choose what works best for your project.

For detailed workflow documentation, see:
- `resources/workflows/feature-implementation-v2/README.md` - Complete workflow guide
- `resources/workflows/feature-planning/README.md` - Task planning workflow
- `resources/README.md` - Quick start guide
