# Spec: Sense Command

**Capability**: `sense-command`
**Status**: New
**Related To**: `cli-core`, `planning-workflow`, `implementation-workflow` (shared by both workflows)

---

## ADDED Requirements

### Requirement: Project Analysis

The system SHALL analyze project structure and detect configuration.

**ID**: SENSE-001 | **Priority**: P0 (Critical) | **Category**: Core Functionality

#### Scenario: Detect project type

**Given** sense command is executed
**When** analyzing project
**Then** the system SHALL detect:
- Primary programming language(s)
- Project type (web app, library, CLI tool, etc.)
- Framework/runtime (if applicable)
- Package manager

#### Scenario: Scan for configuration files

**Given** sense command is analyzing project
**When** scanning directory
**Then** the system SHALL look for:
- `pyproject.toml`, `package.json`, `Cargo.toml`, etc.
- Configuration files for quality tools
- Test directories
- CI/CD configuration files

---

### Requirement: Quality Tool Detection

The system SHALL detect installed quality tools.

**ID**: SENSE-002 | **Priority**: P0 (Critical) | **Category**: Core Functionality

#### Scenario: Detect linters

**Given** sense command is analyzing project
**When** checking for linters
**Then** the system SHALL detect:
- Python: ruff, pylint, flake8, black
- JavaScript/TypeScript: eslint, prettier
- Go: golint, gofmt
- Rust: clippy, rustfmt

#### Scenario: Detect type checkers

**Given** sense command is analyzing project
**When** checking for type checkers
**Then** the system SHALL detect:
- Python: mypy, pyright, pyre
- TypeScript: tsc
- Flow: flow

#### Scenario: Detect test runners

**Given** sense command is analyzing project
**When** checking for test tools
**Then** the system SHALL detect:
- Python: pytest, unittest, nose
- JavaScript: jest, vitest, mocha
- Go: go test
- Rust: cargo test

#### Scenario: Detect coverage tools

**Given** sense command is analyzing project
**When** checking for coverage
**Then** the system SHALL detect:
- Python: coverage.py, pytest-cov
- JavaScript: nyc, c8, istanbul
- Go: go test -cover

---

### Requirement: Configuration Generation

The system SHALL generate quality configuration based on detected tools.

**ID**: SENSE-003 | **Priority**: P0 (Critical) | **Category**: Core Functionality

#### Scenario: Generate quality config

**Given** sense detects quality tools
**When** generating configuration
**Then** the system SHALL create `quality_config` section in `.synapse/config.json`:
- Tool name
- Command to execute tool
- Expected exit code for success
- Any required arguments

#### Scenario: Suggest default thresholds

**Given** generating quality configuration
**When** coverage tool is detected
**Then** the system SHALL:
- Suggest default coverage threshold (e.g., 80%)
- Allow user to customize threshold
- Include threshold in quality config

---

### Requirement: Third-Party Workflow Detection

The system SHALL detect other workflow systems in use.

**ID**: SENSE-004 | **Priority**: P2 (Medium) | **Category**: Core Functionality

#### Scenario: Detect competing workflow systems

**Given** sense command is analyzing project
**When** scanning for workflow systems
**Then** the system SHALL detect:
- Other AI workflow tools
- Custom Claude Code configurations
- Alternative task management systems

#### Scenario: Warn about conflicts

**Given** conflicting system is detected
**When** sense command reports
**Then** the system SHALL:
- Display warning about potential conflicts
- Suggest reviewing configurations
- NOT block Synapse usage

---

### Requirement: Configuration Update

The system SHALL update `.synapse/config.json` with findings.

**ID**: SENSE-005 | **Priority**: P0 (Critical) | **Category**: Core Functionality

#### Scenario: Write quality config atomically

**Given** sense command completes analysis
**When** writing to config.json
**Then** the system SHALL:
- Read existing config.json
- Add or update `quality_config` section
- Preserve all other configuration
- Write atomically (temp file + rename)

#### Scenario: Backup before update

**Given** config.json will be modified
**When** sense command runs
**Then** the system SHALL:
- Create backup of current config.json
- Allow restoration if update fails

---

### Requirement: Sense Command Output

The system SHALL provide clear, actionable output.

**ID**: SENSE-006 | **Priority**: P1 (High) | **Category**: User Experience

#### Scenario: Display detected configuration

**Given** sense command completes
**When** displaying results
**Then** the system SHALL show:
- Project type and language
- Detected quality tools with versions
- Generated configuration
- Location of updated config file

#### Scenario: Provide recommendations

**Given** sense detects missing quality tools
**When** displaying results
**Then** the system SHALL:
- Recommend tools to install
- Provide installation commands
- Suggest configuration options

---

### Requirement: Incremental Updates

The system SHALL support re-running sense to update configuration.

**ID**: SENSE-007 | **Priority**: P2 (Medium) | **Category**: Core Functionality

#### Scenario: Update existing configuration

**Given** quality config already exists
**When** user runs sense command again
**Then** the system SHALL:
- Detect new tools since last run
- Update configuration with new findings
- Preserve manual customizations where possible
- Report what changed

#### Scenario: Handle tool removal

**Given** quality tool was previously detected
**When** tool is no longer available
**Then** sense SHALL:
- Detect tool removal
- Warn user about missing tool
- Suggest removing from configuration
