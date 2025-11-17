#!/usr/bin/env python3
"""Post-tool-use hook for feature-planning workflow

Validates that the writer sub-agent has properly formatted the task list
according to the required structure with mandatory status fields.
"""
import json
import sys
import os
import re
from typing import List, Tuple


def validate_status_field(
    line_num: int,
    status_code: str,
    status_value: str,
    current_task_code: str,
    expected_suffix: str,
    status_name: str,
    valid_statuses: List[str],
    errors: List[str],
    warnings: List[str]
) -> None:
    """Validate a status field (Dev/QA/UV).

    Args:
        line_num: Line number in the file
        status_code: Actual status code from the file
        status_value: Status value (e.g., "Not Started")
        current_task_code: Current task code (e.g., "T001")
        expected_suffix: Expected code suffix (e.g., "DS", "QA", "UV")
        status_name: Human-readable status name (e.g., "Dev Status")
        valid_statuses: List of valid status values
        errors: List to append errors to
        warnings: List to append warnings to
    """
    expected_status_code = f"{current_task_code}-{expected_suffix}"
    if status_code != expected_status_code:
        errors.append(
            f"Line {line_num}: {status_name} code '{status_code}' doesn't match task code. "
            f"Expected '{expected_status_code}'"
        )

    if status_value not in valid_statuses:
        valid_str = ", ".join(valid_statuses)
        warnings.append(
            f"Line {line_num}: {status_name} has non-standard value '{status_value}' "
            f"(expected: {valid_str})"
        )


