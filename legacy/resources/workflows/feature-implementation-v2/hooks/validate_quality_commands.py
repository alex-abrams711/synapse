#!/usr/bin/env python3
"""
Validation script for quality gate commands.

This script validates that configured quality commands will actually fail
when they encounter errors, ensuring the quality gates work as expected.
"""

import json
import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple, Optional


# Language-specific failure injection templates
FAILURE_TEMPLATES = {
    "python": {
        "lint": {
            "file": "test_lint.py",
            "content": """# This file has intentional lint errors
def badFunction( ):  # Bad spacing
    unused_var = 1
    x=2+3  # No spaces around operators
    return x
"""
        },
        "typecheck": {
            "file": "test_typecheck.py",
            "content": """# This file has intentional type errors
def add_numbers(a: int, b: int) -> int:
    return a + b

# Type error: passing string instead of int
result: int = add_numbers("not", "numbers")
"""
        },
        "test": {
            "file": "test_failing.py",
            "content": """# This file has an intentionally failing test
def test_should_fail():
    assert 1 == 2, "This test is designed to fail"
"""
        },
        "build": {
            "file": "test_syntax.py",
            "content": """# This file has syntax errors
def broken_function()
    return "missing colon"
"""
        },
        "coverage": {
            "file": "test_coverage.py",
            "content": """# Test file that won't meet coverage thresholds
def uncovered_function():
    return "This function is never tested"

def test_nothing():
    pass
"""
        }
    },
    "node": {
        "lint": {
            "file": "test-lint.js",
            "content": """// Intentional lint errors
const unused = 1;
function badFunction( ){
    var x=2+3
    return x
}
"""
        },
        "typecheck": {
            "file": "test-typecheck.ts",
            "content": """// Intentional type errors
function addNumbers(a: number, b: number): number {
    return a + b;
}

const result: number = addNumbers("not", "numbers");
"""
        },
        "test": {
            "file": "test-failing.test.js",
            "content": """// Intentionally failing test
test('should fail', () => {
    expect(1).toBe(2);
});
"""
        },
        "build": {
            "file": "test-syntax.js",
            "content": """// Syntax error
function broken() {
    return "missing bracket"
"""
        },
        "coverage": {
            "file": "test-coverage.js",
            "content": """// Low coverage code
function uncovered() {
    return "never tested";
}

test('minimal test', () => {
    expect(true).toBe(true);
});
"""
        }
    },
    "rust": {
        "lint": {
            "file": "src/lib.rs",
            "content": """// Intentional clippy warnings
pub fn bad_function() {
    let unused = 1;
    let x = if true { 1 } else { 1 }; // Useless if statement
}
"""
        },
        "test": {
            "file": "src/lib.rs",
            "content": """#[cfg(test)]
mod tests {
    #[test]
    fn it_fails() {
        assert_eq!(1, 2);
    }
}
"""
        },
        "build": {
            "file": "src/lib.rs",
            "content": """// Syntax error
pub fn broken() {
    let x = 1
}
"""
        }
    },
    "go": {
        "lint": {
            "file": "main.go",
            "content": """package main

// Intentional lint issues
func badFunction() {
    unused := 1
    _ = unused
}
"""
        },
        "test": {
            "file": "main_test.go",
            "content": """package main

import "testing"

func TestFail(t *testing.T) {
    if 1 != 2 {
        t.Error("This test should fail")
    }
}
"""
        },
        "build": {
            "file": "main.go",
            "content": """package main

// Syntax error
func broken() {
    x := 1
"""
        }
    }
}


def load_quality_config(config_path: str = ".synapse/config.json") -> Optional[Dict[str, Any]]:
    """Load quality configuration from Synapse config file."""
    if not os.path.exists(config_path):
        return None

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config.get("quality-config")
    except Exception as e:
        print(f"❌ Error loading config: {e}", file=sys.stderr)
        return None


def detect_project_type(quality_config: Dict[str, Any]) -> str:
    """Detect project type from quality config."""
    project_type = quality_config.get("projectType", "").lower()

    # Map project types to template keys
    if "python" in project_type:
        return "python"
    elif "node" in project_type or "typescript" in project_type or "javascript" in project_type:
        return "node"
    elif "rust" in project_type:
        return "rust"
    elif "go" in project_type or "golang" in project_type:
        return "go"
    else:
        # Default to python for unknown types
        return "python"


