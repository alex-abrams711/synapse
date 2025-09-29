# Data Model: Synapse Agent Workflow System

## Core Entities

### AgentTemplate
Represents a template for agent behavior that gets scaffolded into projects.

**Fields**:
- `id`: str - Agent identifier ("dev", "auditor", "dispatcher")
- `name`: str - Display name for the agent
- `description`: str - Agent purpose and capabilities
- `prompt_template`: str - Base prompt template for the agent
- `rules`: List[str] - Operational constraints and guidelines
- `capabilities`: List[str] - Allowed actions for this agent type
- `version`: str - Template version for compatibility

**Validation**:
- id must be lowercase alphanumeric
- prompt_template must be non-empty
- capabilities cannot be empty

### ProjectConfig
Configuration for a scaffolded project's Synapse workflow.

**Fields**:
- `project_name`: str - Human-readable project name
- `synapse_version`: str - Version of Synapse that created this config
- `workflow_dir`: str - Relative path to workflow directory (default: ".synapse")
- `agents`: Dict[str, AgentConfig] - Agent-specific configurations
- `task_log_path`: str - Path to task log file relative to workflow_dir
- `created_at`: datetime - Project initialization timestamp
- `last_updated`: datetime - Last configuration update

**Validation**:
- project_name must be non-empty
- synapse_version must follow semantic versioning
- workflow_dir must be relative path

### AgentConfig
Per-project configuration for a specific Claude Code agent.

**Fields**:
- `agent_id`: str - Reference to agent template
- `enabled`: bool - Whether agent is active in this project
- `custom_prompt`: Optional[str] - Project-specific prompt override
- `custom_rules`: List[str] - Additional project-specific rules
- `context_file`: str - Path to Claude agent file (e.g., ".claude/agents/dev.md")

**Validation**:
- agent_id must reference valid agent template
- context_file must be valid relative path under .claude/agents/

### Task
Unit of work within the workflow (runtime, not template).

**Fields**:
- `id`: str - Unique task identifier (UUID)
- `description`: str - Task description
- `type`: TaskType enum - CODING | REFACTORING | TESTING | VERIFICATION | ORCHESTRATION
- `status`: TaskStatus enum - PENDING | IN_PROGRESS | COMPLETED | FAILED | NEEDS_REVISION
- `assigned_agent`: str - Agent ID handling this task
- `acceptance_criteria`: List[str] - Criteria that must be met
- `subtasks`: List[Subtask] - Breakdown of work
- `created_at`: datetime - Task creation timestamp
- `updated_at`: datetime - Last status update
- `parent_task_id`: Optional[str] - For subtask hierarchy
- `metadata`: Dict[str, Any] - Extensible task-specific data

**Validation**:
- description must be non-empty
- assigned_agent must reference configured agent
- acceptance_criteria must have at least one criterion
- status transitions must follow state machine

**State Transitions**:
```
PENDING → IN_PROGRESS → COMPLETED
                     ↓     ↑
                  NEEDS_REVISION
                     ↓
                   FAILED
```

### Subtask
Granular breakdown of a Task.

**Fields**:
- `id`: str - Unique subtask identifier
- `parent_task_id`: str - Parent task reference
- `description`: str - Subtask description
- `status`: SubtaskStatus enum - PENDING | IN_PROGRESS | COMPLETED | FAILED
- `order`: int - Execution order within parent task
- `estimated_effort`: Optional[str] - Time/complexity estimate
- `actual_effort`: Optional[str] - Actual time taken
- `result`: Optional[str] - Execution result/output
- `verification_notes`: Optional[str] - AUDITOR notes

**Validation**:
- parent_task_id must reference existing task
- order must be positive integer
- description must be non-empty

### WorkflowState
Current state of the project's workflow execution.

**Fields**:
- `workflow_id`: str - Unique workflow identifier
- `project_config`: ProjectConfig - Associated project configuration
- `status`: WorkflowStatus enum - IDLE | ACTIVE | PAUSED | COMPLETED | ERROR
- `current_task_id`: Optional[str] - Currently executing task
- `task_queue`: List[str] - Queued task IDs awaiting execution
- `completed_tasks`: List[str] - Successfully completed task IDs
- `failed_tasks`: List[str] - Failed task IDs requiring attention
- `created_at`: datetime - Workflow start time
- `last_activity`: datetime - Last agent activity timestamp

**Validation**:
- project_config must be valid
- current_task_id must reference existing task if set
- status transitions must be valid

**State Transitions**:
```
IDLE → ACTIVE → COMPLETED
       ↓   ↑
     PAUSED
       ↓
     ERROR
```

### TaskLogEntry
Individual entry in the workflow task log.

**Fields**:
- `timestamp`: datetime - Entry timestamp
- `agent_id`: str - Agent creating this entry
- `action`: str - Action performed (e.g., "task_assigned", "task_completed")
- `task_id`: Optional[str] - Related task ID
- `subtask_id`: Optional[str] - Related subtask ID
- `data`: Dict[str, Any] - Action-specific structured data
- `message`: str - Human-readable description
- `log_level`: str - INFO | WARNING | ERROR | DEBUG