def validate_task_format(file_path: str) -> Tuple[bool, List[str]]:
    """Validate task list format according to writer.md specification.

    Args:
        file_path: Path to the tasks file to validate

    Returns:
        Tuple of (is_valid, error_messages)
    """
    if not os.path.exists(file_path):
        return False, [f"File not found: {file_path}"]

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        return False, [f"Error reading file: {e}"]

    errors = []
    warnings = []
    tasks_found = []
    current_task_line = None
    current_task_code = None
    current_task_has_ds = False
    current_task_has_qa = False
    current_task_has_uv = False
    expected_task_num = 1

    # Patterns for validation with task codes
    # Task format: [ ] - T001 - Task description
    task_pattern = re.compile(r'^(\[ \]|\[x\]|\[X\]) - (T\d{3,}) - (.+)$')

    # Subtask format (indented): [ ] - T001-ST001 - Subtask description
    subtask_pattern = re.compile(r'^  (\[ \]|\[x\]|\[X\]) - (T\d{3,}-ST\d{3,}) - (.+)$')

    # Status patterns (indented) with codes
    # [ ] - T001-DS - Dev Status: [Not Started]
    # [ ] - T001-QA - QA Status: [Not Started]
    # [ ] - T001-UV - User Verification Status: [Not Started]
    ds_status_pattern = re.compile(r'^  (\[ \]|\[x\]|\[X\]) - (T\d{3,}-DS) - Dev Status: \[(.+?)\]$')
    qa_status_pattern = re.compile(r'^  (\[ \]|\[x\]|\[X\]) - (T\d{3,}-QA) - QA Status: \[(.+?)\]$')
    uv_status_pattern = re.compile(r'^  (\[ \]|\[x\]|\[X\]) - (T\d{3,}-UV) - User Verification Status: \[(.+?)\]$')

    for i, line in enumerate(lines, 1):
        line_num = i
        line_stripped = line.rstrip()

        # Skip empty lines and markdown headers/formatting
        if not line_stripped or line_stripped.startswith('#') or line_stripped.startswith('```'):
            continue

        # Check for top-level task
        task_match = task_pattern.match(line_stripped)
        if task_match:
            # Before starting new task, check if previous task had required fields
            if current_task_line is not None:
                if not current_task_has_ds:
                    errors.append(f"Line {current_task_line}: Task {current_task_code} missing required 'Dev Status' field with code {current_task_code}-DS")
                if not current_task_has_qa:
                    errors.append(f"Line {current_task_line}: Task {current_task_code} missing required 'QA Status' field with code {current_task_code}-QA")
                if not current_task_has_uv:
                    errors.append(f"Line {current_task_line}: Task {current_task_code} missing required 'User Verification Status' field with code {current_task_code}-UV")

            # Start tracking new task
            task_code = task_match.group(2)
            task_desc = task_match.group(3)

            # Validate task code format and sequencing
            expected_code = f"T{expected_task_num:03d}"
            if task_code != expected_code:
                errors.append(f"Line {line_num}: Task code '{task_code}' is incorrect. Expected '{expected_code}' (tasks must be sequential and zero-padded)")

            tasks_found.append((line_num, task_code, task_desc))
            current_task_line = line_num
            current_task_code = task_code
            current_task_has_ds = False
            current_task_has_qa = False
            current_task_has_uv = False
            expected_task_num += 1
            continue

        # Check for status fields (only valid within a task)
        if current_task_line is not None:
            # Check for Dev Status
            ds_match = ds_status_pattern.match(line_stripped)
            if ds_match:
                current_task_has_ds = True
                validate_status_field(
                    line_num=line_num,
                    status_code=ds_match.group(2),
                    status_value=ds_match.group(3),
                    current_task_code=current_task_code,
                    expected_suffix="DS",
                    status_name="Dev Status",
                    valid_statuses=['Not Started', 'In Progress', 'Complete'],
                    errors=errors,
                    warnings=warnings
                )
                continue

            # Check for QA Status (supports Failed - {reason} pattern)
            qa_match = qa_status_pattern.match(line_stripped)
            if qa_match:
                current_task_has_qa = True
                qa_status_value = qa_match.group(3)

                # QA Status validation - allow Failed - {reason} pattern
                valid_qa_statuses = ['Not Started', 'Passed', 'Complete']
                is_valid_qa = (
                    qa_status_value in valid_qa_statuses or
                    qa_status_value.startswith('Failed - ')
                )

                # If not valid, use validate_status_field with base valid statuses
                if not is_valid_qa:
                    validate_status_field(
                        line_num=line_num,
                        status_code=qa_match.group(2),
                        status_value=qa_status_value,
                        current_task_code=current_task_code,
                        expected_suffix="QA",
                        status_name="QA Status",
                        valid_statuses=valid_qa_statuses + ['Failed - {reason}'],
                        errors=errors,
                        warnings=warnings
                    )
                else:
                    # Still validate the status code
                    expected_status_code = f"{current_task_code}-QA"
                    if qa_match.group(2) != expected_status_code:
                        errors.append(
                            f"Line {line_num}: QA Status code '{qa_match.group(2)}' doesn't match task code. "
                            f"Expected '{expected_status_code}'"
                        )
                continue

            # Check for User Verification Status
            uv_match = uv_status_pattern.match(line_stripped)
            if uv_match:
                current_task_has_uv = True
                validate_status_field(
                    line_num=line_num,
                    status_code=uv_match.group(2),
                    status_value=uv_match.group(3),
                    current_task_code=current_task_code,
                    expected_suffix="UV",
                    status_name="User Verification Status",
                    valid_statuses=['Not Started', 'Complete'],
                    errors=errors,
                    warnings=warnings
                )
                continue

            # Check for subtasks - validate code format matches parent task
            subtask_match = subtask_pattern.match(line_stripped)
            if subtask_match:
                subtask_code = subtask_match.group(2)
                # Verify subtask code starts with current task code
                if not subtask_code.startswith(f"{current_task_code}-ST"):
                    errors.append(f"Line {line_num}: Subtask code '{subtask_code}' doesn't match parent task code '{current_task_code}'. Expected format: '{current_task_code}-ST###'")
                continue

    # Check last task
    if current_task_line is not None:
        if not current_task_has_ds:
            errors.append(f"Line {current_task_line}: Task {current_task_code} missing required 'Dev Status' field with code {current_task_code}-DS")
        if not current_task_has_qa:
            errors.append(f"Line {current_task_line}: Task {current_task_code} missing required 'QA Status' field with code {current_task_code}-QA")
        if not current_task_has_uv:
            errors.append(f"Line {current_task_line}: Task {current_task_code} missing required 'User Verification Status' field with code {current_task_code}-UV")

    # Check if any tasks were found
    if not tasks_found:
        errors.append("No tasks found in file. Expected format: [ ] - T001 - Task description")

    # Combine errors and warnings
    all_messages = errors + warnings
    is_valid = len(errors) == 0

    return is_valid, all_messages


