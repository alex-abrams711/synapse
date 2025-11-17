---
allowed-tools: Bash, Read, Write, Glob, Grep
description: Analyze project and generate quality configuration for hooks
---

The user input can guide you on project type and non-conventional configurations. You **MUST** consider it before proceeding.

User input:

$ARGUMENTS

# Quality Configuration Setup

You are tasked with analyzing the current project and adding a comprehensive quality configuration section to the Synapse config file that will be used by the quality gate hooks.

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
   - Add a `third_party_workflow` section with detected workflow information
   - **IMPORTANT**: Only ONE workflow per project - if multiple workflows detected, ask user to choose
   - Include project-appropriate thresholds and settings
   - Add optional commands if available
   - Save the updated config.json file

## Configuration Schema

Both the `quality-config` and `third_party_workflow` sections should be added to the existing `.synapse/config.json` file.

**BREAKING CHANGE**: The config structure uses `third_party_workflow` (object) instead of `third_party_workflows` (array). Only ONE workflow per project is supported.

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
  "third_party_workflow": {
    "type": "openspec|github-spec-kit|custom",
    "active_tasks_file": "path/to/tasks.md",
    "active_tasks": [],
    "task_format_schema": {
      "version": "2.0",
      "patterns": {
        "task": "^\\[\\s*\\]\\s*-\\s*(?P<task_code>T\\d{3,})\\s+-\\s+(?P<description>(?!.*:).*)",
        "subtask": "^\\s+\\[\\s*\\]\\s*-\\s*(?P<subtask_code>T\\d{3,}-ST\\d{3,})\\s*-\\s*(?P<description>.*)",
        "status_field": "^\\s+\\[\\s*\\]\\s*-\\s*T\\d{3,}-(?P<field_code>[A-Z]{2,})\\s*-\\s*.*:\\s*\\[(?P<status_value>[^\\]]+)\\]"
      },
      "field_mapping": {
        "dev_status": "DS",
        "qa": "QA",
        "user_verification": "UV"
      },
      "status_semantics": {
        "states": {
          "dev": {
            "not_started": ["Not Started"],
            "in_progress": ["In Progress"],
            "complete": ["Complete"]
          },
          "qa": {
            "not_verified": ["Not Started"],
            "verified_success": ["Complete", "Passed"],
            "verified_failure_pattern": "^Failed - .*"
          },
          "user_verification": {
            "not_started": ["Not Started"],
            "verified": ["Verified"]
          }
        }
      }
    }
  }
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
  "third_party_workflow": {
    "type": "openspec|github-spec-kit|custom",
    "active_tasks_file": "path/to/tasks.md",
    "active_tasks": [],
    "task_format_schema": {
      "version": "2.0",
      "patterns": {
        "task": "^\\[\\s*\\]\\s*-\\s*(?P<task_code>T\\d{3,})\\s+-\\s+(?P<description>(?!.*:).*)",
        "subtask": "^\\s+\\[\\s*\\]\\s*-\\s*(?P<subtask_code>T\\d{3,}-ST\\d{3,})\\s*-\\s*(?P<description>.*)",
        "status_field": "^\\s+\\[\\s*\\]\\s*-\\s*T\\d{3,}-(?P<field_code>[A-Z]{2,})\\s*-\\s*.*:\\s*\\[(?P<status_value>[^\\]]+)\\]"
      },
      "field_mapping": {
        "dev_status": "DS",
        "qa": "QA",
        "user_verification": "UV"
      },
      "status_semantics": {
        "states": {
          "dev": {
            "not_started": ["Not Started"],
            "in_progress": ["In Progress"],
            "complete": ["Complete"]
          },
          "qa": {
            "not_verified": ["Not Started"],
            "verified_success": ["Complete", "Passed"],
            "verified_failure_pattern": "^Failed - .*"
          },
          "user_verification": {
            "not_started": ["Not Started"],
            "verified": ["Verified"]
          }
        }
      }
    }
  }
}
```

**Important Notes**:
- Only add the `quality-config` and `third_party_workflow` sections to the existing config.json
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

### Interactive Clarification

If detection confidence is low or ambiguous:

```python
print("\\n⚠️  Monorepo detection is uncertain.")
print(f"Found {len(detected_projects)} potential sub-projects:")
for name, info in detected_projects.items():
    print(f"  - {name} ({info['directory']}) - {info['type']}")

