# Migration Guide: Legacy to Option 6 Workflows

This guide helps you transition from legacy workflows to the new Option 6 implementation.

## Should You Migrate?

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

## What's Different

### Configuration Structure

**Legacy:**
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

**Option 6:**
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

**Key changes:**
- `third_party_workflows.detected` (array) → `third_party_workflow` (object)
- Added required `active_tasks` field
- One workflow per project (not multiple)

### QA Status Semantics

**Legacy:**
- `[Not Started]`, `[In Progress]`, `[Complete]`
- Hook blocks until all tasks complete

**Option 6:**
- `[Not Started]` - Hook blocks
- `[Passed]`/`[Complete]` - Hook allows
- `[Failed - {reason}]` - Hook allows (NEW!)

**Impact:** You can now stop with failures and fix them later.

### Hook Behavior

**Legacy:**
- Hook runs quality checks
- Complex logic (~1000+ lines)
- Blocks on failures

**Option 6:**
- Hook only checks status
- Simple logic (~400 lines)
- Allows stop after verification (even with failures)
- Agent runs quality checks

### Active Tasks Management

**Legacy:**
- Automatic detection from task file
- No manual management needed

**Option 6:**
- Agent sets `active_tasks` when starting work
- Agent clears `active_tasks` when done
- More explicit, but requires discipline

## Migration Steps

### Step 1: Complete In-Progress Work

Before migrating, finish any active features using the legacy workflow.

```bash
# If you have uncommitted changes
git add .
git commit -m "Complete feature X before migration"
```

### Step 2: Backup Current Config

```bash
cp .synapse/config.json .synapse/config.json.backup
```

### Step 3: Update Config Structure

**Manual approach:**

1. Read your current `.synapse/config.json`
2. Find the `third_party_workflows.detected` array
3. Take the first (or preferred) workflow object
4. Restructure as shown above
5. Add `active_tasks: []` field
6. Save as `third_party_workflow` (singular, object)

**Automated approach (when available):**

```bash
# Once sense command is updated
synapse workflow remove
synapse workflow feature-planning  # Re-detect with new structure
```

### Step 4: Update Task Format (If Needed)

Check your tasks.md:

**Required format:**
```markdown
[ ] - T001 - Task description
  [ ] - T001-DS - Dev Status: [Not Started]
  [ ] - T001-QA - QA Status: [Not Started]
  [ ] - T001-UV - User Verification Status: [Not Started]
```

**If your tasks don't have codes:** Use the feature-planning workflow's writer agent to regenerate them.

### Step 5: Update Workflow References

Update your `.claude/settings.json` or workflow configuration to point to new workflows:

```json
{
  "workflows": {
    "active_workflow": "feature-implementation-v2"
  }
}
```

### Step 6: Test the New Workflow

1. Create a simple test task
2. Set `active_tasks` to that task code
3. Try to stop (should block)
4. Mark QA Status as `[Passed]`
5. Try to stop (should allow)
6. Clear `active_tasks`

### Step 7: Learn the New Workflow

Read:
- `/resources/workflows/feature-implementation-v2/README.md`
- `/resources/workflows/feature-planning/README.md`

Understand:
- When to set `active_tasks`
- How to handle failures
- Exit code meanings

## Common Migration Issues

### Issue: Hook blocks but I cleared active_tasks

**Cause:** `active_tasks` still has task codes

**Fix:**
```json
{
  "third_party_workflow": {
    "active_tasks": []  // Must be empty array, not [""]
  }
}
```

### Issue: Hook allows stop but I want verification

**Cause:** QA Status is `[Failed - ...]` (which allows stop in Option 6)

**Fix:** Set QA Status to `[Not Started]` if you want the hook to block

### Issue: Task codes not found

**Cause:** Mismatch between `active_tasks` codes and task file codes

**Fix:** Ensure codes match exactly:
```json
"active_tasks": ["T001", "T002"]  // Must match task file
```

### Issue: Schema parsing errors

**Cause:** Task format doesn't match schema patterns

**Fix:** Check your `task_format_schema.patterns` match your actual task format

## Rollback Plan

If you need to rollback:

1. Restore backup config:
```bash
cp .synapse/config.json.backup .synapse/config.json
```

2. Switch back to legacy workflow in settings

3. Continue using `legacy/resources/workflows/`

## Gradual Migration

You don't have to migrate everything at once:

**Option A: Per-feature migration**
- Use legacy for current feature
- Use Option 6 for next feature
- Migrate when natural boundaries occur

**Option B: Hybrid approach**
- Use feature-planning (works with both)
- Use legacy feature-implementation for now
- Switch to Option 6 when comfortable

**Option C: Trial run**
- Create a test branch
- Try Option 6 on that branch
- Decide based on experience

## Getting Help

**If migration fails:**

1. Check logs in `.synapse/logs/`
2. Verify config structure with schema
3. Test hook manually: `python3 resources/workflows/feature-implementation-v2/hooks/stop_qa_check.py`
4. Review this guide's troubleshooting section

**Common debugging commands:**

```bash
# Validate config JSON
python3 -c "import json; json.load(open('.synapse/config.json'))"

# Check hook execution
python3 resources/workflows/feature-implementation-v2/hooks/stop_qa_check.py

# View hook directive
python3 resources/workflows/feature-implementation-v2/hooks/stop_qa_check.py 2>&1 | less
```

## Why Migrate?

**Reliability:**
- Simpler hooks = fewer failure points
- Schema-driven parsing = flexible formats
- Clear exit codes = predictable behavior

**Control:**
- Stop with failures
- Fix on your schedule
- Track failed tasks

**Maintainability:**
- ~400 lines vs 1000+
- Clear separation: hook checks, agent verifies
- Easier to debug and extend

**Future-proof:**
- New features built on Option 6
- Active development and testing
- Community feedback incorporated

## Conclusion

Migration is optional but recommended for new work. The Option 6 approach represents lessons learned from the legacy implementation and provides a more robust, flexible foundation.

Both systems will continue to be supported. Choose what works best for your project.
