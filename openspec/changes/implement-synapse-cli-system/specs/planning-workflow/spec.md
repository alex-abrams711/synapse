# Spec: Feature Planning Workflow

**Capability**: `planning-workflow`
**Status**: New
**Related To**: `file-operations`, `settings-management` (specific workflow implementation)

---

## ADDED Requirements

### Requirement: Task Writer Agent Definition

The system SHALL provide task-writer agent for structured task creation.

**ID**: PLAN-001 | **Priority**: P0 (Critical) | **Category**: Workflow Content

#### Scenario: Agent creates hierarchical tasks

**Given** task-writer agent is active
**When** user requests task creation
**Then** the agent SHALL create tasks with:
- Checkbox notation (`- [ ]` for incomplete, `- [x]` for complete)
- Hierarchical subtasks with proper indentation
- Quality standards reminder section
- Dev/QA/User verification subtasks

#### Scenario: Agent enforces task structure

**Given** task-writer agent is creating task
**When** generating markdown
**Then** the task SHALL include:
- Task title describing feature
- Acceptance criteria section
- Implementation notes section
- Quality checkpoints section
- Verification subtasks (Dev, QA, User)

---

### Requirement: User Prompt Reminder Hook

The system SHALL provide reminder hook for task-writer usage.

**ID**: PLAN-002 | **Priority**: P0 (Critical) | **Category**: Workflow Content

#### Scenario: Display reminder on prompt submission

**Given** user submits prompt to Claude Code
**When** UserPromptSubmit hook triggers
**Then** the system SHALL display reminder:
- Suggest using task-writer agent for new features
- Brief usage instructions
- Non-blocking (doesn't prevent submission)

---

### Requirement: Planning Workflow Settings

The system SHALL configure Claude Code for planning workflow.

**ID**: PLAN-003 | **Priority**: P0 (Critical) | **Category**: Workflow Configuration

#### Scenario: Register UserPromptSubmit hook

**Given** planning workflow is applied
**When** merging settings
**Then** settings.json SHALL include:
```json
{
  "hooks": {
    "userPromptSubmit": [
      {
        "command": ".claude/hooks/user-prompt-submit-reminder.sh"
      }
    ]
  }
}
```

---

### Requirement: Planning Workflow File Structure

The system SHALL include required files in planning workflow.

**ID**: PLAN-004 | **Priority**: P0 (Critical) | **Category**: Workflow Content

#### Scenario: Include all required files

**Given** planning workflow resources
**When** workflow is packaged
**Then** it SHALL contain:
- `agents/task-writer.md`: Agent definition
- `hooks/user-prompt-submit-reminder.sh`: Reminder hook
- `commands/synapse/sense.md`: Project analysis command
- `settings.json`: Hook configuration

---

### Requirement: Sense Command Integration

The system SHALL provide sense command for project analysis.

**ID**: PLAN-005 | **Priority**: P0 (Critical) | **Category**: Workflow Content

#### Scenario: Sense command available as /sense

**Given** planning workflow is applied
**When** user types `/sense` in Claude Code
**Then** command SHALL:
- Analyze project structure
- Detect project type and language
- Identify existing quality tools
- Generate quality configuration
- Update `.synapse/config.json` with findings

#### Scenario: Sense detects quality tools

**Given** project has linters, type checkers, test runners
**When** sense command runs
**Then** it SHALL detect and report:
- Linters (ruff, pylint, eslint, etc.)
- Type checkers (mypy, pyright, tsc, etc.)
- Test runners (pytest, jest, vitest, etc.)
- Coverage tools (coverage.py, nyc, etc.)
