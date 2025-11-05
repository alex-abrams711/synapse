# Sense Command

The `/sense` command analyzes the current project to detect:
- Project type and primary language
- Package managers and build tools
- Quality tools (linters, type checkers, test runners, coverage tools)

## Usage

In Claude Code, use this command to understand the project's quality tooling:

```
/sense
```

Claude will analyze the project and report what quality tools are configured.

## What It Detects

### Project Type
- **Python**: Detects `pyproject.toml`, `setup.py`, `requirements.txt`
- **JavaScript/TypeScript**: Detects `package.json`, `tsconfig.json`
- **Go**: Detects `go.mod`
- **Rust**: Detects `Cargo.toml`
- **Java**: Detects `pom.xml`, `build.gradle`
- **Ruby**: Detects `Gemfile`

### Package Managers
- Python: pip, poetry, pipenv, uv
- JavaScript: npm, yarn, pnpm
- Other: cargo, go modules, bundler, maven, gradle

### Quality Tools

**Linters:**
- Python: ruff, pylint, flake8
- JavaScript/TypeScript: eslint, prettier

**Type Checkers:**
- Python: mypy, pyright
- TypeScript: tsc

**Test Runners:**
- Python: pytest, unittest
- JavaScript/TypeScript: jest, vitest, mocha

**Coverage Tools:**
- Python: coverage
- JavaScript/TypeScript: jest --coverage, nyc

## Example Output

```
Project Information:
  Primary Language: Python
  Languages: Python
  Package Manager: uv
  Build Tool: pyproject.toml

Linters:
  ✓ ruff: ruff check .

Type Checkers:
  ✓ mypy: mypy .

Test Runners:
  ✓ pytest: pytest

Coverage Tools:
  ✓ coverage: coverage run -m pytest && coverage report
    Default threshold: 80%
```

## Monorepo Support

The sense command detects monorepo structures and generates optimized configurations:

### Automatic Monorepo Detection

When analyzing a project, sense checks for:
- Multiple project directories with distinct package managers
- Common monorepo markers (lerna.json, nx.json, pnpm-workspace.yaml, etc.)
- Multiple language configurations at different depths

### Monorepo Configuration

For monorepo projects, sense generates a `mode: "monorepo"` configuration with:
- Separate project configurations for each sub-package
- Individual quality commands per project
- **Optimization settings** for performance (5-10x faster checks)

Example monorepo config:

```json
{
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
          "test": "cd backend && pytest"
        },
        "thresholds": {
          "lintLevel": "strict"
        }
      },
      "frontend": {
        "directory": "frontend/",
        "projectType": "node",
        "commands": {
          "lint": "cd frontend && npm run lint",
          "test": "cd frontend && npm test"
        },
        "thresholds": {
          "lintLevel": "flexible"
        }
      }
    }
  }
}
```

### Optimization Settings

The `optimization` section enables git-based change detection to only run quality checks on affected packages:

**Configuration Options**:
- `check_affected_only` (default: `true`) - Enable smart detection of changed projects
- `detection_method` (default: `"uncommitted"`) - How to detect changes:
  - `"uncommitted"` - Detect uncommitted changes (default, best for local development)
  - `"since_main"` - Changes since origin/main (best for CI/CD and PRs)
  - `"last_commit"` - Changes in the last commit only
  - `"staged"` - Only staged changes
  - `"all_changes"` - All changes including untracked files
- `fallback_to_all` (default: `true`) - Check all projects if no changes detected (safety fallback)
- `force_check_projects` (default: `[]`) - Projects to always check regardless of changes (useful for shared libraries)
- `verbose_logging` (default: `false`) - Show detailed detection information

**Performance Impact**:
- **Without optimization**: 15 packages × 10 sec = 150 seconds
- **With optimization**: 1-2 packages × 10 sec = 10-20 seconds
- **Improvement**: 5-10x faster for typical single-project changes

**Environment Variable Overrides**:
You can override optimization settings at runtime:
- `SYNAPSE_CHECK_ALL_PROJECTS=1` - Force check all projects
- `SYNAPSE_DETECTION_METHOD=<method>` - Override detection method
- `SYNAPSE_VERBOSE_DETECTION=1` - Enable verbose logging