**Validation**:
- agent_id must reference configured agent
- action must be from allowed action set
- timestamp must be monotonically increasing within log
- message must be non-empty

### VerificationReport
Output from AUDITOR agent after verification.

**Fields**:
- `id`: str - Report identifier
- `task_id`: str - Task being verified
- `auditor_id`: str - AUDITOR agent ID
- `timestamp`: datetime - Verification timestamp
- `overall_status`: VerificationStatus enum - PASSED | FAILED | PARTIAL
- `findings`: List[Finding] - Individual verification results
- `recommendations`: List[str] - Improvement suggestions
- `retry_count`: int - Number of verification attempts
- `evidence`: Dict[str, str] - Supporting evidence (file paths, outputs)

**Validation**:
- task_id must reference completed task
- auditor_id must be AUDITOR type agent
- findings cannot be empty
- retry_count must be non-negative

### Finding
Individual verification result within a report.

**Fields**:
- `subtask_id`: str - Subtask being verified
- `criterion`: str - Acceptance criterion checked
- `passed`: bool - Whether criterion was met
- `details`: str - Verification details and reasoning
- `evidence_path`: Optional[str] - Path to supporting evidence
- `automated_check`: bool - Whether this was an automated verification

**Validation**:
- subtask_id must reference existing subtask
- criterion must be from parent task's acceptance_criteria
- details must be non-empty

## Template File Formats

### Agent Template Markdown Structure
```markdown
# {Agent Name} Agent

## Role
{Agent description and purpose}

## Capabilities
- {Capability 1}
- {Capability 2}

## Rules
1. {Rule 1}
2. {Rule 2}

## Prompt Template
{Base prompt for Claude Code to assume this agent role}

## Context Variables
- PROJECT_NAME: {description}
- WORKFLOW_DIR: {description}
```

### Task Log JSON Schema
```json
{
  "workflow_id": "string",
  "project_name": "string",
  "synapse_version": "string",
  "entries": [
    {
      "timestamp": "ISO-8601 datetime",
      "agent_id": "string",
      "action": "string",
      "task_id": "string|null",
      "data": {},
      "message": "string",
      "log_level": "INFO|WARNING|ERROR|DEBUG"
    }
  ]
}
```

### Project Configuration YAML
```yaml
project_name: "My Project"
synapse_version: "1.0.0"
workflow_dir: ".synapse"
task_log_path: "task_log.json"

agents:
  dev:
    enabled: true
    context_file: ".claude/agents/dev.md"
    custom_rules: []
  auditor:
    enabled: true
    context_file: ".claude/agents/auditor.md"
    custom_rules: []
  dispatcher:
    enabled: true
    context_file: ".claude/agents/dispatcher.md"
    custom_rules: []

claude_commands:
  status:
    enabled: true
    command_file: ".claude/commands/status.md"
  workflow:
    enabled: true
    command_file: ".claude/commands/workflow.md"
  validate:
    enabled: true
    command_file: ".claude/commands/validate.md"
  agent:
    enabled: true
    command_file: ".claude/commands/agent.md"

created_at: "2025-01-27T10:00:00Z"
last_updated: "2025-01-27T10:00:00Z"
```

## Relationships

```
ProjectConfig 1 → N AgentConfig
ProjectConfig 1 → 1 WorkflowState
WorkflowState 1 → N Task
Task 1 → N Subtask
Task 1 → N VerificationReport
VerificationReport 1 → N Finding
TaskLogEntry N → 1 Task (optional)
AgentTemplate N → N AgentConfig (through agent_id)
```

## File System Layout (After "synapse init")

```
project-root/
├── .claude/
│   ├── agents/
│   │   ├── dev.md           # DEV Claude agent
│   │   ├── auditor.md       # AUDITOR Claude agent
│   │   └── dispatcher.md    # DISPATCHER Claude agent
│   └── commands/
│       ├── status.md        # /status Claude command
│       ├── workflow.md      # /workflow Claude command
│       ├── validate.md      # /validate Claude command
│       └── agent.md         # /agent Claude command
├── .synapse/
│   ├── config.yaml          # ProjectConfig
│   ├── task_log.json        # TaskLogEntry[]
│   └── workflow_state.json  # WorkflowState
├── CLAUDE.md                # Main Claude Code context file
└── [existing project files...]
```

## Data Flow

1. **Initialization**: `synapse init` creates ProjectConfig and scaffolds agent templates
2. **Task Creation**: User or DISPATCHER creates Task with acceptance criteria
3. **Task Assignment**: DISPATCHER assigns Task to appropriate agent via TaskLogEntry
4. **Execution**: Agent updates Task status and creates Subtasks via TaskLogEntry
5. **Verification**: AUDITOR creates VerificationReport with Findings
6. **Iteration**: Failed verification creates new Task or updates existing Task
7. **Completion**: All acceptance criteria met, WorkflowState updated to COMPLETED