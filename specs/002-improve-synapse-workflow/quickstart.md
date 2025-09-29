# Quickstart: Synapse Workflow UX Improvements

**Feature**: Template Integration and Slash Command System
**Duration**: 5-10 minutes
**Prerequisites**: Existing project with or without CLAUDE.md

## Overview

This quickstart demonstrates the enhanced Synapse workflow experience with seamless CLAUDE.md integration and intuitive slash commands. You'll learn how to integrate Synapse without losing existing Claude Code configurations and how to use the new explicit agent commands.

## Scenario 1: Fresh Project Setup

### Step 1: Initialize Synapse
```bash
# Initialize Synapse in a new project
synapse init --project-name "My Project"
```

**Expected Outcome**:
- Creates `.synapse/` workflow directory
- Generates CLAUDE.md with Synapse agents and commands
- Installs slash commands: `/synapse:plan`, `/synapse:implement`, `/synapse:review`
- Installs agent commands: `/synapse:dev`, `/synapse:audit`, `/synapse:dispatch`

**Verification**:
```bash
# Check created files
ls -la .claude/commands/
ls -la .synapse/
cat CLAUDE.md | head -20
```

### Step 2: Use Workflow Commands
Open your project in Claude Code and try the new commands:

```
/synapse:plan "Add user authentication to my web app"
```

**Expected Outcome**:
- DISPATCHER agent analyzes the request
- Creates structured task breakdown
- Updates workflow state in `.synapse/workflow_state.json`

```
/synapse:implement
```

**Expected Outcome**:
- DEV agent begins implementation based on planned tasks
- Shows progress through task log entries
- Maintains code quality standards

```
/synapse:review
```

**Expected Outcome**:
- AUDITOR agent verifies completed work
- Generates verification report
- Provides feedback and recommendations

## Scenario 2: Existing Project with CLAUDE.md

### Step 1: Backup and Analyze
```bash
# Check existing CLAUDE.md
cat CLAUDE.md

# Initialize Synapse with existing file
synapse init --project-name "Existing Project"
```

**Expected Outcome**:
- Detects existing CLAUDE.md file
- Creates backup at `CLAUDE.md.backup.YYYY-MM-DD`
- Preserves user content in designated template slots
- Integrates Synapse functionality seamlessly

**Verification**:
```bash
# Verify backup was created
ls -la CLAUDE.md*

# Check that user content was preserved
diff CLAUDE.md.backup.* CLAUDE.md | grep -A5 -B5 "user_context"
```

### Step 2: Verify Content Preservation
Open the new CLAUDE.md and verify:
- Your original project context is preserved
- Your custom instructions remain intact
- Synapse agents and commands are added
- Template structure is clean and organized

### Step 3: Handle Command Conflicts
If you have existing slash commands that conflict:

```bash
# Check for conflicts
ls .claude/commands/ | grep -E "(plan|implement|review)"
```

**Expected Behavior**:
- Synapse uses `/synapse:` prefix automatically
- Warns about conflicts during initialization
- Your existing commands remain unchanged
- Both command sets work independently

## Scenario 3: Direct Agent Communication

### Step 1: Communicate with DEV Agent
```
/synapse:dev "Review the authentication module and suggest improvements"
```

**Expected Outcome**:
- Direct communication with DEV agent
- Agent has full project context
- Receives specific development guidance

### Step 2: Communicate with AUDITOR Agent
```
/synapse:audit "Perform security review of the login system"
```

**Expected Outcome**:
- AUDITOR agent analyzes code for security issues
- Provides detailed security assessment
- Suggests specific improvements

### Step 3: Communicate with DISPATCHER Agent
```
/synapse:dispatch "What's the current status of all tasks?"
```

**Expected Outcome**:
- DISPATCHER provides workflow overview
- Shows task progress and agent assignments
- Identifies any blockers or issues

## Scenario 4: Migration from v1.x

### Step 1: Detect Legacy Installation
```bash
# Check for legacy CLAUDE.md structure
grep -n "Synapse Agent Workflow System" CLAUDE.md

# Check current version
cat .synapse/config.yaml | grep synapse_version
```

### Step 2: Upgrade to New UX
```bash
# Force upgrade with new template structure
synapse init --force --project-name "My Project"
```

**Expected Outcome**:
- Preserves workflow state and task logs
- Upgrades CLAUDE.md to new template structure
- Installs new slash commands with `/synapse:` prefix
- Maintains backward compatibility for existing workflows

## Troubleshooting

### Issue: Command conflicts detected
**Solution**: Synapse automatically uses `/synapse:` prefix. Check `.synapse/command_registry.json` for conflict details.

### Issue: User content not preserved
**Solution**: Check backup file and manually copy missing content to appropriate template slots in CLAUDE.md.

### Issue: Template integration failed
**Solution**:
```bash
# Restore from backup
cp CLAUDE.md.backup.YYYY-MM-DD CLAUDE.md

# Retry with manual template integration
synapse template integrate --force-backup
```

### Issue: Agents not responding correctly
**Solution**: Verify agent context files were created correctly:
```bash
ls -la .claude/agents/
cat .claude/agents/dev.md | head -10
```

## Validation Tests

### Test 1: Template Integration
```bash
# Verify template structure
grep -c "{{{ user_" CLAUDE.md  # Should be 0 (slots filled)
grep -c "# Synapse Agent" CLAUDE.md  # Should be 1
```

### Test 2: Command Installation
```bash
# Verify all commands installed
ls .claude/commands/ | grep synapse | wc -l  # Should be 6
```

### Test 3: Content Preservation
```bash
# Verify user content preserved (assuming you had custom content)
grep -i "your custom content" CLAUDE.md  # Should find your content
```

### Test 4: Workflow Functionality
In Claude Code, run:
```
/status
```
Should show Synapse workflow system is active and agents are available.

## Success Criteria

✅ **Template Integration**: Existing CLAUDE.md content preserved and integrated
✅ **Command Installation**: All 6 Synapse commands installed with `/synapse:` prefix
✅ **Conflict Resolution**: No naming conflicts with existing commands
✅ **Agent Communication**: Direct agent communication works through slash commands
✅ **Workflow Functionality**: Planning, implementation, and review workflows operational
✅ **Backward Compatibility**: Existing Synapse functionality preserved

## Next Steps

After completing this quickstart:
1. Explore advanced workflow patterns with multiple agents
2. Customize agent behavior through configuration
3. Integrate Synapse with your development workflow
4. Set up project-specific agent rules and preferences

## Performance Expectations

- **Template Integration**: <500ms for typical CLAUDE.md files
- **Command Installation**: <1s for all 6 commands
- **Agent Response**: <2s for initial agent invocation
- **Workflow Updates**: <100ms for status updates

This quickstart demonstrates how Synapse's enhanced UX provides seamless integration while maintaining full functionality and user control.