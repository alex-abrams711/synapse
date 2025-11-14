# Product Requirements Document: Synapse
## AI-First Workflow System for Claude Code Integration

**Version**: 1.1
**Date**: October 18, 2024 (Updated: November 14, 2024)
**Status**: Living Document

---

## Executive Summary

Synapse is a CLI tool that helps developers integrate AI workflow patterns with Claude Code. It provides two complementary workflows: "feature-planning" for structured task creation and "feature-implementation" for quality-gated development execution, both integrated through file copying and settings management.

### Vision Statement
To provide a minimal, reliable system for applying Claude Code workflow enhancements to development projects.

---

## Problem Statement

### Current Pain Points

1. **Manual Claude Code Setup**: Developers manually create `.claude/` directory structures and configuration files
2. **Inconsistent Task Structure**: No standardized way to create structured, quality-focused tasks
3. **Missing Workflow Reminders**: Developers forget to follow established workflow patterns
4. **Configuration Management**: Difficult to track and rollback Claude Code configuration changes

### Target Users
- Software developers using Claude Code
- Individual developers who want structured task management
- Developers who need basic workflow state tracking

---

## Solution Overview

Synapse provides:
- **Project Initialization**: Sets up basic `.synapse/` configuration
- **Workflow Application**: Copies pre-defined files to `.claude/` directory
- **Settings Management**: Merges workflow settings with existing Claude Code settings
- **State Tracking**: Maintains workflow state and enables rollback

---

## Functional Requirements

### Core Features

#### 1. **Project Initialization**
- **FR-001**: `synapse init` command creates `.synapse/` directory
- **FR-002**: Creates `config.json` with basic project metadata
- **FR-003**: Prompts user to select Claude Code as AI assistant
- **FR-004**: Copies `sense.md` command to `.synapse/commands/synapse/`
- **FR-005**: Handles directory creation errors gracefully

#### 2. **Workflow Management**
- **FR-006**: `synapse workflow list` shows available workflows (feature-planning, feature-implementation)
- **FR-007**: `synapse workflow status` displays active workflow and file tracking
- **FR-008**: `synapse workflow <name>` applies a workflow by copying files
- **FR-009**: `synapse workflow remove` removes workflow and restores backup
- **FR-010**: `--force` flag overwrites existing files during workflow application

#### 3. **File Operations**
- **FR-011**: Copy `agents/` directory from workflow to `.claude/agents/`
- **FR-012**: Copy `hooks/` directory from workflow to `.claude/hooks/`
- **FR-013**: Copy `commands/synapse/` from resources to `.claude/commands/synapse/`
- **FR-014**: Make shell scripts executable after copying
- **FR-015**: Skip existing files unless `--force` is used

#### 4. **Settings Management**
- **FR-016**: Merge workflow `settings.json` with `.claude/settings.json`
- **FR-017**: Append hooks to existing hook arrays
- **FR-018**: Create `.claude/settings.json` if it doesn't exist
- **FR-019**: Validate JSON structure after merging
- **FR-020**: Report which hooks and settings were added

#### 5. **Backup System**
- **FR-021**: Create timestamped backup of `.claude/` directory before applying workflow
- **FR-022**: Store backups in `.synapse/backups/`
- **FR-023**: Restore from latest backup when removing workflow
- **FR-024**: Clean up empty directories after restoration
- **FR-025**: Skip backup if `.claude/` doesn't exist

#### 6. **State Tracking**
- **FR-026**: Store active workflow name in `.synapse/config.json`
- **FR-027**: Track applied workflows with timestamps
- **FR-028**: Create manifest in `.synapse/workflow-manifest.json` listing copied files
- **FR-029**: Track hooks added to settings for removal
- **FR-030**: Clear workflow state when removing

### Feature Planning Workflow

#### 7. **Task Writer Agent**
- **FR-031**: Provide `task-writer.md` agent definition
- **FR-032**: Agent creates hierarchical tasks with checkbox notation
- **FR-033**: Include quality standards reminder in tasks
- **FR-034**: Add Dev/QA/User verification subtasks
- **FR-035**: Format tasks with specific markdown structure

#### 8. **Planning Workflow Hooks**
- **FR-036**: Provide `user-prompt-submit-reminder.sh` hook
- **FR-037**: Hook reminds to use task-writer agent on every user prompt
- **FR-038**: Hook integrates with Claude Code's UserPromptSubmit system
- **FR-039**: Simple bash script that outputs reminder message

### Feature Implementation Workflow

#### 9. **Implementation Agents**
- **FR-040**: Provide `implementer.md` agent definition
- **FR-041**: Implementer agent makes minimal changes for single tasks
- **FR-042**: Enforces quality gates (lint/types/tests/coverage) before completion
- **FR-043**: Provide `verifier.md` agent definition
- **FR-044**: Verifier agent performs comprehensive QA verification
- **FR-045**: Verifier uses Playwright for UI testing with screenshots

