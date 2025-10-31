# Synapse

AI-first workflow system with quality gates and sub-agent orchestration for Claude Code.

## What is Synapse?

Synapse provides standardized AI agents, quality gates, and workflow automation for Claude Code projects. It includes specialized agents for implementation and verification, automated quality enforcement hooks, and reusable workflow commands.

**Tech Stack:** Python 3.9+, Claude Code integration

**Capabilities:**
- Task implementation agent with quality standards
- Comprehensive verification agent
- Automated quality gate enforcement
- Workflow command system
- Project lifecycle hooks

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
- `agents/` - implementer.md, verifier.md
- `commands/` - synapse/sense.md (quality config setup)
- `hooks/` - quality gates, completion verification
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
synapse workflow feature-implementation  # Feature development with verification
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
- Specialized AI agents for your project type
- Quality gate hooks for automated checking
- Project-specific commands (like `/sense` for quality configuration)
- Settings optimized for your development workflow

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

Detected workflows are stored in `.synapse/config.json` under `third_party_workflows` with:
- Workflow type and confidence scores
- Active feature directory and tasks file for agent context
- User preferences for future detection

This allows Synapse to work seamlessly alongside other workflow management systems while maintaining its own quality gates and AI agent orchestration.

## Architecture

### Workflow System
Synapse applies workflow-specific configurations through:
- **File Copying**: Agents, hooks, and commands from `resources/workflows/<name>/` to `.claude/`
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
  "third_party_workflows": {
    "detected": [
      {
        "type": "openspec|spec-kit|custom",
        "detection_method": "known_pattern|llm_analysis",
        "active_feature_directory": "openspec/changes/add-auth/",
        "active_tasks_file": "openspec/changes/add-auth/tasks.md"
      }
    ]
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
├── agents/             # AI agent definitions (implementer.md, verifier.md)
├── hooks/              # Quality gate scripts
├── commands/           # Additional slash commands
└── settings.json       # Claude Code hook configuration
```

That's it. Claude Code automatically detects and uses the `.synapse/` directory for enhanced AI-assisted development with quality enforcement and third-party workflow awareness.

