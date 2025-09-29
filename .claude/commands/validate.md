# /validate - Validate Configuration and System State

## Description
Validate the Synapse project configuration, workflow state, and system integrity. Detect issues and provide automated fixes where possible.

## Usage
```
/validate
/validate --fix
/validate --component <component>
/validate --deep
```

## Implementation
Comprehensive validation system that checks all aspects of the Synapse workflow system.

### Data Sources
- `.synapse/config.yaml` - Project configuration
- `.synapse/task_log.json` - Task log integrity
- `.synapse/workflow_state.json` - Workflow state consistency
- `.claude/agents/*.md` - Agent template validity
- `.claude/commands/*.md` - Command template validity

## Validation Components

### Configuration Validation
Verify project configuration integrity:

**Config Structure:**
- Required fields present and properly typed
- Agent configurations valid and consistent
- File paths exist and are accessible
- Version compatibility checks
- YAML syntax and format validation

**Checks performed:**
```
✓ Project name is valid and non-empty
✓ Synapse version follows semantic versioning
✓ Workflow directory exists and is writable
✓ Agent configurations are properly structured
✓ Claude command definitions are valid
✓ File paths reference existing templates
```

### Workflow State Validation
Ensure workflow state consistency:

**State Integrity:**
- Workflow status transitions are valid
- Task references are consistent
- Agent assignments match configuration
- No orphaned or corrupted tasks
- Timestamp consistency and ordering

**Task Log Validation:**
- JSON format integrity
- Entry structure compliance
- Agent ID references are valid
- Action types are recognized
- Chronological ordering maintained

### Template Validation
Verify all template files are valid and accessible:

**Agent Templates:**
- Markdown format and structure
- Required sections present (Role, Capabilities, Rules)
- Variable placeholders properly formatted
- No syntax errors or malformed content

**Command Templates:**
- Proper command definition format
- Usage examples are valid
- Implementation guidance is complete
- No conflicting command names

### File System Validation
Check file system integrity:

**Directory Structure:**
- Required directories exist (`.claude/`, `.synapse/`)
- Proper permissions on workflow files
- No conflicting or duplicate files
- Template files are readable

**File Integrity:**
- All referenced files exist
- File formats are correct (JSON, YAML, Markdown)
- No corrupted or empty files
- Backup files are available if needed

## Validation Options

### Standard Validation (`/validate`)
Performs comprehensive validation of all components:

```
🔍 Synapse Project Validation

Configuration:
✓ Project structure is valid
✓ config.yaml syntax and content OK
✓ All agent configurations valid
✓ File paths and permissions OK

Workflow State:
✓ workflow_state.json is valid
✓ Task references are consistent
✓ No orphaned tasks found
✓ State transitions are valid

Templates:
✓ Agent templates (3/3) valid
✓ Command templates (4/4) valid
✓ All placeholders properly formatted
✓ No syntax errors detected

File System:
✓ Directory structure complete
✓ All required files present
✓ Permissions are correct
✓ No corruption detected

📋 Validation Summary:
  Total Checks: 47
  Passed: 47
  Failed: 0
  Warnings: 0

✅ Project validation completed successfully!
```

### Auto-Fix Mode (`/validate --fix`)
Attempts to automatically fix detected issues:

**Fixable Issues:**
- Missing directories or files
- Incorrect file permissions
- Malformed JSON structure
- Inconsistent timestamps
- Orphaned task references
- Missing template variables

**Example with fixes:**
```
🔧 Synapse Project Validation with Auto-Fix

Configuration:
✓ Project structure is valid
⚠ config.yaml missing claude_commands section → FIXED
✓ All agent configurations valid
✓ File paths and permissions OK

Workflow State:
✓ workflow_state.json is valid
⚠ Found 2 orphaned task references → FIXED
✓ State transitions are valid

Templates:
⚠ Missing workflow_dir placeholder in dev.md → FIXED
✓ Command templates (4/4) valid
✓ All placeholders properly formatted

File System:
✓ Directory structure complete
⚠ workflow_state.json permissions too restrictive → FIXED
✓ No corruption detected

📋 Validation Summary:
  Total Checks: 47
  Passed: 43
  Fixed: 4
  Failed: 0
  Warnings: 0

✅ Project validation completed with 4 automatic fixes!
```

### Component-Specific Validation (`/validate --component`)
Focus validation on specific components:

```
/validate --component config
/validate --component templates
/validate --component workflow
/validate --component filesystem
```

### Deep Validation (`/validate --deep`)
Performs extended validation including:
- Content analysis of templates
- Cross-reference validation
- Performance impact assessment
- Security vulnerability scanning
- Integration consistency checks

## Error Handling and Recovery

### Common Issues and Solutions

**Corrupted Configuration:**
```
❌ Error: config.yaml is corrupted or invalid
🔧 Suggested fixes:
  1. Run `/validate --fix` to attempt automatic repair
  2. Restore from backup: cp .synapse/config.yaml.backup .synapse/config.yaml
  3. Reinitialize: synapse init --force
```

**Missing Template Files:**
```
❌ Error: Agent template dev.md not found
🔧 Suggested fixes:
  1. Run `/validate --fix` to restore missing templates
  2. Check file permissions in .claude/agents/
  3. Verify template directory structure
```

**Workflow State Corruption:**
```
❌ Error: Workflow state contains invalid references
🔧 Suggested fixes:
  1. Run `/validate --fix` to clean invalid references
  2. Reset workflow state: /workflow reset
  3. Review recent task log for corruption source
```

### Manual Recovery Procedures
For issues that can't be automatically fixed:

1. **Backup current state** before manual intervention
2. **Identify root cause** through detailed error analysis
3. **Apply targeted fixes** based on specific issue type
4. **Re-validate** after fixes to ensure resolution
5. **Document resolution** for future reference

## Performance Considerations
- Cache validation results for repeated checks
- Implement efficient file scanning algorithms
- Limit deep validation to avoid performance impact
- Use streaming for large file validation

## Security Validation
Additional security-focused checks:
- Ensure no sensitive data in configuration files
- Validate file permissions prevent unauthorized access
- Check for potential injection vulnerabilities
- Verify template content doesn't contain malicious code

## Integration Notes
The validation system should be run regularly to maintain system health and can be integrated into CI/CD pipelines for automated quality assurance.