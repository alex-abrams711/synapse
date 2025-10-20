# Spec: CLI Core

**Capability**: `cli-core`
**Status**: New
**Related To**: N/A (foundational capability)

---

## ADDED Requirements

### Requirement: Project Initialization Command

The system SHALL provide a `synapse init` command that initializes Synapse in a project directory.

**ID**: CLI-001 | **Priority**: P0 (Critical) | **Category**: Core Functionality

#### Scenario: Initialize in current directory

**Given** the user is in a project directory without `.synapse/`
**When** they run `synapse init`
**Then** the system SHALL:
- Create `.synapse/` directory
- Create `.synapse/config.json` with project metadata
- Create `.synapse/commands/synapse/` directory
- Copy `sense.md` command to `.synapse/commands/synapse/`
- Display success message with next steps

#### Scenario: Initialize in specified directory

**Given** the user provides a directory path
**When** they run `synapse init /path/to/project`
**Then** the system SHALL initialize Synapse in the specified directory

#### Scenario: Prevent double initialization

**Given** `.synapse/` directory already exists
**When** they run `synapse init`
**Then** the system SHALL:
- Display warning that project is already initialized
- Exit with code 0 (not an error)
- NOT overwrite existing configuration

#### Scenario: Handle permission errors

**Given** the user lacks write permissions
**When** they run `synapse init`
**Then** the system SHALL:
- Display clear error message about permissions
- Exit with code 3 (system error)

---

### Requirement: Command-Line Interface Structure

The system SHALL provide a command-line interface using argparse with subcommands.

**ID**: CLI-002 | **Priority**: P0 (Critical) | **Category**: Core Functionality

#### Scenario: Display help

**Given** the user wants to see available commands
**When** they run `synapse --help` or `synapse -h`
**Then** the system SHALL display:
- Tool description
- Available subcommands
- Global options
- Usage examples

#### Scenario: Display version

**Given** the user wants to check CLI version
**When** they run `synapse --version`
**Then** the system SHALL display the installed version number

#### Scenario: Handle unknown commands

**Given** the user provides an invalid command
**When** they run `synapse invalid-command`
**Then** the system SHALL:
- Display error message
- Suggest `synapse --help`
- Exit with code 1 (user error)

---

### Requirement: Entry Point Configuration

The system SHALL be installable as a command-line tool via setuptools entry points.

**ID**: CLI-003 | **Priority**: P0 (Critical) | **Category**: Packaging

#### Scenario: Install via pip

**Given** the package is built and published
**When** user runs `pip install synapse-cli`
**Then** the `synapse` command SHALL be available in their PATH

#### Scenario: Install via pipx

**Given** the package is built and published
**When** user runs `pipx install synapse-cli`
**Then** the `synapse` command SHALL be available globally in an isolated environment

#### Scenario: Editable install for development

**Given** developer has source code
**When** they run `pip install -e .`
**Then** the `synapse` command SHALL run from source with live changes

---

### Requirement: Resource Directory Discovery

The system SHALL correctly locate bundled resources regardless of installation method.

**ID**: CLI-004 | **Priority**: P0 (Critical) | **Category**: Packaging

#### Scenario: Locate resources in installed package

**Given** package is installed via pip
**When** CLI needs to access workflow files
**Then** the system SHALL locate resources using `pkg_resources` or `importlib.resources`

#### Scenario: Locate resources in editable install

**Given** package is installed with `pip install -e .`
**When** CLI needs to access workflow files
**Then** the system SHALL locate resources in the source directory

#### Scenario: Handle missing resources

**Given** resources directory is missing or corrupted
**When** CLI attempts to access resources
**Then** the system SHALL:
- Display clear error message
- Suggest reinstalling the package
- Exit with code 3 (system error)

---

### Requirement: Error Handling and Exit Codes

The system SHALL use consistent exit codes for different error categories.

**ID**: CLI-005 | **Priority**: P0 (Critical) | **Category**: User Experience

#### Scenario: Success exit code

**Given** any command completes successfully
**When** the command finishes
**Then** the system SHALL exit with code 0

#### Scenario: User error exit code

**Given** user provides invalid syntax or arguments
**When** the error is detected
**Then** the system SHALL:
- Exit with code 1
- Display helpful error message
- Suggest correct usage

#### Scenario: State error exit code

**Given** system state is invalid (e.g., not initialized)
**When** the error is detected
**Then** the system SHALL:
- Exit with code 2
- Explain what's wrong with state
- Suggest corrective action

#### Scenario: System error exit code

**Given** system operation fails (permissions, disk full, etc.)
**When** the error is detected
**Then** the system SHALL:
- Exit with code 3
- Explain the system error
- Provide troubleshooting steps

#### Scenario: Validation error exit code

**Given** validation fails (conflicts, invalid JSON, etc.)
**When** the error is detected
**Then** the system SHALL:
- Exit with code 4
- Explain what failed validation
- Suggest how to fix it

---

### Requirement: Configuration File Schema

The system SHALL maintain `.synapse/config.json` with standardized schema.

**ID**: CLI-006 | **Priority**: P0 (Critical) | **Category**: Data Model

#### Scenario: Create initial config

**Given** user runs `synapse init`
**When** config.json is created
**Then** it SHALL contain:
- `synapse_version`: CLI version string
- `initialized_at`: ISO 8601 timestamp
- `project.name`: Inferred from directory name
- `project.root_directory`: Absolute path
- `agent.type`: "claude-code"
- `agent.description`: "Claude Code AI coding assistant"
- `workflows.active_workflow`: null
- `workflows.applied_workflows`: empty array
- `settings.auto_backup`: true
- `settings.strict_validation`: true
- `settings.uv_required`: true

#### Scenario: Read config safely

**Given** config.json exists
**When** CLI reads configuration
**Then** the system SHALL:
- Validate JSON structure
- Provide defaults for missing fields
- Handle parse errors gracefully

#### Scenario: Update config atomically

**Given** CLI needs to modify config
**When** writing updates
**Then** the system SHALL:
- Write to temp file first
- Validate JSON structure
- Rename temp file to config.json (atomic operation)
- Preserve file if validation fails
