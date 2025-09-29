# Synapse Agent Workflow System - Quickstart Guide

## Installation

Install Synapse globally via pip:

```bash
pip install synapse-workflow
```

This makes the `synapse` command available globally on your system.

## Quick Start: Project Initialization

### 1. Initialize Your Project

Navigate to any existing project or create a new directory:

```bash
cd my-project
synapse init
```

This creates:
- `.claude/agents/` directory with Claude Code agent definitions
- `.claude/commands/` directory with Claude Code slash commands
- `.synapse/` directory with workflow state and logging
- `CLAUDE.md` context file for Claude Code

### 2. Verify Installation

Check that everything was set up correctly by opening the project in Claude Code and using the `/status` slash command:

**In Claude Code:**
```
/status
```

Output:
```
✓ Synapse Agent Workflow System
Project: my-project
Status: IDLE
Agents: 3 enabled (dev, auditor, dispatcher)
Last Activity: Project initialized
```

## Example Workflow: Submit Button Implementation

This demonstrates the complete agent workflow using Claude Code.

### 1. Project Structure After Init

```
my-project/
├── .claude/
│   ├── agents/
│   │   ├── dev.md           # DEV Claude agent
│   │   ├── auditor.md       # AUDITOR Claude agent
│   │   └── dispatcher.md    # DISPATCHER Claude agent
│   └── commands/
│       ├── status.md        # /status Claude command
│       └── workflow.md      # /workflow Claude command
├── .synapse/
│   ├── config.yaml          # Project configuration
│   ├── task_log.json        # Agent communication log
│   └── workflow_state.json  # Current workflow state
├── CLAUDE.md                # Main Claude Code context
└── [your existing files...]
```

### 2. Agent Context Files

Each agent gets a dedicated context file with role-specific prompts:

**`.claude/agents/dev.md`**:
```markdown
# DEV Agent

You are the DEV agent in a Synapse workflow system. Your role is to implement code according to specifications while maintaining quality standards.

## Capabilities
- Code implementation
- Refactoring existing code
- Writing unit tests
- Code quality assurance

## Rules
1. Break down tasks into granular subtasks before implementation
2. Complete ALL acceptance criteria
3. Maintain code quality (linting, type checking, test coverage)
4. Do NOT modify agent system code
5. Update task log with progress

## Current Task
Check .synapse/task_log.json for your assigned tasks.

## Available Commands
Use `/status` to check current workflow status.
Use `/workflow` to manage workflow state.
```

### 3. Claude Code Workflow with Slash Commands

Once initialized, Claude Code automatically understands the agent roles and has access to custom slash commands:

**In Claude Code:**

**User**: "Implement a submit button that is blue with white text and becomes disabled when clicked"

**Claude (as DISPATCHER)**: "I'll analyze this task and break it down for the DEV agent."

*Or use the slash command:*

**User**: `/status`

**Claude**: *Executes the /status command defined in .claude/commands/status.md*

*DISPATCHER creates task in task log:*
```json
{
  "timestamp": "2025-01-27T10:00:00Z",
  "agent_id": "dispatcher",
  "action": "task_assigned",
  "task_id": "task-001",
  "data": {
    "description": "Implement submit button",
    "acceptance_criteria": [
      "Button is blue with white text",
      "Button text says 'Submit'",
      "Button is disabled on click"
    ],
    "assigned_to": "dev"
  },
  "message": "Assigned UI implementation task to DEV agent"
}
```

**Claude (as DEV)**: "I'll implement this button step by step..."

*DEV agent implementation and subtask logging*

**Claude (as AUDITOR)**: "I'll verify the implementation meets all criteria..."

*AUDITOR verification and reporting*

### 4. Monitoring Progress

Track the workflow progress using Claude Code slash commands:

**In Claude Code:**
```
# Check current status
/status

# View recent activity
/workflow log --lines 20

# Validate project state
/validate

# Manage agents
/agent dev status
```

### 5. Task Log Example

The task log captures all agent interactions:

