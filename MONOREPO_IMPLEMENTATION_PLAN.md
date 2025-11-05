# Monorepo Quality Config Implementation Plan

## Overview

Implement support for monorepo projects with multiple sub-packages, each having distinct quality configurations, languages, and tooling.

**Design Approach**: Hybrid mode with explicit `mode` field and `projects` structure.

**Execution Strategy**: Run quality checks for all projects (no affected-file detection in v1).

**Project Naming**: Directory-based naming (e.g., "backend", "frontend").

---

## Design Specification

### Config Structure

```json
{
  "quality-config": {
    "mode": "single" | "monorepo",

    // SINGLE MODE (default if mode not specified):
    "projectType": "python",
    "commands": {
      "lint": "ruff check .",
      "test": "pytest"
    },
    "thresholds": {
      "lintLevel": "strict",
      "coverage": {...}
    },
    "metadata": {...},

    // MONOREPO MODE:
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
          "coverage": {...}
        },
        "metadata": {...}
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
        "metadata": {...}
      }
    }
  }
}
```

### Key Principles

1. **Explicit mode** - `mode` field determines structure interpretation
2. **Directory-based naming** - Project names derived from directory paths
3. **Commands include `cd`** - Each command changes to project directory
4. **Breaking changes allowed** - No backwards compatibility constraints
5. **Auto-detection first** - Sense detects monorepo, asks for clarification when uncertain

---

## Implementation Phases

### Phase 1: Schema & Core Validation

**Goal**: Update schema and validation to support both single and monorepo modes.

#### Task 1.1: Update Schema Definition
**File**: `resources/schemas/synapse-config-schema.json`

**Changes**:
- Add `mode` enum field to quality-config
- Add conditional schema based on mode:
  - If `mode: "single"` → require `commands`, `thresholds`, `projectType`
  - If `mode: "monorepo"` → require `projects` object
- Define `projects` schema structure
- Each project has same structure as single mode but with `directory` field

**Validation**:
- Schema validates both modes correctly
- Rejects invalid mode values
- Ensures projects have required fields

**Files to modify**:
- `resources/schemas/synapse-config-schema.json`

---

#### Task 1.2: Update Config Validation Logic
**File**: `resources/workflows/feature-implementation/hooks/validate_config.py`

**Changes**:
1. Remove rejection of `subprojects` structure (lines 72-77)
2. Add mode detection:
   ```python
   mode = quality_config.get("mode", "single")
   ```
3. Add validation for each mode:
   - **Single mode**: Validate flat structure (current behavior)
   - **Monorepo mode**: Validate `projects` exists and each project has required fields
4. Update error messages to reference mode
5. Add helper function `validate_monorepo_structure()`

**Validation function signature**:
```python
def validate_monorepo_structure(quality_config: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate monorepo quality-config structure."""
    if "projects" not in quality_config:
        return False, "Monorepo mode requires 'projects' object"

    projects = quality_config["projects"]
    if not isinstance(projects, dict) or len(projects) == 0:
        return False, "'projects' must be non-empty object"

    for project_name, project_config in projects.items():
        # Validate each project has required fields
        if "directory" not in project_config:
            return False, f"Project '{project_name}' missing 'directory' field"
        if "commands" not in project_config:
            return False, f"Project '{project_name}' missing 'commands' field"
        if "thresholds" not in project_config:
            return False, f"Project '{project_name}' missing 'thresholds' field"
        # Validate commands structure
        if not isinstance(project_config["commands"], dict):
            return False, f"Project '{project_name}' commands must be object"
        # Validate thresholds structure
        if not isinstance(project_config["thresholds"], dict):
            return False, f"Project '{project_name}' thresholds must be object"

    return True, "Monorepo structure is valid"
```

**Files to modify**:
- `resources/workflows/feature-implementation/hooks/validate_config.py`

**Tests to add**:
- Update `test_validate_config.py` with monorepo test cases

---

#### Task 1.3: Update Test Suite
**File**: `test_validate_config.py`

