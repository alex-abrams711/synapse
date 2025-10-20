---
allowed-tools: Bash, Read, Write, Glob, Grep
description: Analyze project and generate quality configuration for hooks (Planning Phase)
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

**Detection Rules**:
- If no `tasks.md` files found: Set `no_task_management: true`
- If patterns are clear: Use `known_pattern` detection method with high confidence
- If patterns require analysis: Use `llm_analysis` with variable confidence
- If user input needed: Use `user_specified` with maximum confidence
- Always include confidence scores (0.0-1.0) for non-user-specified detections

**Note**: This command is used during the planning phase, BEFORE feature directories are created. It detects workflow systems but does not require active features to exist yet.

## Output

After analysis, update the `.synapse/config.json` file with both the quality configuration and third-party workflow detection results. Provide a summary of what was detected and configured. If you are unable to complete the task fully, please explain what was done and what is missing so that the user can assist.

**Important**:
- Only include commands that actually exist in the project
- Test commands before adding them to ensure they work
- Read the existing `.synapse/config.json` file and preserve all existing sections
- Only add or update the `quality-config` and `third_party_workflows` sections
- Always perform third-party workflow detection even if no quality commands are found
- For third-party workflows, be thorough but ask for user clarification when uncertain
- Ensure the resulting JSON is valid and well-formatted
- During planning phase, do NOT require active feature directories or tasks files to exist