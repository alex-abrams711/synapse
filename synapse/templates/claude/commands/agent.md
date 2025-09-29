# /agent - Manage Agent Configuration and Status

## Description
Manage individual agent configurations, status, and behavior within the Synapse workflow system. Control agent availability, settings, and monitor agent-specific activities.

## Usage
```
/agent status
/agent <agent-id> status
/agent <agent-id> enable
/agent <agent-id> disable
/agent <agent-id> config [--set key=value]
/agent <agent-id> rules [--add rule] [--remove rule]
/agent <agent-id> workload
/agent <agent-id> history [--lines N]
```

## Implementation
Comprehensive agent management interface that provides control over individual agent behavior and configuration.

### Data Sources
- `{{workflow_dir}}/config.yaml` - Agent configurations
- `{{workflow_dir}}/task_log.json` - Agent activity history
- `{{workflow_dir}}/workflow_state.json` - Current agent assignments
- `.claude/agents/<agent-id>.md` - Agent context files

## Subcommands

### /agent status
Show overview of all agents in the system.

**Output format:**
```
🤖 Agent Status Overview

DEV Agent:
├─ Status: ✓ Enabled
├─ Current Task: task-abc123 (Implement user auth)
├─ Workload: 2 pending, 1 in progress
├─ Last Activity: 2025-01-27 10:30:15
├─ Context File: .claude/agents/dev.md
└─ Custom Rules: 2 active

AUDITOR Agent:
├─ Status: ✓ Enabled
├─ Current Task: None
├─ Workload: 1 pending verification
├─ Last Activity: 2025-01-27 10:25:03
├─ Context File: .claude/agents/auditor.md
└─ Custom Rules: 1 active

DISPATCHER Agent:
├─ Status: ✓ Enabled
├─ Current Task: Coordinating workflow
├─ Workload: Managing 3 active tasks
├─ Last Activity: 2025-01-27 10:30:20
├─ Context File: .claude/agents/dispatcher.md
└─ Custom Rules: None

📊 System Summary:
  Total Agents: 3
  Active: 3
  Busy: 2
  Available: 1
```

### /agent <agent-id> status
Show detailed status for a specific agent.

**Example: `/agent dev status`**
```
🤖 DEV Agent - Detailed Status

Configuration:
├─ Agent ID: dev
├─ Status: ✓ Enabled
├─ Context File: .claude/agents/dev.md
├─ Last Updated: 2025-01-27 09:00:00
└─ Custom Prompt: None

Current Assignment:
├─ Task: task-abc123
├─ Description: Implement user authentication system
├─ Status: IN_PROGRESS
├─ Started: 10:15:00
├─ Progress: 3/5 subtasks completed
├─ Est. Completion: 11:15:00
└─ Next Action: Write unit tests for auth flow

Workload:
├─ Active Tasks: 1
├─ Pending Tasks: 2
├─ Completed Today: 4
├─ Failed Tasks: 0
└─ Average Task Time: 45 minutes

Custom Rules:
1. "Use TypeScript for all new components"
2. "Ensure 90% test coverage minimum"

Recent Activity (Last 5 actions):
[10:30] Completed subtask: Password hashing implementation
[10:20] Started subtask: Unit test implementation
[10:15] Task assigned: task-abc123
[10:10] Completed task: task-xyz789 (Login form styling)
[10:05] Verification passed: task-def456
```

### /agent <agent-id> enable/disable
Enable or disable specific agents.

**Enable agent:**
```
/agent dev enable
✓ DEV agent enabled successfully
  - Agent will accept new task assignments
  - Context file reloaded: .claude/agents/dev.md
  - Updated configuration saved
```

**Disable agent:**
```
/agent auditor disable
⚠ AUDITOR agent disabled
  - Agent will not accept new tasks
  - Current tasks will continue until completion
  - Verification queue will be paused
  - Re-enable with: /agent auditor enable
```

### /agent <agent-id> config
View and modify agent configuration settings.

**View configuration:**
```
/agent dev config

📋 DEV Agent Configuration:
  agent_id: dev
  enabled: true
  context_file: .claude/agents/dev.md
  custom_prompt: null
  custom_rules:
    - "Use TypeScript for all new components"
    - "Ensure 90% test coverage minimum"
```

