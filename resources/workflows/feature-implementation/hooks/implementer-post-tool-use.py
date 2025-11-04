#!/usr/bin/env python3
import json
import sys
import subprocess
import os

# Import config validation
from validate_config import validate_config_for_hooks, format_validation_error

def load_quality_config():
    """Load and validate quality configuration from .synapse/config.json"""
    config_path = ".synapse/config.json"

    if not os.path.exists(config_path):
        print(f"⚠️ Synapse config not found at {config_path}", file=sys.stderr)
        print("💡 Run '/synapse:sense' to generate quality configuration", file=sys.stderr)
        return None

    # First, validate config structure
    is_valid, error_summary, detailed_issues = validate_config_for_hooks(config_path)

    if not is_valid:
        # Hard block with validation error
        error_message = format_validation_error(error_summary, detailed_issues)

        print("", file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        print(error_message, file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        print("", file=sys.stderr)

        # Return blocking JSON for Claude
        output = {
            "decision": "block",
            "reason": error_message
        }
        print(json.dumps(output))
        sys.exit(2)

    # Load config (we know it's valid now)
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            quality_config = config.get("quality-config")

            if not quality_config:
                print(f"⚠️ Quality config not found in {config_path}", file=sys.stderr)
                print("💡 Run '/synapse:sense' to generate quality configuration", file=sys.stderr)
                return None

            print(f"📋 Using quality config from {config_path}", file=sys.stderr)
            return quality_config

    except Exception as e:
        print(f"❌ Error loading config from {config_path}: {e}", file=sys.stderr)
        return None

def run_quality_command(command_name, command_str, timeout=30, lint_level="strict"):
    """Run a quality command and return result"""
    if not command_str:
        return "SKIP", "No command configured"

    try:
        # Execute command with shell to support cd, &&, and other shell features
        result = subprocess.run(
            command_str,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd()
        )

        # Handle lint level for linting commands
        if command_name == "lint":
            if lint_level == "flexible":
                # For flexible mode, only fail on errors (exit code 2), allow warnings (exit code 1)
                status = "PASS" if result.returncode in [0, 1] else "FAIL"
            else:  # strict mode
                # In strict mode, fail on ANY warnings or errors
                if result.returncode != 0:
                    status = "FAIL"
                else:
                    # Exit code 0, but check for warnings in output
                    output_text = (result.stdout + result.stderr).lower()
                    warning_indicators = [
                        'warning:',
                        'warnings:',
                        'warn:',
                        ' warning ',
                        'warnings found',
                        'warning found',
                        '[warn]',
                        '(warning)'
                    ]
                    has_warnings = any(indicator in output_text for indicator in warning_indicators)

                    if has_warnings:
                        status = "FAIL"
                        print("⚠️ Strict mode: Found warnings in lint output", file=sys.stderr)
                    else:
                        status = "PASS"
        else:
            status = "PASS" if result.returncode == 0 else "FAIL"

        output = result.stdout + result.stderr if result.returncode != 0 else result.stdout

        return status, output

    except subprocess.TimeoutExpired:
        return "FAIL", f"Command timed out after {timeout}s"
    except FileNotFoundError:
        return "SKIP", f"Command not found: {command_str}"
    except Exception as e:
        return "FAIL", f"Error running command: {e}"

def parse_coverage_output(output, coverage_thresholds):
    """Parse coverage output and check against thresholds"""
    import re

    # Try to extract coverage percentages from output
    # Common patterns: "Statements: 85%", "Lines: 90%", "Coverage: 85%"
    coverage_data = {}

    # Pattern for detailed coverage (statements, branches, functions, lines)
    detailed_patterns = {
        'statements': r'(?:statements?|stmts?)[:\s]+(\d+(?:\.\d+)?)%',
        'branches': r'(?:branches?|branch)[:\s]+(\d+(?:\.\d+)?)%',
        'functions': r'(?:functions?|funcs?)[:\s]+(\d+(?:\.\d+)?)%',
        'lines': r'(?:lines?)[:\s]+(\d+(?:\.\d+)?)%'
    }

    # Try detailed parsing first
    for metric, pattern in detailed_patterns.items():
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            coverage_data[metric] = float(match.group(1))

    # If no detailed coverage found, try simple "Coverage: X%" pattern
    if not coverage_data:
        simple_match = re.search(r'coverage[:\s]+(\d+(?:\.\d+)?)%', output, re.IGNORECASE)
        if simple_match:
            # Use the simple coverage for all metrics
            pct = float(simple_match.group(1))
            coverage_data = {
                'statements': pct,
                'branches': pct,
                'functions': pct,
                'lines': pct
            }

    # Check thresholds
    failures = []
    if isinstance(coverage_thresholds, dict):
        for metric, threshold in coverage_thresholds.items():
            if metric in coverage_data:
                if coverage_data[metric] < threshold:
                    failures.append(f"{metric}: {coverage_data[metric]}% < {threshold}%")
    else:
        # Legacy simple threshold
        overall_coverage = coverage_data.get('lines', coverage_data.get('statements', 0))
        if overall_coverage < coverage_thresholds:
            failures.append(f"coverage: {overall_coverage}% < {coverage_thresholds}%")

    return failures, coverage_data

def check_quality_gates():
    """Check all quality gates using configuration file"""
    config = load_quality_config()
    if not config:
        return None, {}

    results = {}
    commands = config.get("commands", {})
    thresholds = config.get("thresholds", {})

    # Check if any quality commands are configured
    has_any_commands = any([
        commands.get("lint"),
        commands.get("typecheck"),
        commands.get("test"),
        commands.get("build"),
        commands.get("coverage")
    ])

    if not has_any_commands:
        print("ℹ️  No quality commands configured - skipping quality checks", file=sys.stderr)
        print("💡 Add linting/testing tools and run 'synapse sense' to enable quality gates", file=sys.stderr)
        return None, {}

    # Get lint level setting
    lint_level = thresholds.get("lintLevel", "strict")

    # Run each configured quality command
    quality_checks = [
        ("lint", commands.get("lint"), thresholds.get("lintTimeout", 30)),
        ("typecheck", commands.get("typecheck"), thresholds.get("typecheckTimeout", 30)),
        ("test", commands.get("test"), thresholds.get("testTimeout", 60)),
        ("build", commands.get("build"), thresholds.get("buildTimeout", 120))
    ]

    for check_name, command, timeout in quality_checks:
        if command:
            print(f"🔍 Running {check_name}: {command}", file=sys.stderr)
            status, output = run_quality_command(check_name, command, timeout, lint_level)
            results[check_name] = status

            if status == "FAIL":
                results[f"{check_name}_output"] = output
                print(f"❌ {check_name} failed", file=sys.stderr)
            elif status == "PASS":
                print(f"✅ {check_name} passed", file=sys.stderr)
                if check_name == "lint" and lint_level == "flexible":
                    print("  (flexible mode: warnings allowed)", file=sys.stderr)
            elif status == "SKIP":
                print(f"⏭️ {check_name} skipped: {output}", file=sys.stderr)

    # Run coverage check if configured
    coverage_cmd = commands.get("coverage")
    if coverage_cmd:
        print(f"📊 Running coverage: {coverage_cmd}", file=sys.stderr)
        status, output = run_quality_command("coverage", coverage_cmd, thresholds.get("testTimeout", 60), lint_level)

        # Parse coverage and check thresholds
        if status == "PASS":
            coverage_thresholds = thresholds.get("coverage", {})

            # Handle both new detailed format and legacy simple format
            if coverage_thresholds:
                failures, coverage_data = parse_coverage_output(output, coverage_thresholds)

                if failures:
                    results["coverage"] = "FAIL"
                    results["coverage_output"] = f"Coverage thresholds not met: {'; '.join(failures)}"
                    print(f"❌ Coverage failed: {'; '.join(failures)}", file=sys.stderr)
                else:
                    results["coverage"] = "PASS"
                    # Show detailed coverage if available
                    if coverage_data:
                        coverage_summary = ", ".join([f"{k}: {v}%" for k, v in coverage_data.items()])
                        print(f"✅ Coverage passed: {coverage_summary}", file=sys.stderr)
                    else:
                        print("✅ Coverage passed", file=sys.stderr)
            else:
                results["coverage"] = "PASS"  # No thresholds configured, just check command success
                print("✅ Coverage check completed (no thresholds configured)", file=sys.stderr)
        else:
            results["coverage"] = status
            if status == "FAIL":
                results["coverage_output"] = output
                print(f"❌ Coverage command failed: {output}", file=sys.stderr)

    return config, results

def main():
    print("🔍 Running task implementer quality gate hook...", file=sys.stderr)

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(2)

    # Parse PostToolUse data
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only process Task tool calls
    if tool_name != "Task":
        print("Not a Task tool call - skipping.", file=sys.stderr)
        sys.exit(0)

    # Extract subagent_type from tool_input
    subagent_type = tool_input.get("subagent_type", "")

    # Only process implementer subagent
    if subagent_type != "implementer":
        print("Not a implementer completion - skipping.", file=sys.stderr)
        sys.exit(0)

    print("🔍 implementer completion detected - running quality gates...", file=sys.stderr)

    # Run quality gate validation
    config, quality_results = check_quality_gates()

    # If config is None, it means no commands configured (new project) - allow work
    if config is None:
        print("✅ No quality commands configured - allowing work to proceed", file=sys.stderr)
        print("REQUIRED: Use \"verifier\" sub-agent to verify \"implementer\"'s results.", file=sys.stderr)
        sys.exit(1)

    # If quality_results is empty but config exists, something went wrong
    if not quality_results:
        output = {
            "decision": "block",
            "reason": "Quality configuration exists but no checks were run. Run 'synapse sense' to regenerate configuration."
        }
        print(json.dumps(output))
        sys.exit(2)

    # Check for failures
    failures = [gate for gate, status in quality_results.items()
               if gate in ["lint", "typecheck", "test", "build", "coverage"] and status == "FAIL"]

    if failures:
        # Collect detailed failure information
        failure_details = []
        for gate in failures:
            output_key = f"{gate}_output"
            if output_key in quality_results:
                # Get more context for the implementer to act on
                error_lines = quality_results[output_key].strip().split('\n')[:10]
                failure_details.append(f"\n\n{gate.upper()} FAILURES:\n" + "\n".join(error_lines))

        # Create explicit instructions for the main agent
        reason = f"""Quality gates failed: {', '.join(failures)}

❌ The implementer's changes did not pass quality checks.

REQUIRED ACTION: You MUST re-invoke the "implementer" sub-agent with these instructions:
- Tell the implementer to fix the quality gate failures listed below
- Provide the specific error details to guide the fixes
- Do NOT make the fixes yourself - the implementer must do this work

FAILURES TO FIX:{''.join(failure_details)}"""

        output = {
            "decision": "block",
            "reason": reason
        }
        print(json.dumps(output))
        sys.exit(2)

    # If we have any results and they're all passing, log success
    if quality_results:
        passing = [gate for gate, status in quality_results.items()
                  if gate in ["lint", "typecheck", "test", "build", "coverage"] and status == "PASS"]
        if passing:
            print(f"✅ Quality gates passed: {', '.join(passing)}", file=sys.stderr)

    # Allow completion if no issues
    print("REQUIRED: Use \"verifier\" sub-agent to verify \"implementer\"'s results.", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()