**New test configs**:
```python
VALID_MONOREPO_CONFIG = {
    "synapse_version": "0.1.0",
    "project": {...},
    "workflows": {...},
    "settings": {...},
    "quality-config": {
        "mode": "monorepo",
        "projects": {
            "backend": {
                "directory": "backend/",
                "projectType": "python",
                "commands": {"lint": "cd backend && ruff check ."},
                "thresholds": {"lintLevel": "strict"}
            }
        }
    }
}

INVALID_MONOREPO_MISSING_PROJECTS = {...}
INVALID_MONOREPO_MISSING_DIRECTORY = {...}
INVALID_MONOREPO_EMPTY_PROJECTS = {...}
```

**Test cases to add**:
- `test_valid_monorepo_config()`
- `test_monorepo_missing_projects()`
- `test_monorepo_missing_directory()`
- `test_monorepo_empty_projects()`
- `test_monorepo_invalid_project_structure()`
- `test_mode_field_validation()`

**Files to modify**:
- `test_validate_config.py`

---

### Phase 2: Quality Command Validation Updates

**Goal**: Update validation script to test commands for all projects in monorepo mode.

#### Task 2.1: Update Validation Script Core Logic
**File**: `resources/workflows/feature-implementation/hooks/validate_quality_commands.py`

**Changes**:

1. **Add mode detection**:
```python
def get_quality_config_mode(quality_config: Dict[str, Any]) -> str:
    """Determine if config is single or monorepo mode."""
    return quality_config.get("mode", "single")
```

2. **Refactor `validate_all_commands()` to support both modes**:
```python
def validate_all_commands(config_path: str = ".synapse/config.json") -> Tuple[bool, Dict[str, Any]]:
    """Validate all configured quality commands."""
    quality_config = load_quality_config(config_path)
    if not quality_config:
        return False, {"error": "Quality config not found"}

    mode = get_quality_config_mode(quality_config)

    if mode == "single":
        return validate_single_project(quality_config)
    elif mode == "monorepo":
        return validate_monorepo_projects(quality_config)
    else:
        return False, {"error": f"Unknown mode: {mode}"}
```

3. **Extract current logic into `validate_single_project()`**:
```python
def validate_single_project(quality_config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """Validate quality commands for single-project configuration."""
    # Current validation logic (unchanged)
    project_type = detect_project_type(quality_config)
    commands = quality_config.get("commands", {})
    thresholds = quality_config.get("thresholds", {})
    lint_level = thresholds.get("lintLevel", "strict")

    results = {
        "mode": "single",
        "project_type": project_type,
        "lint_level": lint_level,
        "validations": {}
    }

    all_valid = True
    for cmd_name in ["lint", "typecheck", "test", "coverage", "build"]:
        cmd = commands.get(cmd_name)
        if cmd:
            is_valid, message = validate_command(cmd_name, cmd, project_type, lint_level)
            results["validations"][cmd_name] = {
                "command": cmd,
                "valid": is_valid,
                "message": message
            }
            if is_valid is False:
                all_valid = False

    return all_valid, results
```

4. **Add new `validate_monorepo_projects()` function**:
```python
def validate_monorepo_projects(quality_config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """Validate quality commands for monorepo configuration."""
    projects = quality_config.get("projects", {})

    if not projects:
        return False, {
            "error": "No projects configured in monorepo mode",
            "message": "Run '/synapse:sense' to generate quality configuration"
        }

    results = {
        "mode": "monorepo",
        "projects": {}
    }

    all_valid = True

    for project_name, project_config in projects.items():
        project_type = detect_project_type(project_config)
        commands = project_config.get("commands", {})
        thresholds = project_config.get("thresholds", {})
        lint_level = thresholds.get("lintLevel", "strict")
        directory = project_config.get("directory", "")

        project_results = {
            "directory": directory,
            "project_type": project_type,
            "lint_level": lint_level,
            "validations": {}
        }

        for cmd_name in ["lint", "typecheck", "test", "coverage", "build"]:
            cmd = commands.get(cmd_name)
            if cmd:
                is_valid, message = validate_command(
                    cmd_name, cmd, project_type, lint_level
                )
                project_results["validations"][cmd_name] = {
                    "command": cmd,
                    "valid": is_valid,
                    "message": message
                }
                if is_valid is False:
                    all_valid = False

        results["projects"][project_name] = project_results

    return all_valid, results
```

