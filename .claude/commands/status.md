# /status - Show Workflow Status

## Description
Display the current status of the Synapse agent workflow system, including active tasks, agent availability, and recent activity.

## Usage
```
/status
```

## Implementation
Read and analyze the workflow state files to provide a comprehensive status overview.

### Data Sources
- `.synapse/workflow_state.json` - Current workflow state
- `.synapse/task_log.json` - Task log with recent activities
- `.synapse/config.yaml` - Project configuration

### Status Information Displayed

#### Workflow Overview
- **Project Name**: test_project
- **Workflow Status**: IDLE | ACTIVE | PAUSED | COMPLETED | ERROR
- **Last Activity**: Timestamp of most recent agent activity
- **Active Tasks**: Count of currently in-progress tasks

#### Agent Status
For each configured agent (DEV, AUDITOR, DISPATCHER):
- **Status**: enabled/disabled
- **Current Task**: Active task assignment if any
- **Workload**: Number of assigned pending tasks
- **Last Activity**: Most recent action timestamp

#### Task Summary
- **Total Tasks**: Count of all tasks in the system
- **Pending**: Tasks waiting to be started
- **In Progress**: Currently active tasks
- **Completed**: Successfully finished tasks
- **Failed**: Tasks that require attention
- **Awaiting Verification**: Tasks waiting for AUDITOR review

#### Recent Activity
Display the last 5-10 entries from the task log showing:
- Timestamp
- Agent
- Action performed
- Brief description

### Example Output Format
```
✓ Synapse Agent Workflow System
Project: test_project
Status: ACTIVE
Last Activity: 2025-01-27 10:30:15

🤖 Agents:
  DEV      ✓ enabled  │ Current: Implement user authentication
  AUDITOR  ✓ enabled  │ Current: Review login validation
  DISPATCHER ✓ enabled │ Current: Coordinating feature rollout

📋 Tasks:
  Pending: 3    In Progress: 2    Completed: 15    Failed: 0
  Awaiting Verification: 1

🕒 Recent Activity:
  [10:30] DEV       completed  │ User login form implementation
  [10:25] AUDITOR   started    │ Verification of authentication flow
  [10:20] DISPATCHER assigned  │ Password reset feature to DEV
  [10:15] DEV       updated    │ Added input validation to login form
  [10:10] AUDITOR   completed  │ Security review of session handling
```

### Error Handling
If workflow files are missing or corrupted:
- Display appropriate error messages
- Suggest running `/validate` to diagnose issues
- Provide guidance for manual recovery if needed

### Performance Considerations
- Cache recent data to avoid repeated file reads
- Limit activity display to prevent overwhelming output
- Use efficient JSON parsing for large task logs

### Integration Notes
This command reads workflow state files directly and doesn't modify any data. It provides a read-only view of the current system status for situational awareness and debugging.