def create_failure_environment(project_type: str, command_type: str, temp_dir: Path) -> Optional[Path]:
    """
    Create a temporary environment with intentional failures.

    Returns the path to the created file, or None if template not available.
    """
    templates = FAILURE_TEMPLATES.get(project_type, {})
    template = templates.get(command_type)

    if not template:
        return None

    file_path = temp_dir / template["file"]

    # Create parent directories if needed
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the failing code
    with open(file_path, 'w') as f:
        f.write(template["content"])

    return file_path


def run_command_in_temp_dir(command: str, temp_dir: Path, timeout: int = 30) -> Tuple[int, str]:
    """
    Run a command in the temporary directory.

    Returns (exit_code, output).
    """
    try:
        # Replace any references to original directory with temp directory
        # Handle commands that cd into subdirectories
        adjusted_command = command

        result = subprocess.run(
            adjusted_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(temp_dir)
        )

        output = result.stdout + result.stderr
        return result.returncode, output

    except subprocess.TimeoutExpired:
        return -1, f"Command timed out after {timeout}s"
    except Exception as e:
        return -1, f"Error running command: {e}"


def validate_command(
    command_name: str,
    command: str,
    project_type: str,
    lint_level: str = "strict"
) -> Tuple[bool, str]:
    """
    Validate that a quality command properly fails when it should.

    Returns (is_valid, message).
    """
    if not command:
        return True, "No command configured (skipped)"

    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        # Create failure environment
        created_file = create_failure_environment(project_type, command_name, temp_dir)

        if not created_file:
            return None, f"⚠️  No validation template available for {command_name} on {project_type}"

        # Copy necessary config files if they exist in the project
        config_files = {
            "python": ["setup.py", "pyproject.toml", "pytest.ini", "setup.cfg"],
            "node": ["package.json", "tsconfig.json", "jest.config.js", ".eslintrc.js", ".eslintrc.json"],
            "rust": ["Cargo.toml"],
            "go": ["go.mod", "go.sum"]
        }

        for config_file in config_files.get(project_type, []):
            if os.path.exists(config_file):
                try:
                    shutil.copy(config_file, temp_dir / config_file)
                except Exception:
                    pass  # Not critical if copy fails

        # Run the command
        exit_code, output = run_command_in_temp_dir(command, temp_dir)

        # Validate the result based on command type
        if command_name == "lint":
            if lint_level == "strict":
                # In strict mode, should fail on warnings or errors
                if exit_code == 0:
                    # Check if output contains warnings
                    output_lower = output.lower()
                    has_warnings = any(w in output_lower for w in [
                        'warning:', 'warn:', 'warnings:', '[warn]', 'warning found'
                    ])

                    if has_warnings:
                        return True, "✅ Properly detects warnings in strict mode"
                    else:
                        return False, (
                            "❌ FAILED: Command returned exit code 0 with no warnings detected.\n"
                            "   Expected: Non-zero exit code OR warnings in output for lint errors.\n"
                            "   This means the lint command will NOT block on lint issues!"
                        )
                else:
                    return True, f"✅ Properly fails (exit code: {exit_code})"
            else:
                # Flexible mode: should pass on warnings, fail on errors
                # For validation, we just check it can detect something
                if exit_code != 0:
                    return True, f"✅ Properly detects lint issues (exit code: {exit_code})"
                else:
                    return False, (
                        "❌ FAILED: Command returned exit code 0.\n"
                        "   Expected: Non-zero exit code for lint errors.\n"
                        "   This means the lint command will NOT block on lint issues!"
                    )

        else:
            # For other commands, should fail (non-zero exit code)
            if exit_code != 0:
                return True, f"✅ Properly fails (exit code: {exit_code})"
            else:
                return False, (
                    f"❌ FAILED: Command returned exit code 0 when it should have failed.\n"
                    f"   Expected: Non-zero exit code for {command_name} failures.\n"
                    f"   This means the {command_name} command will NOT block on issues!"
                )


