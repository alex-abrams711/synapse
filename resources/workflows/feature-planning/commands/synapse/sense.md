---
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion
description: Analyze project and generate quality configuration for workflows
---

The user input can guide you on project type and non-conventional configurations. You **MUST** consider it before proceeding.

User input:

$ARGUMENTS

# Quality Configuration Setup

You are tasked with analyzing the current project and adding a comprehensive quality configuration section to the Synapse config file that will be used by the quality gate hooks.

## Your Task

### IMPORTANT: IGNORE SYNAPSE WORKFLOW FILES AND DIRECTORIES WHEN DECIPHERING PROJECT TYPE

1. **Analyze Project Structure**:
   - Identify the project type (Node.js, Python, Rust, Go, Java, etc.)
   - Look for planning, design, and architecture documentation as its possible this is a greenfield project that has no code and the documentation might allow you to decipher the planned project type
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
   - **BREAKING CHANGE**: If multiple workflows detected, ask user to choose ONE (Synapse supports single workflow only)
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
   - Add a `third_party_workflow` section (SINGULAR, OBJECT) with detected workflow information
   - Include task_format_schema with three-category QA patterns
   - Include active_tasks field (empty array by default)
   - Add project-appropriate thresholds and settings
   - Save the updated config.json file

## Configuration Schema

