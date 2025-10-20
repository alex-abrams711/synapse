# Spec: State Tracking

**Capability**: `state-tracking`
**Status**: New
**Related To**: `cli-core`, `file-operations` (maintains operational state)

---

## ADDED Requirements

### Requirement: Workflow Manifest Creation

The system SHALL create detailed manifest of workflow changes.

**ID**: STATE-001 | **Priority**: P0 (Critical) | **Category**: State Management

#### Scenario: Create manifest on workflow application

**Given** workflow is successfully applied
**When** all files are copied and settings merged
**Then** the system SHALL create `.synapse/workflow-manifest.json` containing:
- `workflow_name`: Name of applied workflow
- `applied_at`: ISO 8601 timestamp
- `synapse_version`: CLI version that applied workflow
- `files_copied`: Array of file objects with path and type
- `hooks_added`: Array of hook configurations
- `settings_updated`: Array of settings sections modified

#### Scenario: Update manifest on subsequent operations

**Given** user applies another workflow
**When** workflow application completes
**Then** the system SHALL update manifest to reflect combined state

---

### Requirement: Config Update on Workflow Changes

The system SHALL update config.json when workflows change.

**ID**: STATE-002 | **Priority**: P0 (Critical) | **Category**: State Management

#### Scenario: Set active workflow

**Given** workflow is applied
**When** operation completes
**Then** the system SHALL:
- Set `workflows.active_workflow` to workflow name
- Add entry to `workflows.applied_workflows` array with name and timestamp
- Write updated config atomically

#### Scenario: Clear active workflow on removal

**Given** user removes workflow
**When** removal completes
**Then** the system SHALL:
- Set `workflows.active_workflow` to null
- Keep history in `applied_workflows` for audit trail

---

### Requirement: Workflow Status Reporting

The system SHALL provide workflow status information.

**ID**: STATE-003 | **Priority**: P0 (Critical) | **Category**: User Experience

#### Scenario: Display active workflow

**Given** user runs `synapse workflow status`
**When** querying status
**Then** the system SHALL display:
- Active workflow name
- Application timestamp
- Number of files managed
- Number of hooks configured
- Backup availability

#### Scenario: Handle no active workflow

**Given** no workflow is active
**When** user runs `synapse workflow status`
**Then** the system SHALL display message indicating no active workflow

---

### Requirement: Workflow History Tracking

The system SHALL maintain history of applied workflows.

**ID**: STATE-004 | **Priority**: P2 (Medium) | **Category**: Auditing

#### Scenario: Record workflow applications

**Given** workflows are applied over time
**When** updating config
**Then** the system SHALL append to `applied_workflows` array

#### Scenario: Display workflow history

**Given** user runs `synapse workflow status --history`
**When** displaying status
**Then** the system SHALL show chronological list of workflows

---

### Requirement: State Consistency Validation

The system SHALL validate state consistency.

**ID**: STATE-005 | **Priority**: P1 (High) | **Category**: Safety

#### Scenario: Verify manifest matches filesystem

**Given** manifest exists
**When** user runs workflow command
**Then** the system SHALL check that files listed in manifest exist

#### Scenario: Detect state drift

**Given** files were manually modified
**When** checking status
**Then** the system SHALL warn about files that don't match manifest

---

### Requirement: Manifest Schema

The system SHALL use standardized manifest schema.

**ID**: STATE-006 | **Priority**: P0 (Critical) | **Category**: Data Model

#### Scenario: Files copied structure

**Given** recording copied file
**When** adding to manifest
**Then** each entry SHALL contain:
- `path`: Relative path from project root
- `type`: One of "agents", "hooks", "commands"
- `source_workflow`: Workflow name

#### Scenario: Hooks added structure

**Given** recording added hook
**When** adding to manifest
**Then** each entry SHALL contain:
- `hook_type`: "UserPromptSubmit", "PreToolUse", or "PostToolUse"
- `matcher`: Pattern string (may be empty)
- `command`: Full command string
- `type`: "command" or "inline"