**Files to modify**:
- `resources/workflows/feature-implementation/hooks/validate_quality_commands.py`

---

#### Task 2.2: Update Validation Reporting
**File**: `resources/workflows/feature-implementation/hooks/validate_quality_commands.py`

**Changes to `format_validation_report()`**:

```python
def format_validation_report(all_valid: bool, results: Dict[str, Any]) -> str:
    """Format validation results into a readable report."""
    lines = []
    lines.append("=" * 80)
    lines.append("🔍 Quality Commands Validation Report")
    lines.append("=" * 80)
    lines.append("")

    if "error" in results:
        lines.append(f"❌ {results['error']}")
        lines.append(f"   {results['message']}")
        return "\n".join(lines)

    mode = results.get("mode", "unknown")
    lines.append(f"Mode: {mode}")
    lines.append("")

    if mode == "single":
        # Existing single-project formatting
        lines.extend(format_single_project_report(results))

    elif mode == "monorepo":
        # New monorepo formatting
        lines.extend(format_monorepo_report(results))

    lines.append("")
    lines.append("=" * 80)

    if all_valid:
        lines.append("✅ ALL QUALITY COMMANDS VALIDATED SUCCESSFULLY")
        lines.append("")
        lines.append("Your quality gates are properly configured and will block on issues.")
    else:
        lines.append("❌ VALIDATION FAILED - QUALITY COMMANDS ARE NOT PROPERLY CONFIGURED")
        lines.append("")
        lines.append("⚠️  CRITICAL ISSUE: Some quality commands will NOT block on errors!")
        # ... rest of error message

    lines.append("=" * 80)
    return "\n".join(lines)

def format_monorepo_report(results: Dict[str, Any]) -> list[str]:
    """Format monorepo validation results."""
    lines = []
    projects = results.get("projects", {})

    lines.append(f"Projects: {len(projects)}")
    lines.append("")

    for project_name, project_data in projects.items():
        lines.append("-" * 80)
        lines.append(f"📦 PROJECT: {project_name}")
        lines.append(f"   Directory: {project_data.get('directory', 'N/A')}")
        lines.append(f"   Type: {project_data.get('project_type', 'unknown')}")
        lines.append(f"   Lint Level: {project_data.get('lint_level', 'N/A')}")
        lines.append("")

        validations = project_data.get("validations", {})

        if not validations:
            lines.append("   ℹ️  No quality commands configured")
            lines.append("")
            continue

        for cmd_name, validation in validations.items():
            lines.append(f"   {cmd_name.upper()}:")
            lines.append(f"     Command: {validation['command']}")

            if validation['valid'] is True:
                lines.append(f"     Status: {validation['message']}")
            elif validation['valid'] is False:
                lines.append(f"     Status: {validation['message']}")
            else:
                lines.append(f"     Status: {validation['message']}")
            lines.append("")

    return lines
```

**Example output**:
```
================================================================================
🔍 Quality Commands Validation Report
================================================================================

Mode: monorepo

Projects: 2

--------------------------------------------------------------------------------
📦 PROJECT: backend
   Directory: backend/
   Type: python
   Lint Level: strict

   LINT:
     Command: cd backend && ruff check .
     Status: ✅ Properly fails (exit code: 1)

   TEST:
     Command: cd backend && pytest
     Status: ✅ Properly fails (exit code: 1)

--------------------------------------------------------------------------------
📦 PROJECT: frontend
   Directory: frontend/
   Type: node
   Lint Level: flexible

   LINT:
     Command: cd frontend && npm run lint
     Status: ✅ Properly fails (exit code: 1)

================================================================================
✅ ALL QUALITY COMMANDS VALIDATED SUCCESSFULLY
================================================================================
```

