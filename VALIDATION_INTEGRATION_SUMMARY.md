# Config Validation Integration - Final Implementation Summary

## Overview

Config validation has been fully integrated into existing hooks and agent prompts, eliminating the need for standalone validation hooks. Validation now happens automatically at the right points in the workflow.

## Implementation Details

### 1. Integration into `implementer-pre-tool-use.py`

**Location**: `resources/workflows/feature-implementation/hooks/implementer-pre-tool-use.py`

**Changes**:
- Added import: `from validate_config import validate_config_for_hooks, format_validation_error`
- Added validation check before task state validation (fail-fast)
- Hard blocks (exit 2) if validation fails with detailed error message
- Error message directs user to run `/synapse:sense` to fix config

**Behavior**:
```python
# Before implementer runs:
1. Check if .synapse/config.json exists
2. Validate structure using validate_config_for_hooks()
3. If invalid:
   - Format error message
   - Print to stderr
   - Return JSON block decision
   - Exit with code 2 (hard block)
4. If valid:
   - Continue with task state validation
```

### 2. Integration into `implementer-post-tool-use.py`

**Location**: `resources/workflows/feature-implementation/hooks/implementer-post-tool-use.py`

**Changes**:
- Added import: `from validate_config import validate_config_for_hooks, format_validation_error`
- Modified `load_quality_config()` to validate config structure before loading
- Hard blocks (exit 2) if validation fails with detailed error message
- Error message directs user to run `/synapse:sense` to fix config

**Behavior**:
```python
# When config is loaded:
1. Check if .synapse/config.json exists
2. Validate structure using validate_config_for_hooks()
3. If invalid:
   - Format error message
   - Print to stderr
   - Return JSON block decision
   - Exit with code 2 (hard block)
4. If valid:
   - Load quality config
   - Continue with quality checks
```

### 3. Integration into `/synapse:sense` Command

**Location**: `resources/workflows/feature-implementation/commands/synapse/sense.md`

**Changes**:
- Added "Final Step: Validate Configuration" section
- Instructs sense command to validate generated config
- Requires validation result in summary report

**Process**:
```markdown
After generating config:
1. Import validation functions
2. Run validate_config_for_hooks()
3. Print validation result
4. Include in summary report (PASS/FAIL)
```

### 4. Quality Config Check in `verifier.md`

**Location**: `resources/workflows/feature-implementation/agents/verifier.md`

**Changes**:
- Added step 5: "Quality Config Check" to verification process
- Added "Quality Config Validation" section to guidelines
- Instructs verifier to check for permissive settings when functional code exists

