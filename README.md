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

Synapse includes pre-built workflows that apply standardized configurations to your Claude Code project.

### New Load/Switch Model

Synapse now supports loading multiple workflows and switching between them instantly:

**List available workflows:**
```bash
synapse workflow list
```

**Load a workflow into your project:**
```bash
synapse workflow load feature-planning
synapse workflow load feature-implementation-v2
```

**Switch between loaded workflows:**
```bash
synapse workflow switch feature-planning        # Switch to planning
# ... do planning work ...
synapse workflow switch feature-implementation-v2  # Switch to implementation
# ... do implementation work ...
synapse workflow switch feature-planning        # Back to planning (instant!)
```

**Check loaded workflows:**
```bash
synapse workflow loaded    # Show all loaded workflows
synapse workflow active    # Show currently active workflow
```

**Deactivate active workflow:**
```bash
synapse workflow deactivate    # Turn off active workflow (keeps it loaded for reactivation)
```

**Unload a workflow:**
```bash
synapse workflow unload feature-planning    # Deactivate if active, then remove from project
```

**Quick apply (convenience command):**
```bash
synapse workflow apply feature-implementation-v2  # Load + switch in one command
```

### Benefits of Load/Switch Model

- **Fast switching**: ~100ms vs 2-5 seconds (no backup/restore needed)
- **Multiple workflows ready**: Load once, switch many times
- **Better for iterative development**: Planning ↔ Implementation cycles
- **Safer**: No constant backup/restore churn
- **Encourages experimentation**: Try different workflows without friction

### What Workflows Configure

Workflows automatically set up:
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

Synapse uses a load/switch architecture for managing workflows:

**Storage Structure:**
```
.synapse/
├── config.json              # Project config with loaded workflow tracking
└── workflows/               # Loaded workflows storage
    ├── feature-planning/
    └── feature-implementation-v2/

.claude/                     # Active workflow projection
├── agents/                  # Copied from active workflow
├── hooks/                   # Copied from active workflow
├── commands/                # Copied from active workflow
└── settings.json           # Generated from active workflow
```

**How it works:**
- **Load**: Copies workflow from `resources/workflows/<name>/` to `.synapse/workflows/<name>/`
- **Switch**: Clears `.claude/` subdirectories and copies from `.synapse/workflows/<active>/`
- **Settings**: Merges workflow settings with absolute paths
- **Tracking**: Maintains loaded workflows list in `.synapse/config.json`
- **Fast**: ~100ms switching (just copy, no backup/restore)

### Configuration Schema
The `.synapse/config.json` file stores project configuration with these key sections:

```json
{
  "synapse_version": "0.1.0",
  "project": { "name": "project-name", "root_directory": "/path" },
  "workflows": {
    "active_workflow": "feature-implementation-v2",
    "loaded_workflows": [
      {
        "name": "feature-planning",
        "loaded_at": "2025-11-13T14:47:16.627155",
        "version": "1.0",
        "customized": false
      },
      {
        "name": "feature-implementation-v2",
        "loaded_at": "2025-11-13T14:47:48.663359",
        "version": "2.0",
        "customized": false
      }
    ]
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