**Files to modify**:
- `resources/workflows/feature-implementation/hooks/validate_quality_commands.py`

---

### Phase 3: Monorepo Detection in Sense Command

**Goal**: Auto-detect monorepo projects and generate appropriate config structure.

#### Task 3.1: Add Monorepo Detection Logic
**File**: `resources/workflows/feature-implementation/commands/synapse/sense.md`

**New detection phase** (insert after "Analyze Project Structure"):

```markdown
## 1.5. Detect Monorepo Structure

After identifying the primary project type, scan for monorepo indicators:

### Monorepo Detection Heuristics

Run these checks to determine if project is a monorepo:

```python
import os
from pathlib import Path
from collections import defaultdict

def detect_monorepo_structure(root_dir: Path = Path.cwd()) -> dict:
    """
    Detect if project is a monorepo with multiple sub-projects.

    Returns:
        {
            "is_monorepo": bool,
            "confidence": float,  # 0.0-1.0
            "detected_projects": {
                "backend": {"directory": "backend/", "type": "python", "indicators": [...]},
                "frontend": {"directory": "frontend/", "type": "node", "indicators": [...]}
            },
            "detection_method": str
        }
    """

    # Known monorepo config files
    monorepo_markers = [
        "lerna.json", "nx.json", "pnpm-workspace.yaml",
        "turbo.json", "rush.json"
    ]

    # Check for monorepo config files
    for marker in monorepo_markers:
        if (root_dir / marker).exists():
            return detect_projects_from_config(root_dir, marker)

    # Check for multiple project configs at different depths
    project_indicators = defaultdict(list)

    # Scan for project config files
    patterns = {
        "python": ["pyproject.toml", "setup.py", "requirements.txt"],
        "node": ["package.json"],
        "rust": ["Cargo.toml"],
        "go": ["go.mod"]
    }

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip common non-project directories
        dirnames[:] = [d for d in dirnames if d not in {
            'node_modules', '.git', '.venv', 'venv', '__pycache__',
            'dist', 'build', '.tox', '.pytest_cache'
        }]

        dir_path = Path(dirpath)
        rel_path = dir_path.relative_to(root_dir)

        # Skip root directory (checked separately)
        if rel_path == Path('.'):
            continue

        # Check if this directory has project indicators
        for project_type, indicators in patterns.items():
            for indicator in indicators:
                if indicator in filenames:
                    project_indicators[str(rel_path)].append({
                        "type": project_type,
                        "indicator": indicator
                    })

    # Analyze findings
    if len(project_indicators) == 0:
        return {
            "is_monorepo": False,
            "confidence": 1.0,
            "detected_projects": {},
            "detection_method": "no_sub_projects_found"
        }

    if len(project_indicators) == 1:
        # Only one sub-project found - ambiguous
        return {
            "is_monorepo": False,
            "confidence": 0.5,
            "detected_projects": convert_indicators_to_projects(project_indicators),
            "detection_method": "single_sub_project_uncertain"
        }

    # Multiple sub-projects found - likely monorepo
    return {
        "is_monorepo": True,
        "confidence": 0.9,
        "detected_projects": convert_indicators_to_projects(project_indicators),
        "detection_method": "multiple_sub_projects"
    }

def convert_indicators_to_projects(indicators: dict) -> dict:
    """Convert detected indicators into project structure."""
    projects = {}

    for directory, indicator_list in indicators.items():
        # Use directory name as project name
        project_name = Path(directory).name

        # Determine primary project type
        type_counts = defaultdict(int)
        for indicator in indicator_list:
            type_counts[indicator["type"]] += 1

        primary_type = max(type_counts, key=type_counts.get)

        projects[project_name] = {
            "directory": str(Path(directory)) + "/",
            "type": primary_type,
            "indicators": indicator_list
        }

    return projects
```

### Interactive Clarification

If confidence is low or detection is ambiguous:

```python
detection_result = detect_monorepo_structure()

