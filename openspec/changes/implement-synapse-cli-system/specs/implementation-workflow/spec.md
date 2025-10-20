# Spec: Feature Implementation Workflow

**Capability**: `implementation-workflow`
**Status**: New
**Related To**: `file-operations`, `settings-management` (specific workflow implementation)

---

## ADDED Requirements

### Requirement: Implementer Agent Definition

The system SHALL provide implementer agent for minimal, quality-gated changes.

**ID**: IMPL-001 | **Priority**: P0 (Critical) | **Category**: Workflow Content

#### Scenario: Agent makes minimal changes

**Given** implementer agent is working on task
**When** implementing feature
**Then** the agent SHALL:
- Make minimum changes to complete single task
- NOT add features beyond task scope
- Run quality checks before marking complete
- Update task status only when all checks pass

#### Scenario: Agent enforces quality gates

**Given** implementer agent completes changes
**When** attempting to mark task complete
**Then** the agent SHALL verify:
- Linting passes (if configured)
- Type checking passes (if configured)
- Tests pass (if configured)
- Coverage meets threshold (if configured)

---

### Requirement: Verifier Agent Definition

The system SHALL provide verifier agent for comprehensive QA.

**ID**: IMPL-002 | **Priority**: P0 (Critical) | **Category**: Workflow Content

#### Scenario: Agent performs comprehensive testing

**Given** verifier agent is activated
**When** performing verification
**Then** the agent SHALL:
- Run full test suite
- Launch application for UI testing
- Use Playwright for browser automation
- Capture screenshots at key verification points
- Test Dev/QA/User verification scenarios

#### Scenario: Agent uses Playwright for UI verification

**Given** verifier agent needs to test UI
**When** running verification
**Then** the agent SHALL:
- Launch browser in headless mode
- Navigate to application
- Take full-page screenshots
- Test key user interactions
- Verify visual regression

---

### Requirement: PreToolUse Quality Gate Hook

The system SHALL provide PreToolUse hook to validate task readiness.

**ID**: IMPL-003 | **Priority**: P0 (Critical) | **Category**: Workflow Content

#### Scenario: Validate task before tool execution

**Given** implementer is about to use tool
**When** PreToolUse hook triggers
**Then** the hook SHALL:
- Parse current task from tracking file
- Verify task is in correct status
- Check prerequisites are met
- Block tool use if validation fails
- Allow tool use if validation passes

#### Scenario: Execute with uv run

**Given** PreToolUse hook is Python script
**When** hook executes
**Then** command SHALL be: `uv run .claude/hooks/task_implementer_pretool_gate.py`

---

### Requirement: PostToolUse Quality Gate Hook

The system SHALL provide PostToolUse hook to run quality checks.

**ID**: IMPL-004 | **Priority**: P0 (Critical) | **Category**: Workflow Content

#### Scenario: Run quality checks after tool use

**Given** implementer used a tool
**When** PostToolUse hook triggers
**Then** the hook SHALL:
- Load quality configuration from `.synapse/config.json`
- Run configured linter
- Run configured type checker
- Run configured tests
- Check code coverage
- Block progression if any check fails

#### Scenario: Report quality check results

**Given** quality checks run
**When** hook completes
**Then** the hook SHALL:
- Display pass/fail for each check
- Show detailed error messages on failure
- Exit with non-zero code to block Claude Code
- Exit with zero code to allow progression

---

### Requirement: Verification Completion Hook

The system SHALL provide PostToolUse hook for verification completion.

**ID**: IMPL-005 | **Priority**: P0 (Critical) | **Category**: Workflow Content

#### Scenario: Update task status after verification

**Given** verifier agent completes verification
**When** PostToolUse hook triggers
**Then** the hook SHALL:
- Parse task tracking file
- Update verification subtasks (Dev/QA/User)
- Mark task complete if all verifications pass
- Generate verification report

---

### Requirement: Implementation Workflow Settings

The system SHALL configure Claude Code for implementation workflow.

**ID**: IMPL-006 | **Priority**: P0 (Critical) | **Category**: Workflow Configuration

#### Scenario: Register all hook types

**Given** implementation workflow is applied
**When** merging settings
**Then** settings.json SHALL include:
```json
{
  "hooks": {
    "userPromptSubmit": [{
      "command": ".claude/hooks/user-prompt-submit-reminder.sh"
    }],
    "preToolUse": [{
      "command": "uv run .claude/hooks/task_implementer_pretool_gate.py"
    }],
    "postToolUse": [
      {
        "command": "uv run .claude/hooks/task_implementer_quality_gate.py"
      },
      {
        "command": "uv run .claude/hooks/task_verifier_completion.py"
      }
    ]
  }
}
```

---

### Requirement: Implementation Workflow File Structure

The system SHALL include required files in implementation workflow.

**ID**: IMPL-007 | **Priority**: P0 (Critical) | **Category**: Workflow Content

#### Scenario: Include all required files

**Given** implementation workflow resources
**When** workflow is packaged
**Then** it SHALL contain:
- `agents/implementer.md`: Implementer agent definition
- `agents/verifier.md`: Verifier agent definition
- `hooks/user-prompt-submit-reminder.sh`: Reminder hook
- `hooks/task_implementer_pretool_gate.py`: PreToolUse validation
- `hooks/task_implementer_quality_gate.py`: PostToolUse quality checks
- `hooks/task_verifier_completion.py`: Verification completion
- `commands/synapse/sense.md`: Project analysis command
- `settings.json`: All hook configurations

---

### Requirement: Python Hook Dependencies

The system SHALL use PEP 723 inline dependencies in Python hooks.

**ID**: IMPL-008 | **Priority**: P0 (Critical) | **Category**: Workflow Content

#### Scenario: Declare dependencies in hook scripts

**Given** Python hook requires external libraries
**When** hook file is created
**Then** it SHALL include inline metadata:
```python
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.31",  # example dependency
# ]
# ///
```

#### Scenario: uv installs dependencies automatically

**Given** Python hook has inline dependencies
**When** hook executes via `uv run`
**Then** uv SHALL:
- Create isolated environment
- Install declared dependencies
- Execute hook script
- Cache environment for performance

---

### Requirement: Quality Configuration Schema

The system SHALL define quality configuration schema in `.synapse/config.json`.

**ID**: IMPL-009 | **Priority**: P0 (Critical) | **Category**: Data Model

#### Scenario: Quality config structure

**Given** sense command detects quality tools
**When** updating config.json
**Then** it SHALL add `quality_config` section:
```json
{
  "quality_config": {
    "linter": {"tool": "ruff", "command": "ruff check"},
    "type_checker": {"tool": "mypy", "command": "mypy ."},
    "test_runner": {"tool": "pytest", "command": "pytest"},
    "coverage": {"tool": "coverage", "command": "coverage run -m pytest", "threshold": 80}
  }
}
```

#### Scenario: Hooks read quality config

**Given** quality gate hooks execute
**When** determining what to run
**Then** hooks SHALL read `quality_config` from `.synapse/config.json`
