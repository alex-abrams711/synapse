# Synapse

AI-first workflow system with quality gates for Claude Code.

## What is Synapse?

Synapse provides workflow management for Claude Code projects, enabling you to load multiple workflows and switch between them instantly. Each workflow includes specialized AI agents, automated quality enforcement hooks, and project-specific commands tailored to different development phases (planning, implementation, etc.).

**Tech Stack:** Python 3.9+, Claude Code integration

**Key Features:**
- **Multiple workflow support**: Load and switch between workflows instantly
- **Workflow isolation**: Each workflow has its own agents, hooks, and commands
- **Fast switching**: ~100ms to change workflows (no backup/restore overhead)
- **Flexible workflow states**: Load, activate, deactivate, and unload as needed
- **Quality enforcement**: Automated hooks for testing, linting, and verification
- **Third-party integration**: Works with OpenSpec, GitHub Spec Kit, and custom task systems

## Installation

**From source:**
```bash
git clone <repository-url>
cd synapse
pip install -e .
```

**From PyPI (when published):**
```bash
pip install synapse-cli
# or
uv tool install synapse-cli
```

## Quick Start

```bash
# 1. Initialize Synapse in your project
synapse init

# 2. List available workflows
synapse workflow list

# 3. Load and activate a workflow
synapse workflow apply feature-implementation-v2

# 4. Start using Claude Code with the active workflow!
```

## Usage

**Initialize in your project:**
```bash
synapse init
```

This creates a `.synapse/` directory with:
- `config.json` - project configuration and workflow tracking

Workflows are then loaded and activated to populate `.claude/` with:
- `agents/` - AI agent definitions
- `hooks/` - quality gate scripts
- `commands/` - slash commands (like `/sense` for quality config)
- `settings.json` - Claude Code hook configuration

**Initialize in specific directory:**
```bash
synapse init /path/to/project
```

## Workflows

Synapse includes pre-built workflows that apply standardized configurations to your Claude Code project.

### Load/Switch Workflow Management

Synapse supports loading multiple workflows and switching between them instantly:

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

After loading and activating a workflow, use the `/sense` command in Claude Code to analyze your project and configure quality standards:

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
├── config.json           # Project settings and workflow tracking
└── workflows/            # Loaded workflows (copied from resources)
    ├── feature-planning/
    │   ├── agents/
    │   ├── hooks/
    │   ├── commands/
    │   └── settings.json
    └── feature-implementation-v2/
        ├── hooks/
        ├── commands/
        └── settings.json

.claude/                  # Active workflow projection (managed by Synapse)
├── agents/               # AI agent definitions (from active workflow)
├── hooks/                # Quality gate scripts (from active workflow)
├── commands/             # Slash commands (from active workflow)
└── settings.json         # Claude Code hook configuration (generated)
```

Claude Code automatically detects and uses both `.synapse/` for configuration and `.claude/` for active workflow integration, providing enhanced AI-assisted development with quality enforcement and third-party workflow awareness.

