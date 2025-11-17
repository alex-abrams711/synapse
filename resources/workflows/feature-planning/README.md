# Feature Planning Workflow

**Task breakdown with mandatory formatting validation**

## Overview

This workflow helps break down features into well-structured, actionable tasks with quality gates.

Uses the `writer` sub-agent to create tasks following strict formatting standards compatible with feature-implementation verification workflows.

## Components

### 1. Writer Agent (`agents/writer.md`)

**Purpose:** Create excellently defined tasks and subtasks

**Features:**
- Hierarchical task structure
- Mandatory task code formatting (T001, T002, etc.)
- Automatic quality gate inclusion
- Status field generation

**Usage:**
```
Call the writer agent with a feature description
```

### 2. Post-Tool-Use Hook (`hooks/writer-post-tool-use.py`)

**Purpose:** Validate task formatting

**Checks:**
- Task codes are sequential and zero-padded (T001, T002, T003)
- Subtask codes match parent task (T001-ST001, T001-ST002)
- Status codes match parent task (T001-DS, T001-QA, T001-UV)
- All three status fields present (Dev, QA, User Verification)
- QA Status supports three-category verification (not verified, verified success, verified failure)

**Exit Codes:**
- `0` - Validation passed
- `2` - Validation failed (blocks with detailed error messages)

### 3. UserPromptSubmit Hook (`hooks/user-prompt-reminder.sh`)

**Purpose:** Remind user of workflow capabilities

## Task Format

### Required Structure

```markdown
[ ] - T001 - Task description
  [ ] - T001-ST001 - Subtask 1
  [ ] - T001-ST002 - Subtask 2
  [ ] - T001-DS - Dev Status: [Not Started]
  [ ] - T001-QA - QA Status: [Not Started]
  [ ] - T001-UV - User Verification Status: [Not Started]

  *Quality Standards: Maintain lint, typecheck, test, coverage, and successful build throughout implementation*

[ ] - T002 - Another task
  [ ] - T002-ST001 - Subtask 1
  [ ] - T002-DS - Dev Status: [Not Started]
  [ ] - T002-QA - QA Status: [Not Started]
  [ ] - T002-UV - User Verification Status: [Not Started]

  *Quality Standards: Maintain lint, typecheck, test, coverage, and successful build throughout implementation*
```

### Task Codes

**Top-level tasks:** `T001`, `T002`, `T003`, ... (sequential, zero-padded)

**Subtasks:** `T001-ST001`, `T001-ST002`, ... (per-task sequential)

**Status fields:**
- Dev Status: `T001-DS`
- QA Status: `T001-QA`
- User Verification: `T001-UV`

### Status Values

**Dev Status:**
- `[Not Started]`
- `[In Progress]`
- `[Complete]`

**QA Status:**
- `[Not Started]` - Not verified
- `[Passed]` or `[Complete]` - Verified successfully
- `[Failed - {reason}]` - Verified with failures

**User Verification Status:**
- `[Not Started]`
- `[Verified]`

## Example Workflow

### 1. User Requests Task Breakdown

```
User: "Break down the user authentication feature into tasks"
```

### 2. Writer Agent Creates Tasks

Writer agent generates:

```markdown
# Feature: User Authentication

## Summary
Implement complete user authentication system with login, registration,
and JWT-based session management.

## Tasks

[ ] - T001 - Implement user login endpoint
  [ ] - T001-ST001 - Create POST /api/auth/login route
  [ ] - T001-ST002 - Add JWT token generation
  [ ] - T001-ST003 - Add password verification with bcrypt
  [ ] - T001-DS - Dev Status: [Not Started]
  [ ] - T001-QA - QA Status: [Not Started]
  [ ] - T001-UV - User Verification Status: [Not Started]

  *Quality Standards: Maintain lint, typecheck, test, coverage, and successful build throughout implementation*

[ ] - T002 - Implement user registration endpoint
  [ ] - T002-ST001 - Create POST /api/auth/register route
  [ ] - T002-ST002 - Add email validation
  [ ] - T002-ST003 - Add password strength checking
  [ ] - T002-DS - Dev Status: [Not Started]
  [ ] - T002-QA - QA Status: [Not Started]
  [ ] - T002-UV - User Verification Status: [Not Started]

  *Quality Standards: Maintain lint, typecheck, test, coverage, and successful build throughout implementation*

## Dependencies
- T002 must complete before T001 (need user accounts before login)

## Notes
- Use bcrypt for password hashing
- JWT tokens expire after 24 hours
```

