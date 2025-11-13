#!/usr/bin/env python3
"""
Stop Hook - QA Verification Check (Option 6)

Simple hook that ONLY checks QA status of active tasks.
Does NOT run quality checks - that's the agent's job.

Exit Codes:
  0 - Success: All active tasks verified (allow stop)
  2 - Block: Verification required (at least one task needs verification)
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Timeout protection (60 seconds max)
import signal


def timeout_handler(signum, frame):
    print("ERROR: Hook timed out after 60 seconds", file=sys.stderr)
    sys.exit(2)


signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(60)


# Early logging for debugging
print("🔍 Stop hook: QA verification check starting...", file=sys.stderr)


def load_config() -> Dict:
    """Load .synapse/config.json"""
    config_path = Path(".synapse/config.json")

    if not config_path.exists():
        print("ERROR: .synapse/config.json not found", file=sys.stderr)
        sys.exit(2)

    try:
        with open(config_path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in config.json: {e}", file=sys.stderr)
        sys.exit(2)


def extract_workflow_config(config: Dict) -> Tuple[Dict, List[str], str, Dict]:
    """
    Extract workflow configuration.

    Returns:
        (workflow, active_tasks, task_file, schema)
    """
    # BREAKING CHANGE: third_party_workflow is now an object, not array
    workflow = config.get("third_party_workflow")

    if not workflow:
        print("\n" + "="*70, file=sys.stderr)
        print("❌ STOP BLOCKED - No Workflow Configured", file=sys.stderr)
        print("="*70, file=sys.stderr)
        print("\nNo third_party_workflow found in config.json.", file=sys.stderr)
        print("Please run the sense command to detect and configure a workflow.", file=sys.stderr)
        print("\n" + "="*70, file=sys.stderr)
        sys.exit(2)

    active_tasks = workflow.get("active_tasks", [])
    task_file = workflow.get("active_tasks_file")
    schema = workflow.get("task_format_schema")

    if not task_file:
        print("\n" + "="*70, file=sys.stderr)
        print("❌ STOP BLOCKED - Missing Configuration", file=sys.stderr)
        print("="*70, file=sys.stderr)
        print("\nNo active_tasks_file specified in third_party_workflow.", file=sys.stderr)
        print("Please update your config.json to include active_tasks_file.", file=sys.stderr)
        print("\n" + "="*70, file=sys.stderr)
        sys.exit(2)

    if not schema:
        print("\n" + "="*70, file=sys.stderr)
        print("❌ STOP BLOCKED - Missing Schema", file=sys.stderr)
        print("="*70, file=sys.stderr)
        print("\nNo task_format_schema found in third_party_workflow.", file=sys.stderr)
        print("Cannot parse tasks without schema definition.", file=sys.stderr)
        print("\n" + "="*70, file=sys.stderr)
        sys.exit(2)

    return workflow, active_tasks, task_file, schema


def check_edge_cases(active_tasks: List[str], task_file: str) -> None:
    """Check for edge cases that should block stop."""

    # Edge case 1: No active tasks
    if not active_tasks:
        # Allow stop if no active tasks (no work to verify)
        print("✅ No active tasks set - allowing stop", file=sys.stderr)
        sys.exit(0)

    # Edge case 2: Task file doesn't exist
    task_file_path = Path(task_file)
    if not task_file_path.exists():
        print("\n" + "="*70, file=sys.stderr)
        print("❌ STOP BLOCKED - Task File Not Found", file=sys.stderr)
        print("="*70, file=sys.stderr)
        print(f"\nTask file '{task_file}' does not exist.", file=sys.stderr)
        print("Cannot verify active tasks without task file.", file=sys.stderr)
        print("\n" + "="*70, file=sys.stderr)
        sys.exit(2)


def parse_task_file(task_file: str, schema: Dict) -> Dict[str, Dict]:
    """
    Parse task file using schema patterns.

    Returns:
        Dict mapping task_code -> task_data
        Example: {"T001": {"description": "...", "fields": {"QA": "[Passed]"}}}
    """
    task_file_path = Path(task_file)

    try:
        with open(task_file_path) as f:
            content = f.read()
    except Exception as e:
        print(f"ERROR: Failed to read task file: {e}", file=sys.stderr)
        sys.exit(2)

    # Extract patterns from schema
    patterns = schema.get("patterns", {})
    task_pattern_obj = patterns.get("task_line") or patterns.get("task")
    status_field_pattern_obj = patterns.get("status_line") or patterns.get("status_field")

    # Extract regex strings from pattern objects
    task_pattern = task_pattern_obj.get("regex") if isinstance(task_pattern_obj, dict) else task_pattern_obj
    status_field_pattern = status_field_pattern_obj.get("regex") if isinstance(status_field_pattern_obj, dict) else status_field_pattern_obj

    if not task_pattern:
        print("ERROR: No task pattern in schema", file=sys.stderr)
        sys.exit(2)

    # Parse tasks
    tasks = {}
    current_task = None

    for line in content.splitlines():
        # Try to match task line
        if task_pattern:
            task_match = re.search(task_pattern, line, re.MULTILINE)
            if task_match:
                try:
                    # Try task_id first (new schema), fallback to task_code (old schema)
                    task_code = task_match.group("task_id") if "task_id" in task_match.groupdict() else task_match.group("task_code")
                    current_task = task_code
                    tasks[task_code] = {
                        "description": line.strip(),
                        "fields": {}
                    }
                except (IndexError, KeyError):
                    # Pattern doesn't have task_code/task_id group, skip
                    pass

        # Try to match status field line
        if status_field_pattern and current_task:
            field_match = re.search(status_field_pattern, line, re.MULTILINE)
            if field_match:
                try:
                    # Try field first (new schema), fallback to field_code (old schema)
                    field_code = field_match.group("field") if "field" in field_match.groupdict() else field_match.group("field_code")
                    # Try status first (new schema), fallback to status_value (old schema)
                    status_value = field_match.group("status") if "status" in field_match.groupdict() else field_match.group("status_value")
                    tasks[current_task]["fields"][field_code] = status_value
                except (IndexError, KeyError):
                    # Pattern doesn't have required groups, skip
                    pass

    return tasks


def check_qa_status(
    active_tasks: List[str],
    parsed_tasks: Dict[str, Dict],
    schema: Dict,
    config: Dict
) -> Tuple[bool, List[str]]:
    """
    Check QA status for all active tasks.

    Returns:
        (all_verified, tasks_needing_verification)
    """
    status_semantics = schema.get("status_semantics", {})
    field_mapping = status_semantics.get("field_mapping", {})
    qa_field_codes = field_mapping.get("qa", ["QA Status"])
    qa_field_code = qa_field_codes[0] if isinstance(qa_field_codes, list) else qa_field_codes

    qa_states = status_semantics.get("states", {}).get("qa", {})

    not_verified_values = qa_states.get("not_verified", ["Not Started"])
    verified_success_values = qa_states.get("verified_success", ["Complete", "Passed"])
    verified_failure_pattern = qa_states.get("verified_failure_pattern", "^Failed - .*")

    tasks_needing_verification = []

    for task_code in active_tasks:
        # Edge case 3: Task not found in file
        if task_code not in parsed_tasks:
            print(f"\n⚠️  Task {task_code} in active_tasks not found in task file", file=sys.stderr)
            tasks_needing_verification.append({
                "code": task_code,
                "reason": "Task not found in file",
                "description": "Unknown"
            })
            continue

        task_data = parsed_tasks[task_code]
        qa_status = task_data["fields"].get(qa_field_code)

        # Edge case 4: QA Status field missing
        if qa_status is None:
            print(f"\n⚠️  Task {task_code} missing QA Status field", file=sys.stderr)
            tasks_needing_verification.append({
                "code": task_code,
                "reason": "Missing QA Status field",
                "description": task_data["description"]
            })
            continue

        # Check if verified
        is_verified = False

        # Check verified success
        if qa_status in verified_success_values:
            is_verified = True
            print(f"✅ Task {task_code}: QA Status = {qa_status} (verified success)", file=sys.stderr)

        # Check verified failure
        elif re.match(verified_failure_pattern, qa_status):
            is_verified = True
            print(f"✅ Task {task_code}: QA Status = {qa_status} (verified failure - allows stop)", file=sys.stderr)

        # Check not verified
        elif qa_status in not_verified_values:
            is_verified = False
            print(f"❌ Task {task_code}: QA Status = {qa_status} (not verified)", file=sys.stderr)

        # Unknown status - treat as not verified
        else:
            is_verified = False
            print(f"⚠️  Task {task_code}: QA Status = {qa_status} (unknown status, treating as not verified)", file=sys.stderr)

        if not is_verified:
            tasks_needing_verification.append({
                "code": task_code,
                "reason": f"QA Status = {qa_status}",
                "description": task_data["description"]
            })

    all_verified = len(tasks_needing_verification) == 0
    return all_verified, tasks_needing_verification


def generate_verification_directive(
    tasks_needing_verification: List[Dict],
    config: Dict
) -> str:
    """Generate comprehensive Exit 2 directive."""

    lines = []
    lines.append("")
    lines.append("="*70)
    lines.append("QA VERIFICATION REQUIRED")
    lines.append("="*70)
    lines.append("")
    lines.append("### Active Tasks Needing Verification")
    lines.append("")

    for task in tasks_needing_verification:
        lines.append(f"- **{task['code']}**: {task['description']}")
        lines.append(f"  - Reason: {task['reason']}")

    lines.append("")
    lines.append("### Quality Commands (from config.json)")
    lines.append("")

    quality_config = config.get("quality-config", {})
    mode = quality_config.get("mode", "single")

    if mode == "single":
        commands = quality_config.get("commands", {})
        lines.append(f"- **lint**: {commands.get('lint', 'Not configured')}")
        lines.append(f"- **test**: {commands.get('test', 'Not configured')}")
        lines.append(f"- **typecheck**: {commands.get('typecheck', 'Not configured')}")
        lines.append(f"- **coverage**: {commands.get('coverage', 'Not configured')}")
        lines.append(f"- **build**: {commands.get('build', 'Not configured')}")

    elif mode == "monorepo":
        projects = quality_config.get("projects", {})
        for project_name, project_config in projects.items():
            lines.append(f"\n**{project_name}:**")
            commands = project_config.get("commands", {})
            lines.append(f"- **lint**: {commands.get('lint', 'Not configured')}")
            lines.append(f"- **test**: {commands.get('test', 'Not configured')}")
            lines.append(f"- **typecheck**: {commands.get('typecheck', 'Not configured')}")
            lines.append(f"- **coverage**: {commands.get('coverage', 'Not configured')}")
            lines.append(f"- **build**: {commands.get('build', 'Not configured')}")

    lines.append("")
    lines.append("### Verification Process")
    lines.append("")
    lines.append("Follow these steps to verify the active tasks:")
    lines.append("")
    lines.append("1. **Run Quality Checks**")
    lines.append("   - Execute all quality commands listed above")
    lines.append("   - Capture results for each check (lint, test, typecheck, coverage, build)")
    lines.append("   - Note any failures or warnings")
    lines.append("")
    lines.append("2. **Review Implementation**")
    lines.append("   - For each task, review the code changes made")
    lines.append("   - Verify the implementation matches task requirements")
    lines.append("   - Check for edge cases and error handling")
    lines.append("   - Ensure code quality standards are met")
    lines.append("")
    lines.append("3. **Test Functionality**")
    lines.append("   - Test the implemented features manually")
    lines.append("   - If this is a web application, use the playwright MCP to test UI/UX")
    lines.append("   - Verify all acceptance criteria are satisfied")
    lines.append("   - Test error conditions and boundary cases")
    lines.append("")
    lines.append("4. **Update Task Status**")
    lines.append("   - For tasks that PASS all checks: Update QA Status to [Complete] or [Passed]")
    lines.append("   - For tasks that FAIL: Update QA Status to [Failed - {specific reason}]")
    lines.append("   - Include detailed failure information (which checks failed, error messages, line numbers)")
    lines.append("")
    lines.append("5. **Handle Failures**")
    lines.append("   - If ANY task has failures, document them clearly")
    lines.append("   - Create a detailed fix plan")
    lines.append("   - Present the plan to the user with the question:")
    lines.append('     **"Would you like me to proceed with the plan to fix the found issues?"**')
    lines.append("   - Wait for user approval before attempting fixes")
    lines.append("   - DO NOT proceed with fixes without explicit user approval")
    lines.append("")
    lines.append("6. **Present Completion Report**")
    lines.append("   - If ALL tasks pass verification, generate and present the completion report")
    lines.append("   - Use the format template below")
    lines.append("")
    lines.append("### Completion Report Format")
    lines.append("")
    lines.append("When all tasks pass verification, present a report following this structure:")
    lines.append("")
    lines.append("```markdown")
    lines.append("## ✅ QA Verification Complete - All Tasks Passed")
    lines.append("")
    lines.append("### Tasks Verified")
    lines.append("- T001: {task_description} - PASSED")
    lines.append("- T002: {task_description} - PASSED")
    lines.append("")
    lines.append("### Quality Metrics")
    lines.append("- Lint: ✅ {status/issue count}")
    lines.append("- Tests: ✅ {passed}/{total} passed")
    lines.append("- Type Check: ✅ {status}")
    lines.append("- Coverage: ✅ {percentage}% (threshold: {threshold}%)")
    lines.append("- Build: ✅ {status}")
    lines.append("")
    lines.append("### Implementation Summary")
    lines.append("{Brief narrative description of what was implemented, key changes made,")
    lines.append(" and how the implementation meets the requirements. Include any notable")
    lines.append(" technical decisions or approaches used.}")
    lines.append("```")
    lines.append("")
    lines.append("**Note:** This is a template. Adapt the actual report based on what was verified")
    lines.append("and include relevant details from your verification process.")
    lines.append("")
    lines.append("="*70)

    return "\n".join(lines)


def main():
    """Main hook execution."""

    # Load config
    config = load_config()

    # Extract workflow configuration
    workflow, active_tasks, task_file, schema = extract_workflow_config(config)

    # Check edge cases
    check_edge_cases(active_tasks, task_file)

    # Parse task file
    parsed_tasks = parse_task_file(task_file, schema)

    # Check QA status
    all_verified, tasks_needing_verification = check_qa_status(
        active_tasks, parsed_tasks, schema, config
    )

    # Determine exit code
    if all_verified:
        print("\n✅ All active tasks verified - allowing stop", file=sys.stderr)
        sys.exit(0)
    else:
        # Generate and print directive
        directive = generate_verification_directive(tasks_needing_verification, config)
        print(directive, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
