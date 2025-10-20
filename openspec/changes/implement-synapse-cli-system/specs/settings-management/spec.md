# Spec: Settings Management

**Capability**: `settings-management`
**Status**: New
**Related To**: `file-operations` (integrates with workflow application)

---

## ADDED Requirements

### Requirement: Settings Merge Algorithm

The system SHALL merge workflow settings into existing `.claude/settings.json` using deep merge with array appending.

**ID**: SETTINGS-001 | **Priority**: P0 (Critical) | **Category**: Core Functionality

#### Scenario: Merge into existing settings

**Given** `.claude/settings.json` exists with existing configuration
**When** workflow settings are applied
**Then** the system SHALL:
- Load both JSON files
- Deep merge workflow settings into existing settings
- Append arrays (especially hooks arrays) instead of replacing
- Preserve all existing settings not in workflow
- Write result atomically

#### Scenario: Create settings file if missing

**Given** `.claude/settings.json` does not exist
**When** workflow settings are applied
**Then** the system SHALL:
- Create `.claude/settings.json` with workflow settings
- Track that file was created

#### Scenario: Handle deeply nested settings

**Given** workflow contains nested configuration objects
**When** merging settings
**Then** the system SHALL recursively merge nested objects at all levels

---

### Requirement: Hook Configuration Management

The system SHALL manage hook configurations in settings.json.

**ID**: SETTINGS-002 | **Priority**: P0 (Critical) | **Category**: Core Functionality

#### Scenario: Append to existing hooks array

**Given** `.claude/settings.json` already has hooks configured
**When** workflow adds new hooks
**Then** the system SHALL:
- Append new hooks to existing hooks array
- NOT remove or modify existing hooks
- Maintain hook order

#### Scenario: Track added hooks for removal

**Given** hooks are added from workflow
**When** creating manifest
**Then** the system SHALL record:
- Hook type (userPromptSubmit, preToolUse, postToolUse)
- Command string
- Any matcher patterns
- Position in array (for removal)

---

### Requirement: JSON Validation

The system SHALL validate JSON structure before and after modifications.

**ID**: SETTINGS-003 | **Priority**: P0 (Critical) | **Category**: Safety

#### Scenario: Validate before merge

**Given** loading settings files
**When** JSON parsing occurs
**Then** the system SHALL:
- Catch JSON parse errors
- Display helpful error with line number
- Exit without modifying files if invalid

#### Scenario: Validate after merge

**Given** settings have been merged
**When** preparing to write file
**Then** the system SHALL:
- Validate merged result is valid JSON
- Check for required fields
- Fail operation if validation fails
- Keep original file intact

---

### Requirement: Atomic Write Operations

The system SHALL write settings files atomically to prevent corruption.

**ID**: SETTINGS-004 | **Priority**: P0 (Critical) | **Category**: Safety

#### Scenario: Use temp file for writes

**Given** writing updated settings
**When** performing write operation
**Then** the system SHALL:
1. Write to temporary file (`.claude/settings.json.tmp`)
2. Validate temp file is valid JSON
3. Rename temp file to target (atomic operation)
4. Delete temp file only after successful rename

#### Scenario: Handle write failures

**Given** write operation fails
**When** error occurs
**Then** the system SHALL:
- Keep original file unchanged
- Remove partial temp file
- Display error message
- Exit with code 3

---

### Requirement: Settings Change Reporting

The system SHALL report what settings were modified.

**ID**: SETTINGS-005 | **Priority**: P1 (High) | **Category**: User Experience

#### Scenario: Display added hooks

**Given** workflow adds hooks to settings
**When** workflow application completes
**Then** the system SHALL display:
- Hook type added
- Command being executed
- Total number of hooks in each category

#### Scenario: Display other setting changes

**Given** workflow modifies non-hook settings
**When** workflow application completes
**Then** the system SHALL list sections modified

---

### Requirement: Settings Rollback

The system SHALL support rolling back settings changes.

**ID**: SETTINGS-006 | **Priority**: P0 (Critical) | **Category**: Safety

#### Scenario: Restore settings from backup

**Given** user removes workflow
**When** restoring from backup
**Then** the system SHALL:
- Copy `.claude/settings.json` from backup
- Overwrite current settings completely
- NOT attempt selective hook removal

#### Scenario: Handle missing backup settings

**Given** backup doesn't contain settings.json
**When** restoring workflow
**Then** the system SHALL:
- Delete `.claude/settings.json` if it was created by workflow
- Keep file if it existed before workflow