if detection_result["confidence"] < 0.7:
    print("\n⚠️  Monorepo detection is uncertain.")
    print(f"Detection method: {detection_result['detection_method']}")
    print(f"Confidence: {detection_result['confidence']:.0%}")

    if detection_result["detected_projects"]:
        print("\nDetected potential sub-projects:")
        for name, project in detection_result["detected_projects"].items():
            print(f"  - {name} ({project['directory']}) - {project['type']}")

    print("\nIs this a monorepo with multiple projects? (Y/n): ", end="")
    response = input().strip().lower()

    if response in ['y', 'yes', '']:
        is_monorepo = True
    else:
        is_monorepo = False
else:
    is_monorepo = detection_result["is_monorepo"]

if is_monorepo:
    # Continue with monorepo configuration
    projects_to_configure = detection_result["detected_projects"]

    # Ask user to confirm/modify project list
    print("\nConfiguring as monorepo with these projects:")
    for name, project in projects_to_configure.items():
        print(f"  ✓ {name} ({project['directory']}) - {project['type']}")

    print("\nProceed with these projects? (Y/n): ", end="")
    if input().strip().lower() not in ['y', 'yes', '']:
        print("Please manually edit .synapse/config.json after generation.")
```
```

**Files to modify**:
- `resources/workflows/feature-implementation/commands/synapse/sense.md`

---

#### Task 3.2: Generate Monorepo Config Structure
**File**: `resources/workflows/feature-implementation/commands/synapse/sense.md`

**Update config generation section**:

```markdown
## 4. Update Synapse Configuration

Based on monorepo detection results:

### Single Project Mode

If `is_monorepo == False`:

```json
{
  "quality-config": {
    "mode": "single",
    "projectType": "python",
    "commands": {...},
    "thresholds": {...},
    "metadata": {...}
  }
}
```

### Monorepo Mode

If `is_monorepo == True`:

```python
# Generate config for each detected project
quality_config = {
    "mode": "monorepo",
    "projects": {}
}

for project_name, project_info in detected_projects.items():
    directory = project_info["directory"]
    project_type = project_info["type"]

    # Discover commands for this project
    commands = discover_quality_commands_for_directory(directory, project_type)

    # Prefix all commands with cd to project directory
    prefixed_commands = {
        cmd_name: f"cd {directory} && {cmd}"
        for cmd_name, cmd in commands.items()
    }

    # Detect thresholds for this project
    thresholds = detect_thresholds_for_project(directory, project_type)

    quality_config["projects"][project_name] = {
        "directory": directory,
        "projectType": project_type,
        "commands": prefixed_commands,
        "thresholds": thresholds,
        "metadata": {
            "generated": datetime.now().isoformat(),
            "detectedFiles": project_info.get("indicators", [])
        }
    }
```

### Command Discovery Per Project

For each project, discover commands by:

1. **Change to project directory**:
   ```python
   os.chdir(project_directory)
   ```

2. **Run discovery** (existing logic):
   - Look for lint configs
   - Find test runners
   - Detect build commands
   - Check coverage tools

3. **Prefix commands** with directory change:
   ```python
   discovered_command = "ruff check ."
   final_command = f"cd {directory} && {discovered_command}"
   ```

4. **Validate command works**:
   ```python
   # Test command runs successfully
   result = subprocess.run(final_command, shell=True, capture_output=True)
   ```

5. **Return to root**:
   ```python
   os.chdir(root_directory)
   ```
```

**Files to modify**:
- `resources/workflows/feature-implementation/commands/synapse/sense.md`

---

#### Task 3.3: Update Validation Step in Sense
**File**: `resources/workflows/feature-implementation/commands/synapse/sense.md`

**Update Final Step 2** to handle both modes:

```markdown
### Final Step 2: Validate Quality Commands

**CRITICAL**: After validating the config structure, validate quality commands.

The validation script automatically detects mode and validates accordingly:
- **Single mode**: Validates project commands
- **Monorepo mode**: Validates all project commands

```python
import subprocess
import sys

validation_script = "resources/workflows/feature-implementation/hooks/validate_quality_commands.py"

