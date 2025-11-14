# Synapse

AI-first workflow system with quality gates and workflow automation for Claude Code.

## What is Synapse?

Synapse provides standardized workflows, quality gates, and automation for Claude Code projects. It includes automated quality enforcement hooks, schema-driven task parsing, and reusable workflow commands.

**Tech Stack:** Python 3.9+, Claude Code integration

**Capabilities:**
- Simplified QA verification with user-controlled fix timing
- Automated quality gate enforcement
- Schema-driven task format detection
- Multi-layer protection against bypassing quality checks
- Stop with failures - fix issues on your schedule

## Installation

**From source (current setup):**
```bash
cd /Users/aabrams/Workspace/AI/synapse
pip install -e .
```

**From PyPI (when published):**
```bash
pip install synapse
# or
uv tool install synapse
```

## Usage

**Initialize in your project:**
```bash
synapse init
```

This creates a `.synapse/` directory with:
- `config.json` - project configuration and workflow tracking

**Initialize in specific directory:**
```bash
synapse init /path/to/project
```

## Workflows

Synapse includes pre-built workflows that apply standardized configurations to your Claude Code project:

**List available workflows:**
```bash
synapse workflow list
```

**Apply a workflow:**
```bash
synapse workflow feature-implementation-v2  # QA verification with quality gates
synapse workflow feature-planning           # Task breakdown and planning
```

**Check workflow status:**
```bash
synapse workflow status
```

**Remove current workflow:**
```bash
synapse workflow remove
```

Workflows automatically configure:
- Quality gate hooks for automated verification
- Project-specific commands (like `/sense` for quality configuration)
- Settings optimized for your development workflow
- Multi-layer protection system (UserPromptSubmit, PreToolUse, PostToolUse, Stop hooks)

## Quality Configuration & Third-Party Integration

After applying a workflow, use the `/sense` command in Claude Code to analyze your project and configure quality standards:

```bash
/sense
```

The sense command provides comprehensive project analysis including:
- **Quality Configuration**: Detects linting, testing, and coverage tools and adds thresholds to `.synapse/config.json`
- **Third-Party Workflow Detection**: Automatically discovers and catalogs task management systems like:
  - **OpenSpec** (`openspec/changes/*/tasks.md`)
  - **GitHub Spec Kit** (`specs/###-feature/tasks.md`)
  - **Custom Workflows** (any `tasks.md` files across your project)

### Third-Party Workflow Integration

Synapse intelligently detects existing workflow frameworks in your project:

1. **Known Patterns**: Instantly recognizes OpenSpec and Spec Kit structures
2. **Generic Discovery**: Finds any `tasks.md` files throughout your project
3. **Smart Analysis**: Uses AI to understand unknown directory patterns
4. **Interactive Fallback**: Asks for clarification when patterns are ambiguous

Detected workflows are stored in `.synapse/config.json` under `third_party_workflow` with:
- Workflow type
- Active tasks file path
- Task format schema for parsing
- Active tasks array for tracking work in progress

This allows Synapse to work seamlessly alongside other workflow management systems while maintaining its own quality gates and verification workflows.

## Architecture

### Workflow System

Synapse uses a simplified two-stage verification approach:
- **Hooks**: Simple checkers (~400 lines) that enforce workflow rules
- **Agent**: Performs actual verification with full tool access

Synapse applies workflow-specific configurations through:
- **File Copying**: Hooks and commands from `resources/workflows/<name>/` to `.claude/`
- **Settings Merging**: Combines workflow settings.json with existing `.claude/settings.json`
- **Tracking**: Maintains workflow manifest in `.synapse/workflow-manifest.json` for precise removal
- **Backup/Restore**: Creates backups before applying workflows for safe rollback

### Configuration Schema
The `.synapse/config.json` file stores project configuration with these key sections:

```json
{
  "synapse_version": "0.1.0",
  "project": { "name": "project-name", "root_directory": "/path" },
  "workflows": {
    "active_workflow": "feature-implementation",
    "applied_workflows": [...]
  },
  "quality-config": {
    "projectType": "python|node|rust|...",
    "commands": { "test": "pytest", "lint": "flake8", ... },
    "thresholds": { "coverage": { "lines": 80 }, ... }
  },
  "third_party_workflow": {
    "type": "openspec|spec-kit|custom",
    "active_tasks_file": "tasks.md",
    "active_tasks": ["T001", "T002"],
    "task_format_schema": {
      "version": "2.0",
      "patterns": {...},
      "field_mapping": {...},
      "status_semantics": {...}
    }
  }
}
```

### Project Structure
```
.synapse/                 # Synapse configuration
├── config.json         # Project settings and workflow tracking
├── workflow-manifest.json  # Applied workflow artifacts
└── commands/synapse/sense.md  # Quality analysis command

.claude/                 # Claude Code integration (created by workflows)
├── hooks/              # Quality gate scripts (stop, pre-tool-use, post-tool-use, etc.)
├── commands/           # Additional slash commands
└── settings.json       # Claude Code hook configuration
```

That's it. Claude Code automatically detects and uses the `.synapse/` directory for enhanced AI-assisted development with quality enforcement and third-party workflow awareness.

