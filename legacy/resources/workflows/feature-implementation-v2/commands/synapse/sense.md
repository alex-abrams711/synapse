---
allowed-tools: Bash, Read, Write, Glob, Grep
description: Analyze project and generate quality configuration for stop hook validation
---

The user input can guide you on project type and non-conventional configurations. You **MUST** consider it before proceeding.

User input:

$ARGUMENTS

# Quality Configuration Setup for V2 Workflow

You are tasked with analyzing the current project and adding a comprehensive quality configuration section to the Synapse config file that will be used by the **stop hook validation system**.

## V2 Workflow Architecture

This workflow uses a **stop hook continuation pattern** instead of sub-agents:
- Main agent implements features directly (no delegation to implementer/verifier agents)
- When agent tries to stop, `stop_validation.py` runs validation automatically
- If validation fails, agent is **forced to continue** (exit code 2) with specific fix instructions
- Process repeats until all quality checks pass

The stop hook validates in priority order:
1. **Build/Syntax** - Code must compile/parse without errors
2. **Tests** - All tests must pass
3. **Tasks** - Tasks marked complete must be verified
4. **Code Quality** - Linting, formatting, type checking
5. **Coverage** - Test coverage must meet thresholds

## Your Task

1. **Analyze Project Structure**:
   - Identify the project type (Node.js, Python, Rust, Go, Java, etc.)
   - If you cannot determine the project type, stop and report to user
   - Check for project-specific config (package.json, Cargo.toml, setup.py, go.mod, pom.xml, etc.)
   - If you cannot determine the project-specific config or are unfamiliar with the project type, use context7 to help identify it
   - Scan for monorepo indicators (see Monorepo Detection section below)
   - If monorepo detected, ask user to confirm project list
   - Determine whether to generate single or monorepo mode config

2. **Detect Third-Party Workflow Systems**:
   - Scan for known workflow frameworks (OpenSpec, GitHub Spec Kit)
   - Discover any tasks.md files across the project
   - Analyze directory structures for workflow patterns
   - If patterns are unclear or ambiguous, ask user for clarification
   - Handle cases where no task management system exists

3. **Discover Quality Commands**:
   - Look for lint scripts/configs (eslint, flake8, clippy, golangci-lint, etc.)
     - If the linting command shows existing warnings, mark lint level as `flexible`, otherwise `strict`
   - Find type checking tools (tsc, mypy, etc.)
   - Identify test runners (jest, pytest, cargo test, go test, etc.)
   - Look for coverage tools
     - If coverage metrics are not defined or set to zero, run coverage and set thresholds to current levels
   - Find build commands

4. **Update Synapse Configuration**:
   - Read the existing `.synapse/config.json` file
   - Add a `quality-config` section with discovered commands
   - Add a `third_party_workflows` section with detected workflow information
   - Include project-appropriate thresholds and settings
   - Add optional commands if available
   - Save the updated config.json file

## Configuration Schema

Both the `quality-config` and `third_party_workflows` sections should be added to the existing `.synapse/config.json` file.

### Single Project Mode (default)

For single projects, use this structure:

```json
{
  "synapse_version": "0.1.0",
  "initialized_at": "existing timestamp",
  "project": { "..." },
  "workflows": { "..." },
  "settings": { "..." },
  "quality-config": {
    "mode": "single",
    "projectType": "node|python|rust|go|java|generic|etc.",
    "commands": {
      "lint": "command to run linting",
      "typecheck": "command to run type checking",
      "test": "command to run tests",
      "coverage": "command to run coverage analysis",
      "build": "command to build project"
    },
    "thresholds": {
      "coverage": {
        "statements": 80,
        "branches": 80,
        "functions": 80,
        "lines": 80
      },
      "lintLevel": "strict|flexible"
    },
    "metadata": {
      "generated": "timestamp",
      "detectedFiles": ["list of key files that influenced detection"]
    }
  },
  "third_party_workflows": { "..." }
}
```

### Monorepo Mode

For monorepos with multiple sub-projects, use this structure:

```json
{
  "synapse_version": "0.1.0",
  "initialized_at": "existing timestamp",
  "project": { "..." },
  "workflows": { "..." },
  "settings": { "..." },
  "quality-config": {
    "mode": "monorepo",
    "optimization": {
      "check_affected_only": true,
      "detection_method": "uncommitted",
      "fallback_to_all": true,
      "force_check_projects": [],
      "verbose_logging": false
    },
    "projects": {
      "backend": {
        "directory": "backend/",
        "projectType": "python",
        "commands": {
          "lint": "cd backend && ruff check .",
          "typecheck": "cd backend && mypy .",
          "test": "cd backend && pytest",
          "coverage": "cd backend && pytest --cov",
          "build": "cd backend && python -m build"
        },
        "thresholds": {
          "lintLevel": "strict",
          "coverage": {
            "statements": 80,
            "branches": 75,
            "functions": 80,
            "lines": 80
          }
        },
        "metadata": {
          "generated": "timestamp",
          "detectedFiles": ["backend/pyproject.toml", "backend/setup.py"]
        }
      },
      "frontend": {
        "directory": "frontend/",
        "projectType": "node",
        "commands": {
          "lint": "cd frontend && npm run lint",
          "typecheck": "cd frontend && npm run typecheck",
          "test": "cd frontend && npm test",
          "build": "cd frontend && npm run build"
        },
        "thresholds": {
          "lintLevel": "flexible"
        },
        "metadata": {
          "generated": "timestamp",
          "detectedFiles": ["frontend/package.json"]
        }
      }
    }
  },
  "third_party_workflows": { "..." }
}
```

**Important Notes**:
- Only add the `quality-config` and `third_party_workflows` sections to the existing config.json
- Do not modify any other existing sections
- The `mode` field defaults to "single" if not specified
- All commands in monorepo mode MUST include `cd <directory> &&` prefix
- Project names are derived from their directory names (e.g., "backend", "frontend")

## Monorepo Detection

After analyzing the basic project structure, determine if this is a monorepo with multiple sub-projects.

### Detection Heuristics

Use the following approach to detect monorepo structure:

1. **Check for explicit monorepo config files** (high confidence):
   - `lerna.json` - Lerna monorepo
   - `nx.json` - Nx monorepo
   - `pnpm-workspace.yaml` - pnpm workspace
   - `turbo.json` - Turborepo
   - `rush.json` - Rush monorepo

2. **Scan for multiple project config files** (medium confidence):
   - Use Glob to find all:
     - `**/package.json` (Node.js projects)
     - `**/pyproject.toml` or `**/setup.py` (Python projects)
     - `**/Cargo.toml` (Rust projects)
     - `**/go.mod` (Go projects)
   - Exclude common non-project directories: `node_modules`, `.git`, `.venv`, `venv`, `dist`, `build`, `__pycache__`
   - If found in subdirectories (not just root), count unique parent directories

3. **Analyze findings**:
   - **0 sub-projects**: Not a monorepo (single project mode)
   - **1 sub-project**: Ambiguous - likely single project unless user confirms otherwise
   - **2+ sub-projects**: Likely monorepo - ask user to confirm

### Optimization Settings for Monorepos

**Always include the `optimization` section in monorepo configs** with these defaults:

- `check_affected_only: true` - Only run quality checks on affected projects (5-10x faster)
- `detection_method: "uncommitted"` - Git method: `uncommitted`, `since_main`, `last_commit`, `staged`, `all_changes`
- `fallback_to_all: true` - Check all projects if no changes detected (safety fallback)
- `force_check_projects: []` - Projects to always check (e.g., shared libraries)
- `verbose_logging: false` - Detailed detection output

If shared libraries detected (e.g., "shared-utils", "core", "common"), recommend adding them to `force_check_projects`.

Environment overrides: `SYNAPSE_CHECK_ALL_PROJECTS=1`, `SYNAPSE_DETECTION_METHOD=<method>`, `SYNAPSE_VERBOSE_DETECTION=1`

## Third-Party Workflow Detection

See the feature-implementation workflow's sense command for the complete third-party workflow detection process, including:
- Known framework detection (OpenSpec, GitHub Spec Kit)
- Generic tasks.md discovery
- Pattern analysis
- Task format schema generation

Use the same detection logic as feature-implementation, but note that in v2:
- The stop hook will validate task completion before allowing the session to end
- Task validation is integrated into the stop validation flow