def main():
    print("🔍 Running task writer validation hook...", file=sys.stderr)

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(0)  # Don't block on JSON errors

    # Parse PostToolUse data
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only process Task tool calls
    if tool_name != "Task":
        print("Not a Task tool call - skipping.", file=sys.stderr)
        sys.exit(0)

    # Extract subagent_type from tool_input
    subagent_type = tool_input.get("subagent_type", "")

    # Only process writer subagent
    if subagent_type != "writer":
        print(f"Not a writer completion (subagent_type: {subagent_type}) - skipping.", file=sys.stderr)
        sys.exit(0)

    print("📝 Writer completion detected - validating task format...", file=sys.stderr)

    # Look for common task file locations in the current directory and subdirectories
    task_files_to_validate = []

    # Check if any common task file exists
    for pattern in ["tasks.md", "TASKS.md"]:
        if os.path.exists(pattern):
            task_files_to_validate.append(pattern)

    # Check openspec pattern
    if os.path.exists("openspec/changes"):
        for change_dir in os.listdir("openspec/changes"):
            tasks_path = os.path.join("openspec/changes", change_dir, "tasks.md")
            if os.path.exists(tasks_path):
                task_files_to_validate.append(tasks_path)

    # Check specs pattern
    if os.path.exists("specs"):
        for spec_dir in os.listdir("specs"):
            tasks_path = os.path.join("specs", spec_dir, "tasks.md")
            if os.path.exists(tasks_path):
                task_files_to_validate.append(tasks_path)

    if not task_files_to_validate:
        print("⚠️ No task files found to validate.", file=sys.stderr)
        print("💡 Expected task files: tasks.md, openspec/changes/*/tasks.md, or specs/*/tasks.md", file=sys.stderr)
        sys.exit(0)

    # Validate all found task files
    all_valid = True
    all_errors = []

    for task_file in task_files_to_validate:
        print(f"📋 Validating {task_file}...", file=sys.stderr)
        is_valid, messages = validate_task_format(task_file)

        if not is_valid:
            all_valid = False
            all_errors.append(f"\n❌ Validation failed for {task_file}:")
            all_errors.extend([f"  {msg}" for msg in messages])
        else:
            print(f"✅ {task_file} is properly formatted", file=sys.stderr)
            if messages:  # Print warnings
                for msg in messages:
                    print(f"⚠️  {msg}", file=sys.stderr)

    if not all_valid:
        reason = """Task format validation failed.

The writer sub-agent must format tasks according to the specification:

Required format for each task:
```
[ ] - T001 - Task description
  [ ] - T001-ST001 - Subtask 1
  [ ] - T001-ST002 - Subtask 2
  [ ] - T001-DS - Dev Status: [Not Started]
  [ ] - T001-QA - QA Status: [Not Started]
  [ ] - T001-UV - User Verification Status: [Not Started]

[ ] - T002 - Task description
  [ ] - T002-ST001 - Subtask 1
  [ ] - T002-DS - Dev Status: [Not Started]
  [ ] - T002-QA - QA Status: [Not Started]
  [ ] - T002-UV - User Verification Status: [Not Started]
```

Key requirements:
- Task codes must be sequential and zero-padded (T001, T002, T003...)
- Subtask codes must match parent task and be sequential per-task (T001-ST001, T001-ST002...)
- Status codes must match parent task code (T001-DS, T001-QA, T001-UV)
- All three status fields (Dev, QA, User Verification) are REQUIRED for each task

REQUIRED ACTION: Re-invoke the "writer" sub-agent with instructions to fix the formatting issues below.

FORMATTING ISSUES:
""" + "\n".join(all_errors)

        output = {
            "decision": "block",
            "reason": reason
        }
        print(json.dumps(output))
        sys.exit(2)

    # Validation passed
    print("✅ All task files are properly formatted", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
