# Config Validation Hooks - Implementation Summary (DEPRECATED)

**⚠️ This document describes the OLD standalone validation hooks approach.**

**✅ See `VALIDATION_INTEGRATION_SUMMARY.md` for the current integrated approach.**

---

# OLD APPROACH (No Longer Used)

## Problem Statement

The `.synapse/config.json` file format was not properly validated before quality gate hooks ran, leading to structural incompatibility issues:

**Structural Incompatibility**: Config files with `subprojects` structure (from monorepo projects) were incompatible with hooks expecting flat `commands` structure, causing hooks to fail silently or behave incorrectly.

## Solution Implemented

Created a simple, schema-based config validation system with four components:

### 1. `synapse-config-schema.json` (Schema Definition)

Location: `resources/schemas/synapse-config-schema.json`

**Purpose**: Defines the expected structure of `.synapse/config.json` based on the format specified in `/sense` command documentation.

**Key Sections**:
- Required top-level fields: `synapse_version`, `project`, `workflows`, `settings`
- Optional `quality-config` section with required `commands` and `thresholds`
- Optional `third_party_workflows` section for task management detection
- Explicitly disallows `subprojects` in `quality-config`

### 2. `validate_config.py` (Validation Module)

Location: `resources/workflows/feature-implementation/hooks/validate_config.py`

**Features**:
- Structural validation against schema (detects incompatible `subprojects` structure)
- Validates required fields are present
- Validates `quality-config` structure when present
- Helpful error formatting with actionable guidance

**Key Functions**:
```python
load_config(config_path)          # Load .synapse/config.json
load_schema()                     # Load validation schema
validate_structure(config)        # Check config structure compatibility
validate_config_for_hooks()       # Comprehensive validation
format_validation_error()         # User-friendly error messages
```

### 3. `validate-config-pre-tool-use.py` (Pre-Tool Hook)

Location: `resources/workflows/feature-implementation/hooks/validate-config-pre-tool-use.py`

**Purpose**: Block implementer/verifier from starting work if config structure is invalid.

**Behavior**:
- ✅ Allows `/sense` command to pass through (escape hatch for fixing config)
- ✅ Only validates on Task tool calls for implementer/verifier agents
- ❌ Hard blocks (exit 2) if config has structural issues
- ❌ Hard blocks (exit 2) if required fields are missing
- ✅ Passes (exit 0) if config structure is valid

### 4. `validate-config-post-tool-use.py` (Post-Tool Hook)

Location: `resources/workflows/feature-implementation/hooks/validate-config-post-tool-use.py`

**Purpose**: Validate config structure after implementer makes changes.

**Behavior**:
- Runs after implementer/verifier completes work
- Re-validates config structure to ensure it remains valid
- ❌ Hard blocks if config structure became invalid
- ✅ Passes if config structure is still valid

## Integration

### Hook Execution Order

**Pre-Tool-Use Flow**:
```
1. validate-config-pre-tool-use.py   → Validates config structure
2. implementer-pre-tool-use.py       → Validates task state
3. [Implementer agent runs]
```

**Post-Tool-Use Flow**:
```
1. [Implementer agent completes]
2. validate-config-post-tool-use.py  → Validates config for new code
3. implementer-post-tool-use.py      → Runs quality checks
```

### Settings Configuration

Updated `resources/workflows/feature-implementation/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          { "command": "uv run .claude/hooks/validate-config-pre-tool-use.py" },
          { "command": "uv run .claude/hooks/implementer-pre-tool-use.py" }
        ]
      },
      {
        "matcher": "SlashCommand",
        "hooks": [
          { "command": "uv run .claude/hooks/validate-config-pre-tool-use.py" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          { "command": "uv run .claude/hooks/validate-config-post-tool-use.py" },
          { "command": "uv run .claude/hooks/implementer-post-tool-use.py" },
          { "command": "uv run .claude/hooks/verifier-post-tool-use.py" }
        ]
      }
    ]
  }
}
```

## Validation Rules

