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

## Integration with Workflows

The sense command automatically runs during workflow initialization:

1. **During `synapse init`**: Basic project detection
2. **Before applying feature-implementation workflow**: Quality tool configuration

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

## Related Commands

- `/openspec:proposal` - Create structured feature proposals
- `/openspec:apply` - Implement approved changes with quality gates
- `synapse workflow feature-implementation` - Apply workflow with quality enforcement
