# Spec: Backup System

**Capability**: `backup-system`
**Status**: New
**Related To**: `file-operations`, `settings-management` (provides safety layer)

---

## ADDED Requirements

### Requirement: Timestamped Backup Creation

The system SHALL create timestamped backups before any workflow modification.

**ID**: BACKUP-001 | **Priority**: P0 (Critical) | **Category**: Safety

#### Scenario: Create backup before workflow application

**Given** user applies a workflow
**When** workflow application starts
**Then** the system SHALL:
- Create `.synapse/backups/{YYYYMMDD_HHMMSS}/` directory
- Copy entire `.claude/` directory to backup location
- Record backup timestamp in manifest
- Continue with workflow application only if backup succeeds

#### Scenario: Skip backup if .claude missing

**Given** `.claude/` directory doesn't exist
**When** workflow application starts
**Then** the system SHALL skip backup creation and proceed

#### Scenario: Handle backup creation failures

**Given** backup creation fails (disk full, permissions, etc.)
**When** error occurs
**Then** the system SHALL:
- Display error message
- Abort workflow application
- Exit with code 3
- NOT modify any files

---

### Requirement: Complete Directory Backup

The system SHALL backup the entire `.claude/` directory structure.

**ID**: BACKUP-002 | **Priority**: P0 (Critical) | **Category**: Safety

#### Scenario: Backup all subdirectories

**Given** `.claude/` contains agents/, hooks/, commands/ subdirectories
**When** creating backup
**Then** the system SHALL recursively copy all subdirectories and files

#### Scenario: Backup settings file

**Given** `.claude/settings.json` exists
**When** creating backup
**Then** the system SHALL include settings.json in backup

#### Scenario: Preserve file permissions in backup

**Given** executable hooks in `.claude/hooks/`
**When** creating backup
**Then** the system SHALL preserve executable permissions

---

### Requirement: Backup Restoration

The system SHALL restore `.claude/` directory from backup during workflow removal.

**ID**: BACKUP-003 | **Priority**: P0 (Critical) | **Category**: Safety

#### Scenario: Restore from latest backup

**Given** user removes active workflow
**When** restoration process starts
**Then** the system SHALL:
- Identify latest backup by timestamp
- Delete current `.claude/` contents
- Copy all files from backup to `.claude/`
- Restore file permissions
- Report success

#### Scenario: Handle missing backup

**Given** no backup exists for current workflow
**When** user attempts workflow removal
**Then** the system SHALL:
- Warn user no backup available
- Ask for confirmation to proceed
- Delete workflow files based on manifest only
- Exit if user cancels

---

### Requirement: Backup Management

The system SHALL manage backup storage.

**ID**: BACKUP-004 | **Priority**: P2 (Medium) | **Category**: Maintenance

#### Scenario: List available backups

**Given** multiple backups exist
**When** user checks workflow status
**Then** the system SHALL display backup timestamps and sizes

#### Scenario: Automatic cleanup

**Given** more than 10 backups exist
**When** creating new backup
**Then** the system MAY delete oldest backups to maintain limit

---

### Requirement: Backup Validation

The system SHALL validate backups before relying on them.

**ID**: BACKUP-005 | **Priority**: P1 (High) | **Category**: Safety

#### Scenario: Verify backup completeness

**Given** backup was created
**When** backup creation completes
**Then** the system SHALL verify:
- Backup directory exists
- Key files are present
- File count matches source

#### Scenario: Detect corrupted backups

**Given** restoring from backup
**When** reading backup files
**Then** the system SHALL:
- Check for read errors
- Warn about missing files
- Attempt best-effort restoration