try:
    result = subprocess.run(
        [sys.executable, validation_script],
        cwd=".",
        timeout=180,  # Increased timeout for monorepos
        capture_output=False,
        text=True
    )

    if result.returncode == 0:
        print("\n✅ Quality commands validation passed")
    else:
        print("\n❌ Quality commands validation FAILED!")
        print("\n⚠️  CRITICAL: Your quality gates are NOT properly configured!")
        print("   Review the failures above for each project.")
        print("\n   REQUIRED ACTION:")
        print("   1. Fix the quality tool configurations shown above")
        print("   2. Re-run this '/synapse:sense' command")

except subprocess.TimeoutExpired:
    print("\n⚠️  Validation timed out - this may indicate an issue with your quality commands")
except Exception as e:
    print(f"\n⚠️  Could not run validation: {e}")
```
```

**Files to modify**:
- `resources/workflows/feature-implementation/commands/synapse/sense.md`

---

### Phase 4: Hook Updates for Monorepo Support

**Goal**: Update quality gate hooks to run checks for all projects in monorepo mode.

#### Task 4.1: Update Implementer Post-Tool-Use Hook
**File**: `resources/workflows/feature-implementation/hooks/implementer-post-tool-use.py`

**Changes**:

1. **Update `load_quality_config()` to detect mode**:
```python
def load_quality_config():
    """Load and validate quality configuration."""
    # ... existing validation logic ...

    quality_config = config.get("quality-config")
    if not quality_config:
        return None

    mode = quality_config.get("mode", "single")
    print(f"📋 Quality config mode: {mode}", file=sys.stderr)

    return quality_config
```

2. **Refactor `check_quality_gates()` to support both modes**:
```python
def check_quality_gates():
    """Check all quality gates using configuration file."""
    config = load_quality_config()
    if not config:
        return None, {}

    mode = config.get("mode", "single")

    if mode == "single":
        return check_single_project_gates(config)
    elif mode == "monorepo":
        return check_monorepo_gates(config)
    else:
        print(f"❌ Unknown quality config mode: {mode}", file=sys.stderr)
        return None, {}
```

3. **Extract current logic to `check_single_project_gates()`**:
```python
def check_single_project_gates(config: Dict[str, Any]) -> Tuple[Optional[Dict], Dict]:
    """Check quality gates for single project."""
    # Current check_quality_gates() logic (unchanged)
    results = {}
    commands = config.get("commands", {})
    thresholds = config.get("thresholds", {})
    lint_level = thresholds.get("lintLevel", "strict")

    # ... run each command ...

    return config, results
```