See the [Hook README](../../workflows/feature-implementation/hooks/README.md#monorepo-optimization) for complete documentation.

## Integration with Workflows

The sense command automatically runs during workflow initialization:

1. **During `synapse init`**: Basic project detection
2. **Before applying feature-implementation workflow**: Quality tool configuration
3. **Monorepo detection**: Automatically configures optimization for multi-package projects

The detected tools are used by the feature-implementation workflow's quality gates to ensure code quality standards are met.

## Manual Configuration Update

You can also run sense manually from the command line to update Synapse configuration:

```bash
synapse sense --update-config
```

This will:
1. Analyze the project
2. Detect all quality tools
3. Update `.synapse/config.json` with quality tool configuration
4. Set up default thresholds (80% coverage, 0 lint/type errors)

## Quality Tool Configuration

Once detected, quality tools are configured in `.synapse/config.json`:

```json
{
  "quality_config": {
    "project_info": {
      "primary_language": "Python",
      "package_manager": "uv"
    },
    "quality_tools": {
      "linters": [
        {"name": "ruff", "command": "ruff check .", "type": "linter"}
      ],
      "type_checkers": [
        {"name": "mypy", "command": "mypy .", "type": "type_checker"}
      ],
      "test_runners": [
        {"name": "pytest", "command": "pytest", "type": "test_runner"}
      ],
      "coverage": [
        {
          "name": "coverage",
          "command": "coverage run -m pytest && coverage report",
          "type": "coverage",
          "threshold": 80
        }
      ]
    },
    "thresholds": {
      "coverage_minimum": 80,
      "lint_errors_max": 0,
      "type_errors_max": 0
    },
    "enforce_on_commit": true
  }
}
```

## When To Use

Use the sense command when:
- Starting work on a new project
- You want to verify what quality tools are configured
- Setting up the feature-implementation workflow
- Quality gates are failing and you need to diagnose tool configuration
- Adding new quality tools to your project

## Best Practices

1. **Run after setup**: Run `/sense` after installing new quality tools
2. **Verify detection**: If tools aren't detected, check configuration files exist
3. **Update config**: Use `--update-config` flag to persist detection results
4. **Quality gates**: Ensure detected tools match what's required by your workflow

## Troubleshooting

**Tool not detected?**
- Verify the tool's configuration file exists (e.g., `pyproject.toml`, `.eslintrc.json`)
- Check that the tool is listed in dependencies (`package.json`, `pyproject.toml`)
- Some tools require explicit configuration files to be detected

**Wrong primary language?**
- Detection prioritizes based on config file presence
- If multiple languages exist, the first-found becomes primary
- You can manually override in `.synapse/config.json` if needed

**Quality gates failing?**
- Run `/sense` to verify tool commands are correct
- Check that tools are actually installed (`pip list`, `npm list`)
- Verify tool commands work from command line first

## Implementation Instructions for AI Assistants

When generating quality configuration for `.synapse/config.json`:

### For Single Project Mode

Generate flat configuration structure:

```json
{
  "quality-config": {
    "mode": "single",
    "projectType": "<detected-type>",
    "commands": { /* ... */ },
    "thresholds": { /* ... */ }
  }
}
```

### For Monorepo Mode

When you detect a monorepo (multiple sub-projects), generate:

```json
{
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
      "<project-name>": {
        "directory": "<project-dir>/",
        "projectType": "<type>",
        "commands": { /* ... */ },
        "thresholds": { /* ... */ }
      }
    }
  }
}
```

**IMPORTANT**: Always include the `optimization` section in monorepo configs with these defaults:
- `check_affected_only: true` - Enables git-based change detection (5-10x performance improvement)
- `detection_method: "uncommitted"` - Best for local development
- `fallback_to_all: true` - Safety fallback
- `force_check_projects: []` - User can add shared libraries later
- `verbose_logging: false` - Minimal output by default

**Recommendation for force_check_projects**:
If you detect shared/common packages (e.g., "shared-utils", "core", "common", "lib"), add them to `force_check_projects` array and explain to the user:

```
ℹ️  Detected shared libraries: shared-utils, core
   These will always be checked due to their dependencies.
   You can modify force_check_projects in .synapse/config.json if needed.
```

## Related Commands

- `/openspec:proposal` - Create structured feature proposals
- `/openspec:apply` - Implement approved changes with quality gates
- `synapse workflow feature-implementation` - Apply workflow with quality enforcement