## Final Validation Steps

### Step 1: Validate Configuration Structure

**CRITICAL**: After updating `.synapse/config.json`, you MUST validate the configuration structure:

```python
from validate_config import validate_config_for_hooks, format_validation_error

# Validate the generated config
is_valid, error_summary, detailed_issues = validate_config_for_hooks(".synapse/config.json")

if not is_valid:
    error_message = format_validation_error(error_summary, detailed_issues)
    print("\n❌ Config Validation Failed!")
    print(error_message)
    print("\n⚠️ Please fix the structural issues above and try again.")
else:
    print("\n✅ Config validation passed - configuration is properly structured")
```

### Step 2: Validate Quality Commands

**CRITICAL**: After validating the config structure, you MUST validate that the quality commands will actually fail when they should:

```python
import subprocess
import sys

# Run validation script
validation_script = "resources/workflows/feature-implementation/hooks/validate_quality_commands.py"

try:
    result = subprocess.run(
        [sys.executable, validation_script],
        cwd=".",
        timeout=180,  # Increased timeout for monorepos
        capture_output=False,  # Show output directly to user
        text=True
    )

    if result.returncode == 0:
        print("\n✅ Quality commands validation passed - all commands will properly block on issues")
    else:
        print("\n❌ Quality commands validation FAILED!")
        print("\n⚠️  CRITICAL: Your quality gates are NOT properly configured!")
        print("   Some commands will NOT block on errors, allowing broken code through.")
        print("\n   REQUIRED ACTION:")
        print("   1. Review the validation failures above")
        print("   2. Fix your quality tool configurations (lint, test, etc.)")
        print("   3. Re-run this '/synapse:sense' command")
        print("\n   The validation failures show exactly which commands are broken.")

except subprocess.TimeoutExpired:
    print("\n⚠️  Validation timed out - this may indicate an issue with your quality commands")
except Exception as e:
    print(f"\n⚠️  Could not run validation: {e}")
```

### Step 3: Explain Stop Hook Workflow

After successful configuration, explain to the user how the v2 workflow operates:

```
✅ Configuration Complete

Your project is now configured for the feature-implementation-v2 workflow.

## How the Stop Hook Validation Works:

1. **You work naturally** - Implement features without sub-agent overhead
2. **Attempt to stop** - When you try to end the session, validation runs automatically
3. **Validation runs** - The stop hook checks (in priority order):
   - Build/syntax errors
   - Test failures
   - Incomplete tasks
   - Code quality issues
   - Coverage thresholds
4. **Pass or continue** - If all checks pass, session ends. If not, you'll see specific issues to fix
5. **Forced continuation** - Exit code 1 prevents stopping until all issues resolved

## Key Benefits:

- **70-80% faster** - No sub-agent context switching
- **60-70% fewer tokens** - Single context maintained throughout
- **Better context** - Main agent keeps full understanding
- **Forced quality** - Cannot complete work until standards met

## Manual Commands Available:

- `/checkpoint` - Run validation manually without blocking (check current status)

The validation runs automatically when you attempt to stop, ensuring quality without manual intervention.
```

## Summary Report

Provide a summary of what was detected and configured:
- **Configuration mode** (single or monorepo)
- Project type(s) detected
- Quality commands configured (lint, test, coverage, etc.)
  - For monorepo: list commands per project and show optimization settings
- Third-party workflow detection results
- Task format schema generation (if applicable)
- **Config structure validation result** (PASS/FAIL)
- **Quality commands validation result** (PASS/FAIL)
- **Stop hook workflow explanation** (how v2 works differently from v1)

If you are unable to complete the task fully, explain what was done and what is missing so that the user can assist.

**Important**:
- Only include commands that actually exist in the project
- Test commands before adding them to ensure they work
- Read the existing `.synapse/config.json` file and preserve all existing sections
- Only add or update the `quality-config` and `third_party_workflows` sections
- Always perform third-party workflow detection even if no quality commands are found
- For third-party workflows, be thorough but ask for user clarification when uncertain
- Always generate task format schema v2.0 when active tasks file is found
- **Ensure the resulting JSON is valid and well-formatted**
- **Always validate the final configuration before reporting success**
- **Explain the stop hook validation workflow to the user**