**Set configuration values:**
```
/agent dev config --set custom_prompt="Focus on security best practices"
✓ Updated custom_prompt for DEV agent
  - Configuration saved to {{workflow_dir}}/config.yaml
  - Agent context will be updated on next task assignment
```

### /agent <agent-id> rules
Manage custom rules for specific agents.

**Add custom rule:**
```
/agent dev rules --add "Follow company coding standards from docs/coding-style.md"
✓ Added custom rule to DEV agent
  - Rule count: 3
  - Configuration updated
```

**Remove custom rule:**
```
/agent dev rules --remove "Use TypeScript for all new components"
✓ Removed custom rule from DEV agent
  - Rule count: 2
  - Configuration updated
```

**List all rules:**
```
/agent dev rules

📜 DEV Agent Custom Rules:
1. "Ensure 90% test coverage minimum"
2. "Follow company coding standards from docs/coding-style.md"

Note: These rules supplement the base agent behavior defined in .claude/agents/dev.md
```

### /agent <agent-id> workload
Analyze agent workload and performance metrics.

**Example: `/agent dev workload`**
```
📊 DEV Agent - Workload Analysis

Current Load:
├─ Active Tasks: 1
├─ Pending Queue: 2
├─ Estimated Completion: 2h 15m
└─ Capacity Utilization: 75%

Task Distribution (Last 7 days):
├─ CODING: 12 tasks (60%)
├─ REFACTORING: 5 tasks (25%)
├─ TESTING: 3 tasks (15%)
└─ Total: 20 tasks completed

Performance Metrics:
├─ Average Task Duration: 45 minutes
├─ Success Rate: 95% (19/20)
├─ First-Pass Quality: 85%
├─ Rework Required: 15%
└─ Verification Pass Rate: 90%

Efficiency Indicators:
✓ Task completion rate: On target
✓ Quality metrics: Above average
⚠ Rework rate: Slightly elevated
✓ Response time: Excellent

Recommendations:
- Consider additional code review before task completion
- Focus on edge case testing to reduce rework
- Current workload is sustainable
```

### /agent <agent-id> history
View agent activity history with filtering options.

**Example: `/agent auditor history --lines 5`**
```
📋 AUDITOR Agent - Activity History (Last 5 entries)

[10:25:33] ✓ VERIFICATION_COMPLETED │ task-abc123
  │ Overall status: PASSED
  │ Findings: 5 criteria verified, all passed
  │ Duration: 8 minutes

[10:15:12] 🔍 VERIFICATION_STARTED │ task-abc123
  │ Task: Implement user authentication
  │ Criteria: 5 acceptance criteria to verify
  │ Estimated time: 10 minutes

[09:45:22] ✓ VERIFICATION_COMPLETED │ task-xyz789
  │ Overall status: FAILED
  │ Findings: 3/5 criteria passed, 2 failed
  │ Rework required: Unit test coverage insufficient

[09:30:15] 🔍 VERIFICATION_STARTED │ task-xyz789
  │ Task: Login form styling improvements
  │ Criteria: 5 acceptance criteria to verify
  │ Estimated time: 15 minutes

[09:20:08] ✓ VERIFICATION_COMPLETED │ task-def456
  │ Overall status: PASSED
  │ Findings: 3 criteria verified, all passed
  │ Duration: 5 minutes
```

## Error Handling

### Invalid Agent ID
```
❌ Error: Agent 'unknown' not found
💡 Available agents: dev, auditor, dispatcher
   Use: /agent status to see all agents
```

### Configuration Conflicts
```
❌ Error: Cannot disable DISPATCHER agent while workflow is active
💡 Pause workflow first: /workflow pause
   Then retry: /agent dispatcher disable
```

### Permission Issues
```
❌ Error: Cannot update agent configuration
💡 Check file permissions on {{workflow_dir}}/config.yaml
   Or run: /validate --fix
```

## Security Considerations
- Validate agent IDs to prevent injection attacks
- Ensure proper access controls on configuration files
- Sanitize custom rule content
- Log all configuration changes for audit purposes

## Performance Impact
- Cache agent status data to reduce file system access
- Optimize history queries for large task logs
- Implement efficient configuration updates
- Use streaming for large history outputs

## Integration Notes
Agent management integrates with the workflow system to ensure configuration changes take effect appropriately. Changes to agent availability affect task assignment and workflow execution.