def get_quality_config_mode(quality_config: Dict[str, Any]) -> str:
    """Determine if config is single or monorepo mode."""
    return quality_config.get("mode", "single")


def validate_single_project(quality_config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate quality commands for single-project configuration.

    Returns (all_valid, results_dict).
    """
    # Get project type and commands
    project_type = detect_project_type(quality_config)
    commands = quality_config.get("commands", {})
    thresholds = quality_config.get("thresholds", {})
    lint_level = thresholds.get("lintLevel", "strict")

    if not commands:
        return False, {
            "error": "No quality commands configured",
            "message": "Run '/synapse:sense' to generate quality configuration"
        }

    # Validate each command
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
            elif is_valid is None:
                # Warning but not a failure
                pass

    return all_valid, results


def validate_monorepo_projects(quality_config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate quality commands for monorepo configuration.

    Returns (all_valid, results_dict).
    """
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
                elif is_valid is None:
                    # Warning but not a failure
                    pass

        results["projects"][project_name] = project_results

    return all_valid, results


def validate_all_commands(config_path: str = ".synapse/config.json") -> Tuple[bool, Dict[str, Any]]:
    """
    Validate all configured quality commands.

    Returns (all_valid, results_dict).
    """
    # Load config
    quality_config = load_quality_config(config_path)
    if not quality_config:
        return False, {
            "error": "Quality config not found",
            "message": "Run '/synapse:sense' to generate quality configuration"
        }

    # Detect mode
    mode = get_quality_config_mode(quality_config)

    if mode == "single":
        return validate_single_project(quality_config)
    elif mode == "monorepo":
        return validate_monorepo_projects(quality_config)
    else:
        return False, {
            "error": f"Unknown mode: {mode}",
            "message": "Mode must be 'single' or 'monorepo'"
        }


def format_single_project_report(results: Dict[str, Any]) -> list:
    """Format single-project validation results."""
    lines = []

    lines.append(f"Project Type: {results.get('project_type', 'unknown')}")
    lines.append(f"Lint Level: {results.get('lint_level', 'strict')}")
    lines.append("")
    lines.append("Validation Results:")
    lines.append("-" * 80)

    validations = results.get("validations", {})

    if not validations:
        lines.append("  ℹ️  No quality commands configured")
        lines.append("")
        return lines

    for cmd_name, validation in validations.items():
        lines.append(f"\n{cmd_name.upper()}:")
        lines.append(f"  Command: {validation['command']}")

        if validation['valid'] is True:
            lines.append(f"  Status: {validation['message']}")
        elif validation['valid'] is False:
            lines.append(f"  Status: {validation['message']}")
        else:
            lines.append(f"  Status: {validation['message']}")

    return lines


def format_monorepo_report(results: Dict[str, Any]) -> list:
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
        lines.extend(format_single_project_report(results))
    elif mode == "monorepo":
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
        lines.append("")
        lines.append("This means your quality gates may allow broken code through.")
        lines.append("")
        lines.append("REQUIRED ACTION:")
        lines.append("  1. Review the failed validations above")
        lines.append("  2. Run '/synapse:sense' to regenerate your quality configuration")
        lines.append("  3. Ensure your quality tools are properly installed and configured")
        lines.append("")
        lines.append("Common issues:")
        lines.append("  - Lint command doesn't fail on errors (check your lint config)")
        lines.append("  - Test command doesn't fail on test failures (check test runner)")
        lines.append("  - Commands are using wrong flags or options")

    lines.append("=" * 80)

    return "\n".join(lines)


def main():
    """Main entry point for validation script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate quality gate commands are properly configured"
    )
    parser.add_argument(
        "--config",
        default=".synapse/config.json",
        help="Path to Synapse config file"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )

    args = parser.parse_args()

    # Run validation
    all_valid, results = validate_all_commands(args.config)

    if args.json:
        # Output JSON for programmatic use
        print(json.dumps({
            "valid": all_valid,
            "results": results
        }, indent=2))
    else:
        # Output human-readable report
        report = format_validation_report(all_valid, results)
        print(report)

    # Exit with appropriate code
    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