**Checks**:
- Look for substantial application code (src/, lib/, app/ directories)
- Read `.synapse/config.json`
- Flag if no test/coverage command AND source code exists
- Flag if coverage thresholds ALL 0% AND source code exists
- Include warning in report (doesn't fail verification)
- Recommend running `/synapse:sense`

### 5. Mandatory Quality Config Task in `writer.md`

**Location**: `resources/workflows/feature-planning/agents/writer.md`

**Changes**:
- Added "MANDATORY: Quality Configuration Task" section
- Requires quality config task for initial setup/POC/MVP projects
- Task includes establishing lint, tests, coverage, and running `/synapse:sense`

**Task Template**:
```markdown
[ ] - [[Establish Quality Configuration and Testing Standards]]
  [ ] - [[Configure and verify linting tools]]
  [ ] - [[Configure and verify type checking]]
  [ ] - [[Set up testing framework and write initial smoke tests]]
  [ ] - [[Configure coverage tools and set appropriate thresholds]]
  [ ] - [[Update .synapse/config.json with accurate quality commands]]
  [ ] - [[Run '/synapse:sense' to validate and finalize quality configuration]]
  [ ] - [[Verify all quality gates pass with current codebase]]
  [ ] - Dev Status: [Not Started]
  [ ] - QA Status: [Not Started]
  [ ] - User Verification Status: [Not Started]
```

**When to include**:
- ✅ Project setup, initialize, scaffold, POC, MVP
- ✅ New application/service from scratch
- ✅ After database/build setup
- ❌ NOT for features on established codebase

### 6. Cleanup

**Removed Files**:
- `resources/workflows/feature-implementation/hooks/validate-config-pre-tool-use.py`
- `resources/workflows/feature-implementation/hooks/validate-config-post-tool-use.py`

**Kept Files**:
- `resources/workflows/feature-implementation/hooks/validate_config.py` (shared utility)
- `resources/schemas/synapse-config-schema.json` (schema definition)

**Modified Files**:
- `resources/workflows/feature-implementation/settings.json` - Removed validation hooks from PreToolUse and PostToolUse

## Validation Flow

### Before Implementation (implementer-pre-tool-use.py)

```
1. User requests implementer agent
2. implementer-pre-tool-use.py runs
3. If .synapse/config.json exists:
   → validate_config_for_hooks() runs
4. If invalid:
   - Print error to stderr
   - Return block decision JSON
   - Exit 2 (hard block)
   - User sees: "Run '/synapse:sense' to fix config"
5. If valid:
   - Continue with task state validation
   - Check blocking conditions
```

### After Implementation (implementer-post-tool-use.py)

```
1. Implementer completes work
2. implementer-post-tool-use.py runs
3. load_quality_config() called
4. → validate_config_for_hooks() runs
5. If invalid:
   - Print error to stderr
   - Return block decision JSON
   - Exit 2 (hard block)
   - User sees: "Run '/synapse:sense' to fix config"
6. If valid:
   - Continue with quality checks (lint, test, coverage, build)
```

### During Config Generation (/synapse:sense)

```
1. Sense command analyzes project
2. Generates quality-config and third_party_workflows
3. Updates .synapse/config.json
4. → validate_config_for_hooks() runs
5. Prints validation result
6. Includes in summary report:
   - Project type
   - Commands configured
   - Workflow detection
   - Validation: PASS/FAIL
```

### During Verification (verifier)

```
1. Verifier runs quality gates
2. Checks if functional source code exists
3. If yes:
   - Read .synapse/config.json
   - Check for test/coverage commands
   - Check coverage thresholds
4. If permissive settings found:
   - Add "Quality Config Warning" section to report
   - Recommend running '/synapse:sense'
   - Does NOT fail verification
```

### During Planning (writer)

```
1. Writer breaks down feature/work item
2. Detects if it's initial setup/POC/MVP
3. If yes:
   - Includes mandatory quality config task
   - Places it AFTER setup, BEFORE features
   - Task includes running '/synapse:sense'
```

## Benefits

1. **Single Source of Truth**: Validation logic in one place (`validate_config.py`)
2. **Automatic Validation**: Happens at the right workflow points without manual triggers
3. **Fail-Fast**: Pre-tool-use validation catches issues before implementer runs
4. **Defense-in-Depth**: Post-tool-use validation provides additional safety
5. **Clear Guidance**: All validation errors direct users to `/synapse:sense`
6. **No Standalone Hooks**: Simpler hook configuration
7. **Proactive Prevention**: Writer ensures quality config is set up early
8. **Continuous Monitoring**: Verifier alerts if config becomes too permissive

## Error Messages

All validation errors now show:
```
❌ Config Validation Failed

[Error description]

Required Action:
  Run '/synapse:sense' to regenerate .synapse/config.json in the correct format

The '/synapse:sense' command will:
  1. Analyze your project structure
  2. Detect quality tools and commands
  3. Generate appropriate quality thresholds
  4. Create a config compatible with quality gate hooks
```

## Testing

All existing tests still pass:
- ✅ Broken config detection (subprojects)
- ✅ Valid config acceptance
- ✅ Incomplete config rejection
- ✅ Missing commands detection
- ✅ Full validation scenarios

Run tests:
```bash
python test_validate_config.py
```

## Migration Notes

For existing projects using the old standalone validation hooks:

1. **Remove old hooks**: The standalone validation hooks are gone
2. **Update workflows**: Run `synapse workflow feature-implementation` to get updated settings.json
3. **Validation still happens**: Now integrated into implementer-post-tool-use.py
4. **No behavior change**: Validation still blocks on invalid config, just integrated differently

## Files Summary

**Created/Modified**:
1. `resources/workflows/feature-implementation/hooks/implementer-pre-tool-use.py` - Added validation (fail-fast)
2. `resources/workflows/feature-implementation/hooks/implementer-post-tool-use.py` - Integrated validation (defense-in-depth)
3. `resources/workflows/feature-implementation/commands/synapse/sense.md` - Added validation step
4. `resources/workflows/feature-implementation/agents/verifier.md` - Added quality config check
5. `resources/workflows/feature-planning/agents/writer.md` - Added mandatory quality config task
6. `resources/workflows/feature-implementation/settings.json` - Removed standalone validation hooks
7. `resources/workflows/feature-implementation/hooks/validate_config.py` - Updated error message to use `/synapse:sense`
8. `resources/workflows/feature-implementation/hooks/README.md` - Updated documentation

**Deleted**:
1. `resources/workflows/feature-implementation/hooks/validate-config-pre-tool-use.py`
2. `resources/workflows/feature-implementation/hooks/validate-config-post-tool-use.py`

**Kept** (Shared Utilities):
1. `resources/workflows/feature-implementation/hooks/validate_config.py`
2. `resources/schemas/synapse-config-schema.json`
3. `test_validate_config.py`
