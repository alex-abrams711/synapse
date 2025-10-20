# Project Context

## Purpose

Synapse is a CLI tool that helps developers integrate AI workflow patterns with Claude Code. It provides two complementary workflows:
- **Feature Planning**: Structured task creation with quality standards and verification checkpoints
- **Feature Implementation**: Quality-gated development execution with automated verification and comprehensive QA

**Vision Statement**: To provide a minimal, reliable system for applying Claude Code workflow enhancements to development projects.

**Core Value**: Simple file copying and settings management that solves manual Claude Code configuration and inconsistent quality enforcement.

## Tech Stack

- **Language**: Python 3.9+
- **CLI Framework**: argparse (standard library)
- **Configuration**: JSON-based files
- **Packaging**: setuptools with entry point (`synapse = "synapse_cli:main"`)
- **Execution**: uv (for running Python hooks in workflows)
- **Testing** (in workflows): Playwright for UI verification
- **Dependencies**: Standard library only - zero external dependencies for core CLI

## Project Conventions

### Code Style

- **Module Structure**: Single module in `src/synapse_cli/`
  - `__init__.py` - Main CLI logic
  - `__main__.py` - Entry point
- **Naming Conventions**: Snake_case for Python files and functions
- **File Organization**: Resources stored in `resources/` directory with clear subdirectory structure
- **Error Handling**: Graceful failure with helpful error messages
- **Validation**: JSON structure validation before writing files

### Architecture Patterns

- **CLI Architecture**: Command-based structure using argparse
  - `synapse init [directory]` - Initialize project
  - `synapse workflow list/status/remove` - Workflow management
  - `synapse workflow <name> [--force]` - Apply workflows

- **File Operations Pattern**: Copy files from `resources/workflows/<name>/` to `.claude/`
  - Agents: `resources/.../agents/*.md` → `.claude/agents/`
  - Hooks: `resources/.../hooks/*` → `.claude/hooks/`
  - Commands: `resources/.../commands/synapse/*` → `.claude/commands/synapse/`
  - Make shell scripts executable after copying

- **Settings Merge Pattern**: Deep merge workflow `settings.json` with `.claude/settings.json`
  - Append hooks to existing hook arrays (no overwrites)
  - Create settings file if it doesn't exist
  - Validate JSON after merging

- **Backup/Restore Pattern**: Atomic operations with rollback capability
  - Create timestamped backup in `.synapse/backups/` before changes
  - Store manifest of all changes in `.synapse/workflow-manifest.json`
  - Restore from latest backup when removing workflow
  - Clean up empty directories after restoration

- **State Tracking Pattern**: Maintain workflow state in `.synapse/config.json`
  - Active workflow name
  - Applied workflows with timestamps
  - Files copied with types
  - Hooks added with configurations

### Testing Strategy

- **Quality Gates** (enforced by implementation workflow):
  - Linting validation
  - Type checking
  - Unit/integration tests
  - Code coverage thresholds

- **Testing Approach**:
  - Comprehensive integration testing for CLI commands
  - UI testing with Playwright (verifier agent workflow)
  - Quality configuration loaded from `.synapse/config.json`
  - Hooks prevent progression with failing tests

- **Validation Layers**:
  - PreToolUse hooks: Validate task readiness before execution
  - PostToolUse hooks: Run quality checks after tool execution
  - Verifier agent: Comprehensive QA with Dev/QA/User verification

### Git Workflow

- **Commit Conventions**: Conventional Commits format
  - `feat:` - New features
  - `fix:` - Bug fixes
  - Example: `feat: implement Synapse Agent Workflow System POC`

- **Branching**: Feature branches for development work
- **Main Branch**: Standard main/master (detected automatically for PRs)

## Domain Context

### Claude Code Integration

Synapse integrates deeply with Claude Code's configuration system:
- **`.claude/` directory**: Standard location for Claude Code configuration
- **Agents**: Markdown files defining specialized AI behaviors
- **Hooks**: Scripts that execute on Claude Code events (UserPromptSubmit, PreToolUse, PostToolUse)
- **Slash Commands**: Custom commands available in Claude Code via `/command-name`
- **Settings.json**: Configuration file for hooks and other Claude Code settings

### Workflow System Concepts

- **Feature Planning Workflow**: Task-writer agent + user prompt reminders + sense command
- **Feature Implementation Workflow**: Implementer/verifier agents + quality gate hooks + sense command
- **Quality-Gated Development**: Automated enforcement of quality standards before task completion
- **Hierarchical Task Tracking**: Checkbox-based task notation with Dev/QA/User verification subtasks