### Structural Validation (Based on Schema)
- ✅ Config must have required top-level fields: `synapse_version`, `project`, `workflows`, `settings`
- ✅ If `quality-config` exists, it must have `commands` and `thresholds` sections
- ✅ `commands` must be a flat object (NOT `subprojects`)
- ❌ Blocks if config uses monorepo `subprojects` structure
- ❌ Blocks if required fields are missing
- ❌ Blocks if `quality-config` exists but lacks required sections

## Example Scenarios

### Scenario 1: Broken Config (Subprojects Structure)

**Config**:
```json
{
  "quality-config": {
    "subprojects": {
      "backend": { "commands": {...}, "thresholds": {...} },
      "frontend": { "commands": {...}, "thresholds": {...} }
    }
  }
}
```

**Result**:
```
❌ Config Validation Failed

Config uses 'subprojects' structure which is incompatible with current hooks.

Required Action:
  Run '/sense' to regenerate .synapse/config.json in the correct format
```

### Scenario 2: Valid Config

**Config**:
```json
{
  "quality-config": {
    "commands": { "lint": "ruff check .", "test": "pytest", "coverage": "pytest --cov" },
    "thresholds": {
      "coverage": { "statements": 80, "branches": 75, "functions": 80, "lines": 80 },
      "lintLevel": "strict"
    }
  }
}
```

**Result**: ✅ Validation passes, work proceeds

## Testing

### Test Suite

Location: `test_validate_config.py`

**Tests**:
1. ✅ Broken config detection (subprojects structure)
2. ✅ Valid config acceptance (flat structure)
3. ✅ Incomplete config rejection (missing required fields)
4. ✅ Missing commands detection
5. ✅ Full validation with broken config file
6. ✅ Full validation with valid config file

**Run Tests**:
```bash
python test_validate_config.py
```

**Output**:
```
🧪 Running Config Validation Tests (Structure Only)
================================================================================
TEST 1: Broken Config (subprojects structure)
✅ Test passed: Broken config correctly identified

TEST 2: Valid Config (flat structure)
✅ Test passed: Valid config correctly accepted

TEST 3: Incomplete Config (missing required fields)
✅ Test passed: Incomplete config correctly rejected

TEST 4: Config with quality-config but missing commands
✅ Test passed: Missing commands correctly detected

TEST 5: Full Validation (broken config in temp file)
✅ Test passed: Full validation correctly identifies broken config

TEST 6: Full Validation (valid config in temp file)
✅ Test passed: Full validation accepts valid config

================================================================================
✅ ALL TESTS PASSED
================================================================================
```

## Files Created/Modified

### New Files
1. `resources/schemas/synapse-config-schema.json` - JSON schema defining config structure
2. `resources/workflows/feature-implementation/hooks/validate_config.py` - Validation module
3. `resources/workflows/feature-implementation/hooks/validate-config-pre-tool-use.py` - Pre-tool hook
4. `resources/workflows/feature-implementation/hooks/validate-config-post-tool-use.py` - Post-tool hook
5. `test_validate_config.py` - Comprehensive test suite
6. `VALIDATION_HOOKS_SUMMARY.md` (this file)

### Modified Files
1. `resources/workflows/feature-implementation/settings.json` - Added validation hooks
2. `resources/workflows/feature-implementation/hooks/README.md` - Added validation documentation

## Benefits

1. **Prevents Silent Failures**: Catches config structure incompatibilities before hooks fail
2. **Schema-Based**: Uses explicit JSON schema for clear, maintainable validation rules
3. **Simple and Focused**: Only validates structure, not content or thresholds
4. **Clear Error Messages**: Provides actionable guidance on how to fix structural issues
5. **Escape Hatch**: Always allows `/sense` command to run for fixing invalid configs
6. **Comprehensive Testing**: Full test suite covers all structural validation scenarios
7. **No False Positives**: Doesn't try to guess if thresholds are "appropriate" - just validates structure

## Next Steps

When applying this workflow to a project:

1. **Install Workflow**: `synapse workflow feature-implementation`
2. **Initialize Config**: `synapse init` (if not already done)
3. **Generate Quality Config**: Run `/sense` to create initial config
4. **Start Development**: Implementer and verifier agents will automatically validate config before/after work

If config validation fails:
1. Run `/sense` to regenerate config in correct format
2. Follow error messages for specific guidance
3. Re-attempt implementer/verifier work
