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

Both the `quality-config` and `third_party_workflows` sections should be added to the existing `.synapse/config.json` file with this structure:

```json
{
  "synapse_version": "0.1.0",
  "initialized_at": "existing timestamp",
  "agent": {
    "type": "claude-code",
    "description": "existing agent info"
  },
  "project": {
    "name": "existing project name",
    "description": "existing description",
    "root_directory": "existing root directory"
  },
  "workflows": {
    "active_workflow": "existing workflow info",
    "applied_workflows": []
  },
  "settings": {
    "auto_backup": true,
    "strict_validation": true,
    "uv_required": true
  },
  "quality-config": {
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
  "third_party_workflows": {
    "detected": [
      {
        "type": "openspec|spec-kit|custom|unknown",
        "detection_method": "known_pattern|llm_analysis|user_specified",
        "root_directory": "openspec/|specs/|custom/path/",
        "active_feature_directory": "openspec/changes/add-auth/",
        "active_tasks_file": "openspec/changes/add-auth/tasks.md",
        "confidence": 0.95,
        "detected_at": "2025-10-16T15:45:00Z"
      }
    ],
    "user_preferences": {
      "no_task_management": false,
      "custom_patterns": [
        {
          "pattern": "docs/*/tasks.md",
          "type": "custom-docs-workflow"
        }
      ]
    },
    "last_scan": "2025-10-16T15:45:00Z"
  }
}
```

**Important**: Only add the `quality-config` and `third_party_workflows` sections to the existing config.json. Do not modify any other existing sections.

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
if format_type == "markdown-checklist":
    task_line_regex = (
        f"^\\s*-\\s*\\[([ xX])\\]\\s*-\\s*"
        f"\\*\\*(?P<task_id>{task_id_pattern}):\\s*(?P<description>.+?)\\*\\*\\s*$"
    )
elif format_type == "numbered-list":
    task_line_regex = (
        f"^\\s*\\d+\\.\\s*"
        f"\\*\\*(?P<task_id>{task_id_pattern}):\\s*(?P<description>.+?)\\*\\*\\s*$"
    )
else:
    task_line_regex = f"(?P<task_id>{task_id_pattern}):\\s*(?P<description>.+)"
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

    # Categorize values
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

```python
from datetime import datetime

schema = {
    "schema_version": "2.0",
    "format_type": format_type,
    "patterns": {
        "task_line": {
            "regex": task_line_regex,
            "groups": ["checkbox", "task_id", "description"] if format_type == "markdown-checklist" else ["task_id", "description"],
            "example": lines[0].strip() if lines else "",
            "required": True
        },
        "status_line": {
            "regex": "^\\s*-\\s*\\[([ xX])\\]\\s*-\\s*(?P<field>[^:]+):\\s*\\[(?P<status>[^\\]]+)\\]\\s*$" if format_type == "markdown-checklist" else "(?P<field>[^:]+):\\s*\\[(?P<status>[^\\]]+)\\]",
            "groups": ["checkbox", "field", "status"] if format_type == "markdown-checklist" else ["field", "status"],
            "example": f"- [X] - {status_lines[0][0]}: [{status_lines[0][1]}]" if status_lines else "",
            "required": True
        }
    },
    "status_semantics": {
        "fields": list(field_mapping.keys()),
        "field_mapping": field_mapping,
        "states": state_mapping
    },
    "task_id_format": {
        "prefix": prefix,
        "digits": digits,
        "pattern": task_id_pattern,
        "example": task_id_candidates[0] if task_id_candidates else "T001",
        "separator": ""
    },
    "metadata": {
        "analyzed_at": datetime.now().isoformat(),
        "sample_size": len(lines),
        "total_tasks_found": len(task_id_candidates),
        "confidence": 1.0 if len(task_id_candidates) > 10 else 0.8,
        "format_detected_by": "sense_command",
        "source_file": active_tasks_file
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
except Exception as e:
    print(f"⚠️ Schema validation failed: {e}")
    schema["metadata"]["confidence"] = 0.5
    # Continue with low confidence schema

# Test parsing with first 200 lines
try:
    validation_tasks = parser.parse_tasks_file(active_tasks_file)
    success_rate = len(validation_tasks) / len(task_id_candidates) if task_id_candidates else 0

    if success_rate >= 0.95:
        schema["validation"] = {
            "valid_sample_size": len(validation_tasks),
            "pattern_match_rate": success_rate,
            "last_validated": datetime.now().isoformat(),
            "validation_passed": True
        }
        print(f"✅ Schema validation passed: {success_rate*100:.1f}% match rate")
    else:
        print(f"⚠️ Schema validation below threshold: {success_rate*100:.1f}%")
        schema["metadata"]["confidence"] = 0.5
except Exception as e:
    print(f"⚠️ Validation error: {e}")
    schema["metadata"]["confidence"] = 0.5
```

### Step 8: Add Schema to Config

Add the generated schema to the workflow detection object:

```python
# Find the workflow entry for this tasks file
for workflow in workflows_detected:
    if workflow.get("active_tasks_file") == active_tasks_file:
        workflow["task_format_schema"] = schema
        break
```

### Error Handling

- If pattern extraction fails → set `format_type` to "custom" and use best-effort patterns
- If no status lines found → create minimal schema with task patterns only
- If validation fails → report to user and continue with low confidence
- If file is too large (>10MB) → only sample first 1000 lines

## Output

After analysis, update the `.synapse/config.json` file with both the quality configuration and third-party workflow detection results. Provide a summary of what was detected and configured. If you are unable to complete the task fully, please explain what was done and what is missing so that the user can assist.

**Important**:
- Only include commands that actually exist in the project
- Test commands before adding them to ensure they work
- Read the existing `.synapse/config.json` file and preserve all existing sections
- Only add or update the `quality-config` and `third_party_workflows` sections
- Always perform third-party workflow detection even if no quality commands are found
- For third-party workflows, be thorough but ask for user clarification when uncertain
- Always generate task format schema v2.0 when active tasks file is found
- Ensure the resulting JSON is valid and well-formatted