### Task Management Patterns

- Structured markdown tasks with specific formatting requirements
- Quality standards reminder embedded in task creation
- Minimal changes per task (implementer agent)
- Comprehensive QA verification (verifier agent with Playwright)

## Important Constraints

### Technical Constraints

- **Python Version**: Must maintain Python 3.9+ compatibility
- **Dependencies**: Standard library only for core CLI (no external deps)
- **uv Required**: Python hooks execute via `uv run` (workflow constraint)
- **File Permissions**: Shell scripts must be executable after copying
- **JSON Validation**: All JSON files must be valid before writing

### Safety Constraints

- **No Data Loss**: Backup/restore must prevent any data loss
- **Atomic Operations**: Use backups to ensure complete rollback capability
- **Settings Integrity**: Must not corrupt existing `.claude/settings.json`
- **Clean Removal**: Workflow removal must completely restore original state
- **Conflict Handling**: Skip existing files unless `--force` flag is used

### Operational Constraints

- **Single Module**: Keep CLI in single module structure for simplicity
- **Resource Discovery**: Use `get_resources_dir()` to locate packaged resources
- **Error Messages**: All failures must have helpful, actionable error messages
- **State Consistency**: Workflow state must stay synchronized with filesystem

## External Dependencies

### Required External Tools

- **Claude Code**: AI coding assistant that Synapse configures and enhances
  - Required for: All workflow functionality
  - Integration point: `.claude/` directory structure

- **uv**: Python package/script runner
  - Required for: Executing Python hooks in implementation workflow
  - Used in: PreToolUse and PostToolUse hook execution

### Optional Testing Tools

- **Playwright**: Browser automation for UI testing
  - Required for: Verifier agent in implementation workflow
  - Used in: Comprehensive QA verification with screenshots

- **Project-Specific Quality Tools**: Detected by `/sense` command
  - Linters (e.g., ruff, pylint, eslint)
  - Type checkers (e.g., mypy, pyright, tsc)
  - Test runners (e.g., pytest, jest, vitest)
  - Coverage tools (e.g., coverage.py, nyc)

## Technical Deep Dive

### uv: Python Project Management and Script Execution

**Why uv**: Synapse uses uv as the execution engine for Python-based Claude Code hooks because it provides isolated, reproducible environments without requiring complex configuration.

**Key Capabilities Used:**
- **Script Execution with `uv run`**: Hooks execute via `uv run <script>.py`, which automatically:
  - Creates isolated virtual environments
  - Installs dependencies defined in inline metadata (PEP 723)
  - Manages Python version requirements
  - Provides consistent execution across different projects

- **Inline Script Dependencies (PEP 723)**: Python hooks can declare dependencies directly in the script:
  ```python
  # /// script
  # requires-python = ">=3.9"
  # dependencies = [
  #   "requests>=2.31",
  # ]
  # ///
  ```

- **Performance**: uv is written in Rust and is 10-100x faster than traditional tools (pip, poetry), making hook execution nearly instantaneous

- **Zero Configuration**: Unlike virtual environment managers, uv requires no setup - just `uv run script.py` works out of the box

**Implementation Details:**
- Hooks in `.claude/hooks/` are executed as: `uv run .claude/hooks/quality_check.py`
- Each hook runs in its own isolated environment based on inline metadata
- uv automatically caches environments for fast subsequent runs
- The `--no-project` flag can skip project dependency installation for standalone scripts

### Playwright: Browser Automation for Comprehensive Testing

**Why Playwright**: The verifier agent uses Playwright for comprehensive UI/UX verification because it provides reliable, cross-browser automation with rich debugging capabilities.

**Key Capabilities Used:**
- **Synchronous API for Testing**: Uses `playwright.sync_api` for straightforward test scripts:
  ```python
  from playwright.sync_api import sync_playwright

  with sync_playwright() as p:
      browser = p.chromium.launch(headless=True)
      page = browser.new_page()
      page.goto('http://localhost:3000')
      page.screenshot(path='verification.png', full_page=True)
      browser.close()
  ```

- **Full-Page Screenshots**: Captures complete application state for verification:
  - `page.screenshot(path='screenshot.png', full_page=True)` - Entire scrollable page
  - `page.locator('.component').screenshot(path='element.png')` - Specific elements
  - Multiple formats supported (PNG, JPEG with quality settings)