4. **Add new `check_monorepo_gates()` function**:
```python
def check_monorepo_gates(config: Dict[str, Any]) -> Tuple[Optional[Dict], Dict]:
    """Check quality gates for all projects in monorepo."""
    projects = config.get("projects", {})

    if not projects:
        print("❌ No projects configured in monorepo", file=sys.stderr)
        return None, {}

    print(f"🔍 Checking quality gates for {len(projects)} project(s)...", file=sys.stderr)
    print("", file=sys.stderr)

    all_results = {
        "mode": "monorepo",
        "projects": {}
    }

    overall_pass = True

    for project_name, project_config in projects.items():
        print(f"📦 Project: {project_name} ({project_config.get('directory', 'N/A')})", file=sys.stderr)
        print("-" * 60, file=sys.stderr)

        project_results = check_project_gates(
            project_name,
            project_config
        )

        all_results["projects"][project_name] = project_results

        # Check if any gates failed for this project
        failures = [
            gate for gate, status in project_results.items()
            if gate in ["lint", "typecheck", "test", "build", "coverage"]
            and status == "FAIL"
        ]

        if failures:
            overall_pass = False
            print(f"❌ {project_name}: {', '.join(failures)} failed", file=sys.stderr)
        else:
            passing = [
                gate for gate, status in project_results.items()
                if gate in ["lint", "typecheck", "test", "build", "coverage"]
                and status == "PASS"
            ]
            if passing:
                print(f"✅ {project_name}: {', '.join(passing)} passed", file=sys.stderr)

        print("", file=sys.stderr)

    if not overall_pass:
        return config, all_results

    return config, all_results

def check_project_gates(project_name: str, project_config: Dict[str, Any]) -> Dict[str, Any]:
    """Check quality gates for a single project in monorepo."""
    results = {}
    commands = project_config.get("commands", {})
    thresholds = project_config.get("thresholds", {})
    lint_level = thresholds.get("lintLevel", "strict")

    # Run quality checks (same logic as single mode)
    quality_checks = [
        ("lint", commands.get("lint"), thresholds.get("lintTimeout", 30)),
        ("typecheck", commands.get("typecheck"), thresholds.get("typecheckTimeout", 30)),
        ("test", commands.get("test"), thresholds.get("testTimeout", 60)),
        ("build", commands.get("build"), thresholds.get("buildTimeout", 120))
    ]

    for check_name, command, timeout in quality_checks:
        if command:
            print(f"  🔍 Running {check_name}: {command}", file=sys.stderr)
            status, output = run_quality_command(check_name, command, timeout, lint_level)
            results[check_name] = status

            if status == "FAIL":
                results[f"{check_name}_output"] = output
                print(f"  ❌ {check_name} failed", file=sys.stderr)
            elif status == "PASS":
                print(f"  ✅ {check_name} passed", file=sys.stderr)
            elif status == "SKIP":
                print(f"  ⏭️  {check_name} skipped: {output}", file=sys.stderr)

    # Coverage check
    coverage_cmd = commands.get("coverage")
    if coverage_cmd:
        print(f"  📊 Running coverage: {coverage_cmd}", file=sys.stderr)
        # ... coverage logic (same as single mode) ...

    return results
```

5. **Update `main()` to handle monorepo results**:
```python
def main():
    """Main entry point."""
    # ... existing setup ...

    config, quality_results = check_quality_gates()

    if config is None:
        # No commands configured
        print("✅ No quality commands configured", file=sys.stderr)
        sys.exit(1)

    mode = config.get("mode", "single")

    if mode == "single":
        failures = [
            gate for gate, status in quality_results.items()
            if gate in ["lint", "typecheck", "test", "build", "coverage"]
            and status == "FAIL"
        ]

        if failures:
            # ... existing single mode failure logic ...
            pass

    elif mode == "monorepo":
        # Collect failures across all projects
        all_failures = {}

        for project_name, project_results in quality_results.get("projects", {}).items():
            failures = [
                gate for gate, status in project_results.items()
                if gate in ["lint", "typecheck", "test", "build", "coverage"]
                and status == "FAIL"
            ]

            if failures:
                all_failures[project_name] = failures

        if all_failures:
            # Format failure details per project
            failure_details = []

            for project_name, failures in all_failures.items():
                failure_details.append(f"\n\n📦 {project_name.upper()} - FAILURES: {', '.join(failures)}")

                for gate in failures:
                    output_key = f"{gate}_output"
                    project_results = quality_results["projects"][project_name]

                    if output_key in project_results:
                        error_lines = project_results[output_key].strip().split('\n')[:10]
                        failure_details.append(f"\n{gate.upper()}:")
                        failure_details.append("\n".join(error_lines))

            reason = f"""Quality gates failed for {len(all_failures)} project(s)

❌ The implementer's changes did not pass quality checks.

REQUIRED ACTION: Re-invoke the "implementer" sub-agent with these instructions:
- Fix the quality gate failures for each project listed below
- Provide the specific error details to guide the fixes

FAILURES BY PROJECT:{''.join(failure_details)}"""

            output = {"decision": "block", "reason": reason}
            print(json.dumps(output))
            sys.exit(2)

    # All passed
    print("REQUIRED: Use \"verifier\" sub-agent to verify \"implementer\"'s results.", file=sys.stderr)
    sys.exit(1)
```

**Files to modify**:
- `resources/workflows/feature-implementation/hooks/implementer-post-tool-use.py`

---

### Phase 5: Testing & Documentation