### 3. Validation Hook Runs

Post-tool-use hook validates:
- ✅ Task codes sequential (T001, T002)
- ✅ Subtask codes match parent
- ✅ Status codes match parent
- ✅ All required status fields present
- ✅ Format is correct

**If validation fails:**
- Hook blocks with detailed error messages
- Agent must fix formatting and retry

**If validation passes:**
- Tasks written to file
- Ready for implementation

## Quality Configuration Task

For new projects, the writer agent automatically includes:

```markdown
[ ] - T001 - Establish Quality Configuration and Testing Standards
  [ ] - T001-ST001 - Configure and verify linting tools
  [ ] - T001-ST002 - Configure and verify type checking
  [ ] - T001-ST003 - Set up testing framework and write initial smoke tests
  [ ] - T001-ST004 - Configure coverage tools and set appropriate thresholds
  [ ] - T001-ST005 - Update .synapse/config.json with accurate quality commands
  [ ] - T001-ST006 - Run '/synapse:sense' to validate and finalize quality configuration
  [ ] - T001-ST007 - Verify all quality gates pass with current codebase
  [ ] - T001-DS - Dev Status: [Not Started]
  [ ] - T001-QA - QA Status: [Not Started]
  [ ] - T001-UV - User Verification Status: [Not Started]

  *Quality Standards: This task establishes the baseline quality gates for the project*
```

**Why:** Ensures quality gates are established BEFORE feature development begins.

## Validation Error Examples

### Missing Status Field

```
❌ Validation failed for tasks.md:
  Line 5: Task T001 missing required 'QA Status' field with code T001-QA
```

**Fix:** Add the missing status field:
```markdown
  [ ] - T001-QA - QA Status: [Not Started]
```

### Wrong Task Code

```
❌ Validation failed for tasks.md:
  Line 1: Task code 'T1' is incorrect. Expected 'T001' (tasks must be sequential and zero-padded)
```

**Fix:** Use zero-padded sequential codes:
```markdown
[ ] - T001 - Task description  (not T1)
```

### Mismatched Status Code

```
❌ Validation failed for tasks.md:
  Line 6: QA Status code 'T002-QA' doesn't match task code. Expected 'T001-QA'
```

**Fix:** Status codes must match parent task:
```markdown
[ ] - T001 - Task description
  [ ] - T001-QA - QA Status: [Not Started]  (not T002-QA)
```

## Task File Locations

The validation hook searches for tasks in:

1. `tasks.md` (root)
2. `openspec/changes/*/tasks.md` (OpenSpec pattern)
3. `specs/*/tasks.md` (Spec Kit pattern)

## Configuration

In `settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "hooks/user-prompt-reminder.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": "uv run .claude/hooks/writer-post-tool-use.py"
          }
        ]
      }
    ]
  }
}
```

## Best Practices

1. **Use imperative mood** - "Implement", "Create", "Update"
2. **One atomic unit per task** - Each task should be independently completable
3. **Include acceptance criteria** - What defines "done"
4. **Consider dependencies** - Note when tasks must be ordered
5. **Maintain consistent granularity** - Similar tasks should be similar size
6. **Include edge cases** - Don't forget error handling

## Integration with Feature Implementation

Tasks created by this workflow are ready for the feature-implementation workflow:

1. Feature planning creates tasks with codes
2. Feature implementation uses task codes in `active_tasks`
3. QA verification checks status fields
4. QA verification allows flexible failure handling

## Compatibility

This workflow is compatible with:
- ✅ Feature Implementation
- ✅ Any workflow that uses task codes

The validation ensures consistent formatting across all workflows.