Both the `quality-config` and `third_party_workflow` sections should be added to the existing `.synapse/config.json` file with this structure:

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
  "third_party_workflow": {
    "type": "openspec|spec-kit|custom|unknown",
    "detection_method": "known_pattern|llm_analysis|user_specified",
    "root_directory": "openspec/|specs/|custom/path/",
    "active_tasks_file": "tasks.md",
    "active_tasks": [],
    "confidence": 0.95,
    "detected_at": "2025-01-15T10:00:00Z",
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

**Important**: Only add the `quality-config` and `third_party_workflow` sections to the existing config.json. Do not modify any other existing sections.

Context:

__Lint Levels__:
- `strict`: Fail on any lint warnings or errors
- `flexible`: Allow warnings, fail only on errors

__Third-Party Workflow Detection Process__:

**Phase 1: Known Framework Detection (High Confidence)**
- **OpenSpec**: Check for `openspec/` directory with `project.md` and `AGENTS.md`
  - Scan `openspec/changes/` for directories containing `tasks.md` files
  - Pattern: `openspec/changes/[change-name]/tasks.md`
  - Set `active_tasks_file` to the most recent or user-specified tasks.md
- **GitHub Spec Kit**: Check for `specs/` directory with numbered features
  - Scan for `specs/[###-feature-name]/` directories containing `tasks.md`
  - Pattern: `specs/[###-feature]/tasks.md`
  - Set `active_tasks_file` to the most recent or user-specified tasks.md

**Phase 2: Generic Tasks.md Discovery (Medium Confidence)**
- Use Glob tool to find all `tasks.md` files across the project: `**/tasks.md`
- Analyze parent directory structure for each found file
- Extract potential feature/change names from directory paths

**Phase 3: Multiple Workflows Handling (Option 6 Requirement)**
- If multiple tasks.md files found:
  - Use AskUserQuestion tool to ask user to select ONE workflow
  - Present options with file paths and descriptions
  - Store user's choice as the single workflow
- Only one workflow can be active in Option 6

**Phase 4: LLM Pattern Analysis (Variable Confidence)**
- For unrecognized directory structures containing `tasks.md` files:
  - Analyze directory naming patterns and organization
  - Examine nearby files (README.md, spec.md, etc.) for context
  - Attempt to infer workflow type and categorization

**Phase 5: Interactive User Resolution (User-Verified)**
- If detection is uncertain or patterns are ambiguous:
  - Present discovered `tasks.md` files to the user
  - Ask user to specify workflow type or confirm "no task management system"
  - Store user responses for configuration

**Detection Rules**:
- If no `tasks.md` files found: Do not add `third_party_workflow` section
- If patterns are clear: Use `known_pattern` detection method with high confidence
- If patterns require analysis: Use `llm_analysis` with variable confidence
- If user input needed: Use `user_specified` with maximum confidence
- Always include confidence scores (0.0-1.0) for non-user-specified detections
- **REQUIRED**: Always include `active_tasks: []` (empty array by default)
- **REQUIRED**: Always include complete `task_format_schema` as shown above

__Task Format Schema Details__:

The schema defines how to parse task files. Use these exact patterns for Option 6 compatibility:

**Task pattern**: Matches top-level tasks with codes
```regex
^\\[\\s*\\]\\s*-\\s*(?P<task_code>T\\d{3,})\\s+-\\s+(?P<description>(?!.*:).*)
```
Matches: `[ ] - T001 - Task description`

**Subtask pattern**: Matches indented subtasks
```regex
^\\s+\\[\\s*\\]\\s*-\\s*(?P<subtask_code>T\\d{3,}-ST\\d{3,})\\s*-\\s*(?P<description>.*)
```
Matches: `  [ ] - T001-ST001 - Subtask description`

**Status field pattern**: Matches status fields with values
```regex
^\\s+\\[\\s*\\]\\s*-\\s*T\\d{3,}-(?P<field_code>[A-Z]{2,})\\s*-\\s*.*:\\s*\\[(?P<status_value>[^\\]]+)\\]
```
Matches: `  [ ] - T001-QA - QA Status: [Passed]`

**Field mapping**:
- Dev Status: `DS`
- QA Status: `QA`
- User Verification: `UV`

**QA Status semantics (Option 6)**:
- `not_verified`: `["Not Started"]` - Hook blocks stop
- `verified_success`: `["Complete", "Passed"]` - Hook allows stop
- `verified_failure_pattern`: `"^Failed - .*"` - Hook allows stop (user can fix later)

**Note**: This command is used during the planning phase, BEFORE feature directories are created. It detects workflow systems but does not require active features to exist yet.

## Output

After analysis, update the `.synapse/config.json` file with both the quality configuration and third-party workflow detection results. Provide a summary of what was detected and configured. If you are unable to complete the task fully, please explain what was done and what is missing so that the user can assist.

**Important**:
- Only include commands that actually exist in the project
- Test commands before adding them to ensure they work
- Read the existing `.synapse/config.json` file and preserve all existing sections
- Only add or update the `quality-config` and `third_party_workflow` sections
- Always perform third-party workflow detection even if no quality commands are found
- For third-party workflows, be thorough but ask for user clarification when uncertain
- **If multiple workflows found, use AskUserQuestion to let user choose ONE**
- Always include `active_tasks: []` and complete `task_format_schema`
- Ensure the resulting JSON is valid and well-formatted
- During planning phase, do NOT require active feature directories or tasks files to exist

## Example: Handling Multiple Workflows

If you detect multiple tasks.md files:

1. List all found workflows:
```
Found multiple task files:
1. openspec/changes/user-auth/tasks.md (OpenSpec pattern)
2. specs/001-api-design/tasks.md (Spec Kit pattern)
3. tasks.md (root level)
```

2. Use AskUserQuestion:
```json
{
  "question": "Which workflow would you like to use for this project?",
  "header": "Workflow",
  "multiSelect": false,
  "options": [
    {
      "label": "OpenSpec (user-auth)",
      "description": "openspec/changes/user-auth/tasks.md - OpenSpec workflow pattern"
    },
    {
      "label": "Spec Kit (001-api-design)",
      "description": "specs/001-api-design/tasks.md - GitHub Spec Kit pattern"
    },
    {
      "label": "Root tasks.md",
      "description": "tasks.md - Simple root-level task file"
    }
  ]
}
```

3. Generate config based on user's choice (only ONE workflow)