#### Task 5.1: Create Test Monorepo Fixture
**Directory**: `tests/fixtures/test-monorepo/`

**Structure**:
```
tests/fixtures/test-monorepo/
├── .synapse/
│   └── config.json          # Monorepo config
├── backend/
│   ├── pyproject.toml
│   ├── src/
│   │   └── main.py
│   └── tests/
│       └── test_main.py
└── frontend/
    ├── package.json
    ├── src/
    │   └── index.ts
    └── tests/
        └── index.test.ts
```

**Config content**:
```json
{
  "quality-config": {
    "mode": "monorepo",
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

---

#### Task 5.2: Integration Tests
**File**: `tests/test_monorepo_validation.py`

**Test cases**:
- `test_detect_monorepo_structure()`
- `test_validate_monorepo_config()`
- `test_validate_monorepo_commands()`
- `test_monorepo_quality_gates()`
- `test_monorepo_single_project_failure()`
- `test_monorepo_multiple_project_failures()`

---

#### Task 5.3: Update Documentation
**Files to create/update**:

1. **`docs/MONOREPO_SUPPORT.md`** - User guide for monorepo configuration
2. **`README.md`** - Add monorepo section to features
3. **`CHANGELOG.md`** - Document breaking changes and new features

**Documentation should cover**:
- What monorepo support means
- How auto-detection works
- Manual configuration guide
- Migration guide (for existing users)
- Examples of different monorepo types
- Troubleshooting common issues

---

## Task Checklist

### Phase 1: Schema & Core Validation
- [ ] Task 1.1: Update Schema Definition
- [ ] Task 1.2: Update Config Validation Logic
- [ ] Task 1.3: Update Test Suite

### Phase 2: Quality Command Validation Updates
- [ ] Task 2.1: Update Validation Script Core Logic
- [ ] Task 2.2: Update Validation Reporting

### Phase 3: Monorepo Detection in Sense Command
- [ ] Task 3.1: Add Monorepo Detection Logic
- [ ] Task 3.2: Generate Monorepo Config Structure
- [ ] Task 3.3: Update Validation Step in Sense

### Phase 4: Hook Updates for Monorepo Support
- [ ] Task 4.1: Update Implementer Post-Tool-Use Hook

### Phase 5: Testing & Documentation
- [ ] Task 5.1: Create Test Monorepo Fixture
- [ ] Task 5.2: Integration Tests
- [ ] Task 5.3: Update Documentation

---

## Implementation Order

**Recommended order for minimal blocking**:

1. **Phase 1** (foundational) - Required for everything else
2. **Phase 2** (validation) - Independent, can be done in parallel with Phase 3
3. **Phase 3** (sense) - Requires Phase 1 complete
4. **Phase 4** (hooks) - Requires Phase 1 and 2 complete
5. **Phase 5** (testing/docs) - Throughout, but final pass at end

**Estimated effort**: 3-4 work sessions

---

## Breaking Changes

**No backwards compatibility concerns**, so these breaking changes are acceptable:

1. Config structure validation now requires `mode` field (defaults to "single" if missing)
2. Hook behavior changes for monorepo configs (runs all projects)
3. Validation script output format differs for monorepo mode
4. Sense command may detect monorepo and generate different structure

---

## Success Criteria

- [ ] Schema validates both single and monorepo configs
- [ ] Sense auto-detects monorepo structure with >85% accuracy
- [ ] Sense asks for clarification when confidence < 70%
- [ ] Quality command validation tests all projects in monorepo
- [ ] Implementer hook runs quality checks for all projects
- [ ] Clear error reporting shows which project failed
- [ ] Documentation covers all common monorepo patterns
- [ ] Test coverage for monorepo functionality >80%

---

## Future Enhancements (Out of Scope for v1)

- Affected-file detection (only run checks for changed projects)
- Parallel execution of project quality checks
- Project dependency awareness (run checks in dependency order)
- Workspace-level commands (commands that run across all projects)
- Per-project timeout configuration
- Selective project enabling/disabling
