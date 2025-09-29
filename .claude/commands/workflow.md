# /workflow - Manage Workflow State

## Description
Manage and interact with the Synapse workflow state, including viewing logs, controlling workflow execution, and managing task states.

## Usage
```
/workflow status
/workflow log [--lines N] [--level LEVEL] [--agent AGENT]
/workflow pause
/workflow resume
/workflow reset
/workflow task <task-id> <action>
```

## Implementation
Provide comprehensive workflow management capabilities through various subcommands.

### Data Sources
- `.synapse/workflow_state.json` - Workflow execution state
- `.synapse/task_log.json` - Complete task activity log
- `.synapse/config.yaml` - Project configuration

## Subcommands

### /workflow status
Display detailed workflow state information.

**Output includes:**
- Current workflow status and state transitions
- Active task details with full context
- Agent assignments and workload distribution
- Workflow statistics and metrics
- Task dependency visualization

**Example:**
```
Workflow State: ACTIVE
Started: 2025-01-27 09:00:00
Duration: 1h 30m 15s

Current Task: task-abc123
├─ Type: CODING
├─ Agent: DEV
├─ Status: IN_PROGRESS
├─ Started: 10:15:00
├─ Progress: 3/5 subtasks completed
└─ Next: Input validation implementation

Queue: 2 pending tasks
├─ task-def456: Password reset feature (Priority: HIGH)
└─ task-ghi789: UI styling improvements (Priority: MEDIUM)

Dependencies:
task-def456 ← requires task-abc123 completion
```

### /workflow log
View filtered task log entries with flexible filtering options.

**Parameters:**
- `--lines N`: Show last N entries (default: 20)
- `--level LEVEL`: Filter by log level (INFO|WARNING|ERROR|DEBUG)
- `--agent AGENT`: Filter by specific agent (dev|auditor|dispatcher)

**Example:**
```
/workflow log --lines 10 --level ERROR --agent dev

📋 Task Log (Last 10 ERROR entries from DEV agent):

[10:25:33] DEV       ERROR     │ task-abc123
  │ Test failure in authentication module
  │ Files: auth/login.py, tests/test_auth.py
  │ Details: Validation logic not handling edge case for empty passwords

[09:45:12] DEV       ERROR     │ task-xyz789
  │ Import error in user management module
  │ Files: user/models.py
  │ Details: Missing dependency on datetime module
```

### /workflow pause
Pause workflow execution while preserving current state.

**Behavior:**
- Changes workflow status to PAUSED
- Preserves current task assignments
- Logs pause action with timestamp
- Agents can still complete in-progress work but won't start new tasks

### /workflow resume
Resume paused workflow execution.

**Behavior:**
- Changes workflow status from PAUSED to ACTIVE
- Resumes task assignment and execution
- Logs resume action with timestamp
- Agents can begin accepting new task assignments

### /workflow reset
Reset workflow to initial state (use with caution).

**Behavior:**
- Prompts for confirmation before proceeding
- Resets workflow status to IDLE
- Clears active task assignments
- Preserves task log history
- Maintains completed task records

**Safety measures:**
- Requires explicit confirmation
- Creates backup of current state
- Logs reset action with detailed context

### /workflow task
Manage individual task state and assignments.

**Usage:**
```
/workflow task <task-id> status     # Show detailed task status
/workflow task <task-id> assign <agent>  # Reassign task to different agent
/workflow task <task-id> priority <level>  # Change task priority
/workflow task <task-id> cancel     # Cancel pending task
/workflow task <task-id> retry      # Retry failed task
```

**Examples:**
```
/workflow task task-abc123 status
Task: task-abc123
├─ Description: Implement user authentication
├─ Type: CODING
├─ Status: IN_PROGRESS
├─ Agent: DEV
├─ Created: 2025-01-27 09:30:00
├─ Started: 09:45:00
├─ Progress: 60% (3/5 subtasks)
└─ Est. Completion: 11:15:00

Acceptance Criteria:
✓ Create login form with validation
✓ Implement password hashing
✓ Add session management
◯ Write unit tests for auth flow
◯ Update documentation

Subtasks:
[1] ✓ Login form HTML/CSS (completed 09:50)
[2] ✓ Form validation logic (completed 10:05)
[3] ✓ Password hashing implementation (completed 10:20)
[4] ◯ Unit test implementation (in progress)
[5] ◯ Documentation update (pending)
```

## Error Handling

### Common Error Scenarios
- **Workflow files corrupted**: Detect and offer recovery options
- **Invalid task IDs**: Provide helpful error messages with suggestions
- **Permission issues**: Guide user through file permission fixes
- **State conflicts**: Detect and resolve inconsistent workflow states

### Recovery Procedures
```
Error: Workflow state file corrupted
Suggested actions:
1. Run `/validate --fix` to attempt automatic repair
2. Check file permissions on .synapse/
3. Review recent task log for corruption source
4. Contact support if issue persists
```

## Security Considerations
- Validate all input parameters to prevent injection attacks
- Sanitize file paths to prevent directory traversal
- Limit log output size to prevent resource exhaustion
- Ensure proper access controls on workflow files

## Performance Optimization
- Cache frequently accessed workflow data
- Implement efficient log filtering for large task logs
- Use streaming for large log outputs
- Optimize JSON parsing for workflow state files

## Integration Notes
This command provides the primary interface for workflow management and should integrate seamlessly with other agent operations. It serves as both a monitoring tool and a control interface for workflow execution.