#### 10. **Quality Gate Hooks**
- **FR-046**: Provide `task_implementer_pretool_gate.py` PreToolUse hook
- **FR-047**: Pre-tool hook parses task status and validates readiness
- **FR-048**: Provide `task_implementer_quality_gate.py` PostToolUse hook
- **FR-049**: Post-tool hook runs quality checks (lint/types/tests/coverage)
- **FR-050**: Provide `task_verifier_completion.py` PostToolUse hook
- **FR-051**: Completion hook updates task status after verification
- **FR-052**: All Python hooks use `uv run` for execution

#### 11. **Advanced Hook System**
- **FR-053**: Support UserPromptSubmit, PreToolUse, and PostToolUse hooks
- **FR-054**: Python hooks load quality configuration from `.synapse/config.json`
- **FR-055**: Hooks parse and update task tracking files
- **FR-056**: Quality gate hooks prevent progression with failing tests

#### 12. **Sense Command**
- **FR-057**: Provide `/sense` slash command for Claude Code
- **FR-058**: Command analyzes project and generates quality configuration
- **FR-059**: Detects project type and existing quality tools
- **FR-060**: Updates `.synapse/config.json` with quality-config section
- **FR-061**: Scans for third-party workflow systems

---

## Technical Requirements

### Architecture
- **TR-001**: Python CLI application using argparse
- **TR-002**: Single module structure in `src/synapse_cli/`
- **TR-003**: Resources stored in `resources/` directory
- **TR-004**: JSON-based configuration files
- **TR-005**: File system operations with error handling

### Dependencies
- **TR-006**: Python 3.9+ compatibility
- **TR-007**: Standard library only (no external dependencies)
- **TR-008**: Setuptools for packaging and distribution
- **TR-009**: Entry point: `synapse = "synapse_cli:main"`

### File Structure
```
synapse/
├── src/synapse_cli/
│   ├── __init__.py          # Main CLI logic
│   └── __main__.py          # Entry point
├── resources/
│   ├── commands/synapse/
│   │   └── sense.md         # Sense command
│   ├── settings/
│   │   └── config-template.json
│   └── workflows/
│       ├── feature-planning/
│       │   ├── settings.json
│       │   ├── agents/task-writer.md
│       │   ├── hooks/user-prompt-submit-reminder.sh
│       │   └── commands/synapse/sense.md
│       └── feature-implementation/
│           ├── settings.json
│           ├── agents/
│           │   ├── implementer.md
│           │   └── verifier.md
│           ├── hooks/
│           │   ├── user-prompt-submit-reminder.sh
│           │   ├── task_implementer_pretool_gate.py
│           │   ├── task_implementer_quality_gate.py
│           │   └── task_verifier_completion.py
│           └── commands/synapse/sense.md
└── pyproject.toml
```

### Data Models

#### Config Schema
```json
{
  "synapse_version": "0.1.0",
  "initialized_at": "2025-10-18T...",
  "project": {
    "name": "project-name",
    "root_directory": "/path/to/project"
  },
  "agent": {
    "type": "claude-code",
    "description": "Claude Code AI coding assistant"
  },
  "workflows": {
    "active_workflow": "feature-planning",
    "applied_workflows": [
      {
        "name": "feature-planning",
        "applied_at": "2025-10-18T..."
      }
    ]
  },
  "settings": {
    "auto_backup": true,
    "strict_validation": true,
    "uv_required": true
  }
}
```

#### Manifest Schema
```json
{
  "workflow_name": "feature-planning",
  "applied_at": "2025-10-18T...",
  "synapse_version": "0.1.0",
  "files_copied": [
    {
      "path": ".claude/agents/task-writer.md",
      "type": "agents"
    }
  ],
  "hooks_added": [
    {
      "hook_type": "UserPromptSubmit",
      "matcher": "",
      "command": ".claude/hooks/user-prompt-submit-reminder.sh",
      "type": "command"
    }
  ],
  "settings_updated": ["hooks"]
}
```

---

## User Stories

### Primary User: Individual Developer using Claude Code

1. **Initialize Project**: As a developer, I want to run `synapse init` to set up workflow capability in my project
2. **Apply Planning Workflow**: As a developer, I want to run `synapse workflow feature-planning` to add structured task creation to my Claude Code setup
3. **Apply Implementation Workflow**: As a developer, I want to run `synapse workflow feature-implementation` to add quality-gated development execution with comprehensive QA verification
4. **View Status**: As a developer, I want to run `synapse workflow status` to see what workflow files are active
5. **Remove Workflow**: As a developer, I want to run `synapse workflow remove` to cleanly remove workflow files and restore my original setup
6. **Force Override**: As a developer, I want to use `--force` to overwrite existing files when updating workflows

---

## Success Criteria

### Must Have (MVP)
- [ ] CLI commands work as specified
- [ ] Both workflows (feature-planning, feature-implementation) can be applied and removed
- [ ] Files are correctly copied to `.claude/` directory
- [ ] Settings merge works without corrupting existing settings
- [ ] Backup/restore functionality prevents data loss
- [ ] Basic error handling for common scenarios