print("\\nIs this a monorepo with multiple independent projects? (Y/n): ")
# Wait for user response
```

If user confirms monorepo:
- Set `mode` to "monorepo"
- Ask user to verify the detected project list
- Generate config for each project

If user declines:
- Set `mode` to "single"
- Generate flat config for primary project only

### Project Config Generation for Monorepo Mode

For each detected project:

1. **Change to project directory**:
   ```python
   import os
   original_dir = os.getcwd()
   os.chdir(project_directory)
   ```

2. **Discover quality commands** (use same logic as single mode):
   - Look for lint configs in project directory
   - Find test runners
   - Detect build commands
   - Check coverage tools

3. **Prefix all commands with directory change**:
   ```python
   discovered_command = "ruff check ."
   final_command = f"cd {directory} && {discovered_command}"
   ```

4. **Return to root**:
   ```python
   os.chdir(original_dir)
   ```

5. **Add to projects config**:
   ```python
   quality_config["projects"][project_name] = {
       "directory": directory,
       "projectType": project_type,
       "commands": prefixed_commands,
       "thresholds": thresholds,
       "metadata": { ... }
   }
   ```

### Important Notes

- Include the `optimization` section to enable git-based change detection (only checks affected projects)
- Project names are derived from directory names (e.g., "backend/", "frontend/")
- All commands MUST include `cd <directory> &&` prefix
- Each project has independent thresholds and settings

### Optimization Settings

**Always include the `optimization` section in monorepo configs** with these defaults:

- `check_affected_only: true` - Only run quality checks on affected projects (5-10x faster)
- `detection_method: "uncommitted"` - Git method: `uncommitted`, `since_main`, `last_commit`, `staged`, `all_changes`
- `fallback_to_all: true` - Check all projects if no changes detected (safety fallback)
- `force_check_projects: []` - Projects to always check (e.g., shared libraries)
- `verbose_logging: false` - Detailed detection output

If shared libraries detected (e.g., "shared-utils", "core", "common"), recommend adding them to `force_check_projects`.

Environment overrides: `SYNAPSE_CHECK_ALL_PROJECTS=1`, `SYNAPSE_DETECTION_METHOD=<method>`, `SYNAPSE_VERBOSE_DETECTION=1`

---

Context:

__Lint Levels__:
- `strict`: Fail on any lint warnings or errors
- `flexible`: Allow warnings, fail only on errors

__Third-Party Workflow Detection Process__:

**Phase 1: Known Framework Detection (High Confidence)**
- **OpenSpec**: Check for `openspec/` directory with `project.md` and `AGENTS.md`
  - Scan `openspec/changes/` for directories containing `tasks.md` files
  - Pattern: `openspec/changes/[change-name]/tasks.md`
- **GitHub Spec Kit**: Check for `specs/` directory with numbered features
  - Scan for `specs/[###-feature-name]/` directories containing `tasks.md`
  - Pattern: `specs/[###-feature]/tasks.md`

**Phase 2: Generic Tasks.md Discovery (Medium Confidence)**
- Use Glob tool to find all `tasks.md` files across the project: `**/tasks.md`
- Analyze parent directory structure for each found file
- Extract potential feature/change names from directory paths

**Phase 3: LLM Pattern Analysis (Variable Confidence)**
- For unrecognized directory structures containing `tasks.md` files:
  - Analyze directory naming patterns and organization
  - Examine nearby files (README.md, spec.md, etc.) for context
  - Attempt to infer workflow type and categorization

**Phase 4: Interactive User Resolution (User-Verified)**
- If detection is uncertain or patterns are ambiguous:
  - Present discovered `tasks.md` files to the user
  - Ask user to specify workflow type or confirm "no task management system"
  - Store user responses in `user_preferences` for future scans

**Phase 5: Active Feature Determination**
- After detecting workflow type and discovering task files, determine which feature is currently active:
  - **Most Recent**: Choose the task file with the most recent modification time
  - **Git Context**: If current branch matches a feature name pattern, use that feature
  - **User Input**: If multiple viable candidates, ask user which feature they're working on
- Set `active_feature_directory` to the parent directory of the active task file
- Set `active_tasks_file` to the full path of the active task file

**Detection Rules**:
- If no `tasks.md` files found: Set `no_task_management: true`
- If patterns are clear: Use `known_pattern` detection method with high confidence
- If patterns require analysis: Use `llm_analysis` with variable confidence
- If user input needed: Use `user_specified` with maximum confidence
- Always include confidence scores (0.0-1.0) for non-user-specified detections
- Always set active_feature_directory and active_tasks_file when tasks are found

**Multiple Workflow Handling (CRITICAL)**:
- **ONLY ONE workflow per project is supported**
- If multiple task files or workflow systems are detected:
  1. Present all detected workflows to the user
  2. Ask user to choose ONE workflow to use
  3. Only include the chosen workflow in config
- Example prompt:
  ```
  ⚠️  Multiple workflow systems detected:
    1. OpenSpec workflow: openspec/changes/feature-x/tasks.md
    2. GitHub Spec Kit: specs/001-feature-y/tasks.md
    3. Custom workflow: docs/tasks.md

  Please choose which workflow to use (enter number):
  ```
- Store the chosen workflow as a single `third_party_workflow` object
- Do NOT create an array or multiple workflow entries

**Phase 6: Task Format Schema Analysis**

After detecting active tasks file, analyze its format and generate a schema v2.0 that enables hooks to parse tasks dynamically.

### Step 1: Read and Sample Tasks File

Read first 500 lines or entire file if smaller to establish patterns:

```python
with open(active_tasks_file, 'r') as f:
    lines = [f.readline() for _ in range(500)]
    if not lines[-1]:  # File has fewer than 500 lines
        f.seek(0)
        lines = f.readlines()
```

### Step 2: Detect Format Type

Count format indicators to determine primary format:

```python
import re

checklist_count = sum(1 for line in lines if re.match(r'^\s*-\s*\[[xX ]\]', line))
numbered_count = sum(1 for line in lines if re.match(r'^\s*\d+\.', line))

if checklist_count > len(lines) * 0.3:
    format_type = "markdown-checklist"
elif numbered_count > len(lines) * 0.3:
    format_type = "numbered-list"
else:
    format_type = "custom"
```

### Step 3: Extract Task Line Pattern

Find lines that appear to be main tasks (have task IDs or are bold):

```python
# Look for task ID patterns
task_id_candidates = []
for line in lines:
    # Common patterns: T001, TASK-001, #001, etc.
    match = re.search(r'\b([A-Z]+[-_]?\d{1,4})\b', line)
    if match:
        task_id_candidates.append(match.group(1))

# Determine most common pattern
if task_id_candidates:
    sample_id = task_id_candidates[0]
    prefix = re.match(r'^([A-Z]+)', sample_id).group(1)
    digits = len(re.search(r'\d+', sample_id).group(0))
    task_id_pattern = f"{prefix}\\d{{{digits}}}"
else:
    task_id_pattern = "T\\d{3}"  # Default

# Build task line regex based on format type
# IMPORTANT: Use "task_code" group name (not "task_id") to match canonical schema
if format_type == "markdown-checklist":
    task_line_regex = (
        f"^\\s*-\\s*\\[([ xX])\\]\\s*-\\s*"
        f"\\*\\*(?P<task_code>{task_id_pattern}):\\s*(?P<description>.+?)\\*\\*\\s*$"
    )
elif format_type == "numbered-list":
    task_line_regex = (
        f"^\\s*\\d+\\.\\s*"
        f"\\*\\*(?P<task_code>{task_id_pattern}):\\s*(?P<description>.+?)\\*\\*\\s*$"
    )
else:
    task_line_regex = f"(?P<task_code>{task_id_pattern}):\\s*(?P<description>.+)"
```

### Step 4: Extract Status Information

Find all status lines and extract field names + values:

```python
status_lines = []
for line in lines:
    # Look for pattern: "Field Name: [Status Value]"
    match = re.search(r'([^:]+):\s*\[([^\]]+)\]', line)
    if match:
        field_name = match.group(1).strip()
        status_value = match.group(2).strip()
        status_lines.append((field_name, status_value))

# Group by field name
from collections import defaultdict
status_by_field = defaultdict(set)
for field, status in status_lines:
    status_by_field[field].add(status)

# Convert to lists
status_values = {
    field: sorted(list(values))
    for field, values in status_by_field.items()
}
```

### Step 5: Normalize Status Values

Map field names and status values to semantic categories:

```python
# Field name normalization
# NOTE: Build as arrays temporarily to collect all field name variants
# Will be normalized to strings (first variant only) in Step 6 to match canonical schema
field_mapping = {}
for raw_field in status_values.keys():
    raw_lower = raw_field.lower()

    if 'dev' in raw_lower:
        semantic = 'dev'
    elif 'qa' in raw_lower or 'quality' in raw_lower:
        semantic = 'qa'
    elif 'user' in raw_lower or 'verification' in raw_lower:
        semantic = 'user_verification'
    else:
        semantic = raw_field.lower().replace(' ', '_')

    if semantic not in field_mapping:
        field_mapping[semantic] = []
    field_mapping[semantic].append(raw_field)

# Status value normalization
state_mapping = {}
for semantic_field, raw_fields in field_mapping.items():
    # Get all status values for this field
    all_values = set()
    for raw_field in raw_fields:
        all_values.update(status_values.get(raw_field, []))

    # Special handling for QA field (three-category pattern: not_verified, verified_success, verified_failure)
    if semantic_field == 'qa':
        states = {
            'not_verified': [],
            'verified_success': [],
            'verified_failure_pattern': None
        }

        for value in all_values:
            value_lower = value.lower()

            # Check for failure pattern first (Failed - reason)
            if value_lower.startswith('failed'):
                # Set the pattern, not individual values
                if states['verified_failure_pattern'] is None:
                    states['verified_failure_pattern'] = "^Failed - .*"
            elif any(kw in value_lower for kw in ['not start', 'pending', 'todo', 'waiting']):
                states['not_verified'].append(value)
            elif any(kw in value_lower for kw in ['complete', 'done', 'pass', 'verified']):
                states['verified_success'].append(value)
            else:
                # Unknown QA status - default to not_verified for safety
                states['not_verified'].append(value)

        state_mapping[semantic_field] = states
    else:
        # Standard three-state pattern for other fields
        states = {
            'not_started': [],
            'in_progress': [],
            'complete': []
        }

        for value in all_values:
            value_lower = value.lower()

            if any(kw in value_lower for kw in ['not start', 'pending', 'todo', 'waiting']):
                states['not_started'].append(value)
            elif any(kw in value_lower for kw in ['progress', 'working', 'active', 'ongoing']):
                states['in_progress'].append(value)
            elif any(kw in value_lower for kw in ['complete', 'done', 'finish', 'pass', 'verified']):
                states['complete'].append(value)
            else:
                # Unknown - default to not_started for safety
                states['not_started'].append(value)

        # Remove in_progress if field doesn't have that state
        if not states['in_progress'] and len(all_values) == 2:
            # Binary state field (e.g., user verification)
            del states['in_progress']

        state_mapping[semantic_field] = states
```

### Step 6: Build Schema Object

**IMPORTANT**: Generate schema in Current format to match canonical schema (not Future v2.0 format).

```python
from datetime import datetime

# Build task pattern regex with correct group names (task_code, not task_id)
if format_type == "markdown-checklist":
    task_regex = (
        f"^\\s*-\\s*\\[([ xX])\\]\\s*-\\s*"
        f"(?P<task_code>{task_id_pattern})\\s*-\\s*(?P<description>.+?)\\s*$"
    )
    status_regex = (
        "^\\s*-\\s*\\[([ xX])\\]\\s*-\\s*"
        "(?P<field_code>[^:]+):\\s*\\[(?P<status_value>[^\\]]+)\\]\\s*$"
    )
else:
    task_regex = f"(?P<task_code>{task_id_pattern}):\\s*(?P<description>.+)"
    status_regex = "(?P<field_code>[^:]+):\\s*\\[(?P<status_value>[^\\]]+)\\]"

# Normalize field_mapping to strings (not arrays) - take first variant only
normalized_field_mapping = {}
for semantic_field, raw_fields in field_mapping.items():
    if isinstance(raw_fields, list):
        normalized_field_mapping[semantic_field] = raw_fields[0]  # Take first only
    else:
        normalized_field_mapping[semantic_field] = raw_fields

schema = {
    "version": "2.0",  # Use "version" not "schema_version"
    "patterns": {
        # Use "task", "status_field" (not "task_line", "status_line")
        # Patterns are strings (not objects)
        "task": task_regex,
        "subtask": f"^\\s+\\[\\s*\\]\\s*-\\s*(?P<subtask_code>{task_id_pattern}-ST\\d{{3,}})\\s*-\\s*(?P<description>.*)$" if format_type == "markdown-checklist" else "",
        "status_field": status_regex
    },
    # field_mapping at TOP LEVEL (not nested under status_semantics)
    "field_mapping": normalized_field_mapping,
    "status_semantics": {
        # No "fields" array, no nested "field_mapping"
        "states": state_mapping
    }
}
```

### Step 7: Validate Schema

Re-parse tasks using generated schema to ensure it works:

```python
from synapse_cli.parsers.task_schema_parser import TaskSchemaParser

# Validate schema compiles and is structurally valid
try:
    parser = TaskSchemaParser(schema)
    print("✅ Schema structure is valid")
except Exception as e:
    print(f"⚠️ Schema validation failed: {e}")
    print("   Continuing with best-effort schema")

# Test parsing with actual tasks file to verify patterns work
try:
    validation_tasks = parser.parse_tasks_file(active_tasks_file)
    success_rate = len(validation_tasks) / len(task_id_candidates) if task_id_candidates else 0

    if success_rate >= 0.95:
        print(f"✅ Schema validation passed: {success_rate*100:.1f}% match rate")
        print(f"   Successfully parsed {len(validation_tasks)} tasks")
    else:
        print(f"⚠️ Schema validation below threshold: {success_rate*100:.1f}%")
        print(f"   Parsed {len(validation_tasks)}/{len(task_id_candidates)} tasks")
except Exception as e:
    print(f"⚠️ Validation error: {e}")
    print("   Schema may not work correctly with this task file format")
```

### Step 8: Add Schema to Config

Add the generated schema to the workflow detection object:

```python
# Build the third_party_workflow object (single workflow only)
# If multiple workflows were detected, user should have chosen one by now
third_party_workflow = {
    "type": workflow_type,  # e.g., "openspec", "github-spec-kit", "custom"
    "active_tasks_file": active_tasks_file,
    "active_tasks": [],  # Initially empty, agent will populate when starting work
    "task_format_schema": schema
}

# Add to config
config["third_party_workflow"] = third_party_workflow
```

**IMPORTANT**:
- Use `third_party_workflow` (singular, object) not `third_party_workflows` (plural, array)
- Always include the `active_tasks` field, initialized to empty array `[]`
- Only ONE workflow per project - if multiple detected, user must choose

### Error Handling

- If pattern extraction fails → set `format_type` to "custom" and use best-effort patterns
- If no status lines found → create minimal schema with task patterns only
- If validation fails → report to user and continue with low confidence
- If file is too large (>10MB) → only sample first 1000 lines

## Output

After analysis, update the `.synapse/config.json` file with both the quality configuration and third-party workflow detection results.

### Final Step 1: Validate Configuration Structure

**CRITICAL**: After updating `.synapse/config.json`, you MUST validate the configuration structure using the validation module:

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

### Final Step 2: Validate Quality Commands

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

### Summary Report

Provide a summary of what was detected and configured:
- **Configuration mode** (single or monorepo)
- Project type(s) detected
- Quality commands configured (lint, test, coverage, etc.)
  - For monorepo: list commands per project
- Third-party workflow detection results
- Task format schema generation (if applicable)
- **Config structure validation result** (PASS/FAIL)
- **Quality commands validation result** (PASS/FAIL)

If you are unable to complete the task fully, explain what was done and what is missing so that the user can assist.

**Important**:
- Only include commands that actually exist in the project
- Test commands before adding them to ensure they work
- Read the existing `.synapse/config.json` file and preserve all existing sections
- Only add or update the `quality-config` and `third_party_workflow` sections
- Always perform third-party workflow detection even if no quality commands are found
- For third-party workflow detection, be thorough but ask for user clarification when uncertain
- **CRITICAL**: Only ONE workflow per project - if multiple detected, ask user to choose
- Always include `active_tasks` field (empty array initially) in `third_party_workflow`
- Always generate task format schema v2.0 when active tasks file is found
- For QA Status field, use three-category pattern (not_verified, verified_success, verified_failure_pattern)
- **Ensure the resulting JSON is valid and well-formatted**
- **Always validate the final configuration before reporting success**