- **Cross-Browser Testing**: Supports Chromium, Firefox, and WebKit for comprehensive coverage

- **Rich Interaction API**: Click, type, hover, drag-and-drop, form filling, JavaScript execution

- **Browser Contexts**: Isolated sessions with custom settings (viewport, user agent, cookies, permissions)

**Implementation Details:**
- Verifier agent launches browser in headless mode for automated testing
- Screenshots stored for Dev/QA/User verification checkpoints
- Can test responsive designs by setting custom viewport sizes
- Supports authentication state persistence for testing protected pages
- Integrates with pytest for structured test execution via `uv run -m pytest`

### setuptools: Package Distribution and CLI Entry Points

**Why setuptools**: Synapse uses setuptools for standard Python packaging with a single CLI entry point that makes the tool globally accessible.

**Key Capabilities Used:**
- **Entry Points**: Defines the `synapse` command as a console script:
  ```python
  setup(
      name="synapse-cli",
      entry_points={
          "console_scripts": [
              "synapse=synapse_cli:main",
          ],
      },
  )
  ```

- **Package Resource Discovery**: Uses `pkg_resources` or `importlib.resources` to locate bundled workflow files:
  ```python
  import pkg_resources
  resources_dir = pkg_resources.resource_filename('synapse_cli', 'resources')
  ```

- **Standard Installation**: Enables installation via pip/pipx:
  ```bash
  pip install synapse-cli
  pipx install synapse-cli  # Isolated global tool
  ```

**Implementation Details:**
- Entry point maps `synapse` command to `main()` function in `synapse_cli/__init__.py`
- Resources directory (`resources/workflows/`) is packaged with the distribution
- Uses `MANIFEST.in` to ensure all workflow files are included in sdist/wheel
- Supports both editable installs (`pip install -e .`) for development and standard installs for users

### argparse: Command-Line Interface Design

**Why argparse**: Part of Python standard library (zero dependencies), provides structured command parsing with automatic help generation.

**Implementation Pattern:**
```python
import argparse

parser = argparse.ArgumentParser(prog='synapse')
subparsers = parser.add_subparsers(dest='command')

# synapse init [directory]
init_parser = subparsers.add_parser('init')
init_parser.add_argument('directory', nargs='?', default='.')

# synapse workflow <name> [--force]
workflow_parser = subparsers.add_parser('workflow')
workflow_parser.add_argument('action', choices=['list', 'status', 'remove', '<name>'])
workflow_parser.add_argument('--force', action='store_true')
```

**Benefits:**
- Automatic `--help` generation
- Type validation and conversion
- Positional and optional arguments
- Subcommand structure for organized CLI
- Error messages for invalid usage

## Technology Integration Patterns

### Hook Execution Flow

1. **Claude Code Event Trigger**: UserPromptSubmit, PreToolUse, or PostToolUse event occurs
2. **Hook Configuration**: `.claude/settings.json` specifies which script to run:
   ```json
   {
     "hooks": {
       "postToolUse": [
         {
           "command": "uv run .claude/hooks/quality_gate.py"
         }
       ]
     }
   }
   ```
3. **uv Execution**: uv creates isolated environment, installs dependencies, runs script
4. **Exit Code Handling**: Non-zero exit code blocks Claude Code from proceeding
5. **Output Display**: Script stdout/stderr shown to user for feedback

### Workflow Application Process

1. **Resource Discovery**: `get_resources_dir()` locates packaged workflow files
2. **Backup Creation**: Timestamped backup in `.synapse/backups/YYYYMMDD_HHMMSS/`
3. **File Operations**: Copy agents, hooks, commands to `.claude/` with correct permissions
4. **Settings Merge**: Deep merge workflow settings into `.claude/settings.json`
5. **State Tracking**: Update `.synapse/config.json` with applied workflow metadata
6. **Rollback on Failure**: Restore from backup if any operation fails

### Verification Workflow Integration

1. **Implementer Agent Completion**: Minimal changes implemented for single task
2. **Hook Trigger**: PostToolUse hook runs quality checks (linting, types, tests)
3. **Verifier Agent Activation**: If checks pass, comprehensive QA begins
4. **Playwright Automation**: Browser launched, application tested, screenshots captured
5. **Verification Checkpoints**: Dev verification → QA verification → User verification
6. **Task Completion**: All three checkpoints must pass before task marked complete