### Validation Criteria

#### Feature Planning Workflow
- [ ] `synapse init` creates proper directory structure
- [ ] `synapse workflow feature-planning` copies all required files
- [ ] Task-writer agent is available in Claude Code after workflow application
- [ ] User prompt submission hook reminder appears
- [ ] Sense command is available as `/sense`

#### Feature Implementation Workflow
- [ ] `synapse workflow feature-implementation` copies all required files
- [ ] Implementer and verifier agents are available in Claude Code
- [ ] PreToolUse hook validates task readiness before tool execution
- [ ] PostToolUse hooks run quality checks after tool execution
- [ ] Python hooks execute with `uv run` and parse quality configuration
- [ ] Quality gates prevent progression with failing tests
- [ ] Verifier agent uses Playwright for UI testing

#### Common Validation
- [ ] `synapse workflow remove` completely restores original state
- [ ] No data loss during workflow operations
- [ ] Workflow switching works correctly
- [ ] Both workflows can coexist with proper file management

---

## Out of Scope

### Explicitly NOT Included
- Advanced quality gate automation
- Third-party workflow system integration
- Multi-project support
- Cloud hosting or sharing
- Plugin architecture
- Enterprise features
- Advanced analytics
- Multi-language support
- Complex configuration validation
- Integration with other AI assistants

---

## Implementation Notes

### Key Implementation Details
1. **Resource Discovery**: Use `get_resources_dir()` to locate packaged resources
2. **Error Handling**: Fail gracefully with helpful error messages
3. **File Permissions**: Make `.sh` files executable after copying
4. **JSON Validation**: Validate configuration files before writing
5. **Atomic Operations**: Use backups to ensure rollback capability

### Commands Implementation
- `synapse init [directory]` - Initialize synapse in specified or current directory
- `synapse workflow list` - Show available workflows (feature-planning, feature-implementation)
- `synapse workflow status` - Show active workflow and copied files
- `synapse workflow remove` - Remove active workflow and restore backup
- `synapse workflow feature-planning [--force]` - Apply feature-planning workflow
- `synapse workflow feature-implementation [--force]` - Apply feature-implementation workflow

### Workflow Content

#### Feature Planning Workflow
- **One Agent**: task-writer.md with hierarchical task formatting requirements
- **One Hook**: user-prompt-submit-reminder.sh that outputs reminder message
- **One Command**: sense.md for project analysis
- **Settings**: Single UserPromptSubmit hook configuration

#### Feature Implementation Workflow
- **Two Agents**: implementer.md (minimal changes) and verifier.md (QA with Playwright)
- **Four Hooks**:
  - user-prompt-submit-reminder.sh (UserPromptSubmit)
  - task_implementer_pretool_gate.py (PreToolUse)
  - task_implementer_quality_gate.py (PostToolUse)
  - task_verifier_completion.py (PostToolUse)
- **One Command**: sense.md for project analysis
- **Settings**: UserPromptSubmit, PreToolUse, and PostToolUse hook configurations with `uv run` execution

---

## Conclusion

Synapse is a focused workflow system that provides two complementary Claude Code integration patterns: structured task planning and quality-gated implementation. It solves the fundamental problems of manual Claude Code configuration and inconsistent quality enforcement while maintaining simplicity and reliability.

The system's value lies in its practical approach to AI-assisted development workflows:
- **Feature Planning**: Structured task creation with mandatory quality checkpoints
- **Feature Implementation**: Quality-gated development with automated verification and comprehensive QA

Both workflows work through simple file copying and settings management, with complete rollback capabilities. The implementation workflow's quality gates and Playwright-based testing represent a meaningful step toward automated quality assurance in AI-assisted development, while the planning workflow ensures consistent task structure and tracking.

The system provides exactly what's needed for these two specific workflow patterns without additional complexity.

---

## Implementation Updates (November 2024)

The current implementation achieves the PRD vision through a simplified architecture:

**Key Features Delivered:**
- ✅ Automated quality gate enforcement (FR-046-051)
- ✅ Configuration management with rollback (FR-021-025)
- ✅ Third-party workflow integration (FR-061)
- ✅ Task structure standardization (FR-031-039)
- ✅ Workflow application system (FR-006-020)

**Additional Capabilities:**
- Multi-layer hook protection system (4 complementary hooks)
- Schema-driven task parsing (format-agnostic)
- User control over fix timing (three-category QA Status)
- Failed task tracking across sessions
- Single workflow per project (simplified model)

**Performance:**
- Hook execution: 0.2-0.5s
- Token efficiency: 60-70% optimized
- Single context usage
- Compact hook code (~400 lines)

For detailed implementation documentation, see [USER_GUIDE.md](USER_GUIDE.md) and [ARCHITECTURE.md](ARCHITECTURE.md).

---


