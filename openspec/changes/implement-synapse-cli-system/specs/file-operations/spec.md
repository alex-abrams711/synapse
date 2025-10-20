# Spec: File Operations

**Capability**: `file-operations`
**Status**: New
**Related To**: `cli-core` (requires resource discovery)

---

## ADDED Requirements

### Requirement: Workflow File Copying

The system SHALL copy workflow files from resources to `.claude/` directory.

**ID**: FILE-001 | **Priority**: P0 (Critical) | **Category**: Core Functionality

#### Scenario: Copy agent files

**Given** a workflow contains agent markdown files
**When** workflow is applied
**Then** the system SHALL:
- Copy all `.md` files from `resources/workflows/{name}/agents/` to `.claude/agents/`
- Preserve file names
- Track copied files in manifest

#### Scenario: Copy hook files

**Given** a workflow contains hook scripts
**When** workflow is applied
**Then** the system SHALL:
- Copy all files from `resources/workflows/{name}/hooks/` to `.claude/hooks/`
- Set executable permission on `.sh` files
- Track copied files in manifest

#### Scenario: Copy command files

**Given** a workflow contains slash commands
**When** workflow is applied
**Then** the system SHALL:
- Copy all files from `resources/workflows/{name}/commands/synapse/` to `.claude/commands/synapse/`
- Create directory structure if missing
- Track copied files in manifest

---

### Requirement: File Conflict Handling

The system SHALL handle existing files appropriately based on user intent.

**ID**: FILE-002 | **Priority**: P0 (Critical) | **Category**: Safety

#### Scenario: Skip existing files by default

**Given** a file already exists at the destination
**When** workflow is applied WITHOUT --force flag
**Then** the system SHALL:
- Skip the file
- Display warning about skipped file
- Continue with other files
- Track that file was skipped

#### Scenario: Overwrite files with --force

**Given** a file already exists at the destination
**When** workflow is applied WITH --force flag
**Then** the system SHALL:
- Overwrite the existing file
- Display notice about overwritten file
- Track that file was overwritten

#### Scenario: Detect file conflicts before copying

**Given** multiple files would conflict
**When** workflow application starts
**Then** the system SHALL:
- Scan for all conflicts first
- Report all conflicts to user
- Fail WITHOUT copying any files if --force not provided
- Provide option to use --force

---

### Requirement: File Permission Management

The system SHALL set appropriate file permissions after copying.

**ID**: FILE-003 | **Priority**: P0 (Critical) | **Category**: Core Functionality

#### Scenario: Make shell scripts executable

**Given** a `.sh` file is copied to `.claude/hooks/`
**When** copy operation completes
**Then** the system SHALL set executable permission (chmod +x)

#### Scenario: Handle permission errors

**Given** system cannot set executable permission
**When** attempting to chmod file
**Then** the system SHALL:
- Display warning about permission failure
- Continue with workflow application
- Log the issue for user review

#### Scenario: Respect umask for other files

**Given** non-executable files are copied
**When** creating files
**Then** the system SHALL respect user's umask settings

---

### Requirement: Directory Structure Creation

The system SHALL create necessary directory structures.

**ID**: FILE-004 | **Priority**: P0 (Critical) | **Category**: Core Functionality

#### Scenario: Create missing directories

**Given** target directory doesn't exist
**When** copying files
**Then** the system SHALL:
- Create all parent directories recursively
- Use permissions appropriate for directories
- Handle nested directory structures

#### Scenario: Handle directory creation errors

**Given** directory cannot be created (permissions, etc.)
**When** attempting mkdir
**Then** the system SHALL:
- Display clear error message
- Roll back any partial changes
- Exit with code 3 (system error)

---

### Requirement: Workflow File Discovery

The system SHALL discover available workflows from packaged resources.

**ID**: FILE-005 | **Priority**: P0 (Critical) | **Category**: Core Functionality

#### Scenario: List available workflows

**Given** user runs `synapse workflow list`
**When** listing workflows
**Then** the system SHALL:
- Scan `resources/workflows/` directory
- Display each workflow name
- Show brief description if available
- Indicate which workflow is currently active

#### Scenario: Validate workflow exists

**Given** user specifies workflow name
**When** attempting to apply workflow
**Then** the system SHALL:
- Verify workflow directory exists in resources
- Verify workflow contains required files (agents, hooks, settings.json)
- Display error if workflow not found or incomplete

---

### Requirement: File Tracking and Manifest

The system SHALL track all files copied during workflow application.

**ID**: FILE-006 | **Priority**: P0 (Critical) | **Category**: State Management

#### Scenario: Record copied files

**Given** files are being copied
**When** each file is successfully copied
**Then** the system SHALL record in manifest:
- Relative path (e.g., `.claude/agents/task-writer.md`)
- File type (agents, hooks, commands)
- Source workflow name
- Timestamp

#### Scenario: Track file operations for rollback

**Given** workflow application fails midway
**When** rolling back changes
**Then** the system SHALL use manifest to:
- Identify which files were copied
- Remove only those files
- Restore original state

---

### Requirement: Resource Validation

The system SHALL validate resource files before copying.

**ID**: FILE-007 | **Priority**: P1 (High) | **Category**: Quality

#### Scenario: Validate markdown syntax

**Given** agent or command file is markdown
**When** copying file
**Then** the system SHALL:
- Check file is valid UTF-8
- Warn if file appears corrupted
- Skip file if unreadable

#### Scenario: Validate executable scripts

**Given** hook file is a shell script
**When** copying file
**Then** the system SHALL:
- Check file has valid shebang (#!/bin/bash or #!/usr/bin/env)
- Warn if script appears malformed
- Continue anyway (let runtime handle validation)

---

### Requirement: Cleanup Operations

The system SHALL clean up empty directories after file removal.

**ID**: FILE-008 | **Priority**: P0 (Critical) | **Category**: Maintenance

#### Scenario: Remove empty agent directories

**Given** all agents are removed from `.claude/agents/`
**When** workflow removal completes
**Then** the system SHALL remove the empty `agents/` directory

#### Scenario: Remove empty command directories

**Given** all commands are removed from `.claude/commands/synapse/`
**When** workflow removal completes
**Then** the system SHALL:
- Remove empty `synapse/` directory
- Remove empty `commands/` directory if synapse was only subdirectory

#### Scenario: Preserve non-empty directories

**Given** directory contains files not from this workflow
**When** workflow removal completes
**Then** the system SHALL keep the directory and its other contents