```json
{
  "workflow_id": "wf-001",
  "project_name": "my-project",
  "synapse_version": "1.0.0",
  "entries": [
    {
      "timestamp": "2025-01-27T10:00:00Z",
      "agent_id": "dispatcher",
      "action": "task_created",
      "task_id": "task-001",
      "message": "Created new implementation task",
      "data": {
        "description": "Implement submit button",
        "subtasks": [
          "Create button component",
          "Apply blue styling with white text",
          "Implement click handler",
          "Add disabled state",
          "Write unit tests"
        ]
      }
    },
    {
      "timestamp": "2025-01-27T10:05:00Z",
      "agent_id": "dev",
      "action": "subtask_completed",
      "task_id": "task-001",
      "message": "Completed button component creation",
      "data": {
        "subtask_id": "subtask-001",
        "result": "Created SubmitButton.tsx component"
      }
    },
    {
      "timestamp": "2025-01-27T10:15:00Z",
      "agent_id": "auditor",
      "action": "verification_completed",
      "task_id": "task-001",
      "message": "Verification passed - all criteria met",
      "data": {
        "overall_status": "PASSED",
        "findings": [
          {
            "criterion": "Button is blue with white text",
            "passed": true,
            "evidence": "CSS verified: background-color: blue; color: white"
          }
        ]
      }
    }
  ]
}
```

## CLI Commands Reference

### Initialize Project (Only CLI Command)
```bash
synapse init [OPTIONS]

Options:
  --project-name TEXT    Override detected project name
  --workflow-dir TEXT    Custom workflow directory (default: .synapse)
  --force               Overwrite existing configuration
```

## Claude Code Slash Commands Reference

All other functionality is accessed through Claude Code slash commands:

### Check Status
```
/status
```
Shows current workflow status and agent activity.

### Manage Workflow
```
/workflow status
/workflow log --lines 20
/workflow reset
```
View and manage workflow state.

### Validate Configuration
```
/validate
/validate --fix
```
Validate project configuration and templates.

### Manage Agents
```
/agent status
/agent dev enable
/agent auditor disable
```
View and configure agent settings.

## Integration with Claude Code

### Automatic Context Loading

Claude Code automatically reads:
1. `CLAUDE.md` - Main project context and agent overview
2. `.claude/agents/*.md` - Individual agent role definitions
3. `.claude/commands/*.md` - Custom slash command definitions
4. `.synapse/task_log.json` - Current workflow state

### Agent Role Switching

Claude Code can switch between agent roles based on task requirements:
- **DISPATCHER**: Task analysis and assignment
- **DEV**: Code implementation and testing
- **AUDITOR**: Verification and quality assurance

### State Persistence

All workflow state persists across Claude Code sessions through JSON files, enabling:
- Resuming interrupted workflows
- Tracking long-running tasks
- Maintaining audit trails
- Debugging agent interactions

## Troubleshooting

### Agent Not Responding
**In Claude Code:**
```
# Check agent status
/status

# Enable disabled agents
/agent dev enable
```

### Corrupted Configuration
```bash
# Re-initialize if needed
synapse init --force
```

**In Claude Code:**
```
# Validate and fix issues
/validate --fix
```

### Task Log Issues
**In Claude Code:**
```
# View recent errors
/workflow log --level ERROR
```

Or check the log file directly:
```bash
cat .synapse/task_log.json | jq .
```

### Claude Code Not Reading Context
Ensure these files exist and are readable:
- `CLAUDE.md` (main context)
- `.claude/agents/[agent].md` (agent contexts)
- `.claude/commands/[command].md` (slash commands)
- `.synapse/config.yaml` (configuration)

## Advanced Usage

### Custom Agent Prompts

Edit agent template files to customize behavior:

```bash
# Edit DEV agent behavior
nano .claude/agents/dev.md

# Add custom slash commands
nano .claude/commands/my-command.md

# Validate changes (in Claude Code)
/validate
```

### Workflow Configuration

Modify `.synapse/config.yaml` for project-specific settings:

```yaml
project_name: "My Custom Project"
agents:
  dev:
    enabled: true
    custom_rules:
      - "Use TypeScript for all new files"
      - "Follow company coding standards"
  auditor:
    enabled: true
    custom_rules:
      - "Require 90% test coverage"
      - "Check accessibility compliance"
```

### Multiple Projects

Each project maintains independent Synapse configurations:

```bash
cd project-a
synapse init --project-name "Project A"

cd ../project-b
synapse init --project-name "Project B"
```

## Best Practices

1. **Initialize Early**: Run `synapse init` when starting new projects or adding to existing ones
2. **Monitor Regularly**: Use `synapse status` to track workflow progress
3. **Review Logs**: Check `synapse log` after complex tasks to understand agent decisions
4. **Validate Often**: Run `synapse validate` after making configuration changes
5. **Customize Wisely**: Modify agent prompts for project-specific needs, but test thoroughly

## Next Steps

- Review [Architecture Documentation](data-model.md)
- Explore [CLI Contracts](contracts/cli-commands.yaml)
- Check [Research Findings](research.md)
- Examine [Implementation Tasks](tasks.md) (when available)