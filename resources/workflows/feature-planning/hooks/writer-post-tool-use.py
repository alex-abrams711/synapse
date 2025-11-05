#!/usr/bin/env python3
"""Post-tool-use hook for feature-planning workflow

Validates that the writer sub-agent has properly formatted the task list
according to the required structure with mandatory status fields.
"""
import json
import sys
import os
import re
from typing import List, Dict, Optional, Tuple


def parse_tool_output_for_file_path(tool_input: Dict, tool_result: str) -> Optional[str]:
    """Extract file path from Write/Edit tool usage.

    Args:
        tool_input: The tool input dict containing parameters
        tool_result: The tool result string

    Returns:
        File path that was written/edited, or None
    """
    # Check for file_path in tool_input (both Write and Edit tools use this)
    if "file_path" in tool_input:
        return tool_input["file_path"]

    return None


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
    current_task_has_qa = False
    current_task_has_uv = False
    line_num = 0

    # Patterns for validation
    # Writer format: [ ] - [[Task description]] or [ ] - [[Task 1: Description]]
    task_pattern = re.compile(r'^(\[ \]|\[x\]|\[X\]) - \[\[(.+?)\]\]$')

    # Subtask format (indented): [ ] - [[Subtask description]]
    subtask_pattern = re.compile(r'^  (\[ \]|\[x\]|\[X\]) - \[\[(.+?)\]\]$')

    # Status patterns (indented)
    # Format 1: [ ] - QA Status: [Not Started]
    # Format 2: [ ] - QA Status: [Not Started/In Progress/Complete]
    qa_status_pattern = re.compile(r'^  (\[ \]|\[x\]|\[X\]) - QA Status: \[(.+?)\]$')
    uv_status_pattern = re.compile(r'^  (\[ \]|\[x\]|\[X\]) - User Verification Status: \[(.+?)\]$')

    # Also support format without checkbox
    qa_status_alt_pattern = re.compile(r'^  - QA Status: \[(.+?)\]$')
    uv_status_alt_pattern = re.compile(r'^  - User Verification Status: \[(.+?)\]$')

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
                if not current_task_has_qa:
                    errors.append(f"Line {current_task_line}: Task missing required 'QA Status' field")
                if not current_task_has_uv:
                    errors.append(f"Line {current_task_line}: Task missing required 'User Verification Status' field")

            # Start tracking new task
            task_desc = task_match.group(2)
            tasks_found.append((line_num, task_desc))
            current_task_line = line_num
            current_task_has_qa = False
            current_task_has_uv = False
            continue

        # Check for status fields (only valid within a task)
        if current_task_line is not None:
            # Check for QA Status
            qa_match = qa_status_pattern.match(line_stripped) or qa_status_alt_pattern.match(line_stripped)
            if qa_match:
                status_value = qa_match.group(2) if qa_match.lastindex >= 2 else qa_match.group(1)
                current_task_has_qa = True

                # Validate status value
                valid_statuses = ['Not Started', 'In Progress', 'Complete']
                if status_value not in valid_statuses:
                    warnings.append(f"Line {line_num}: QA Status has non-standard value '{status_value}' (expected: Not Started, In Progress, or Complete)")
                continue

            # Check for User Verification Status
            uv_match = uv_status_pattern.match(line_stripped) or uv_status_alt_pattern.match(line_stripped)
            if uv_match:
                status_value = uv_match.group(2) if uv_match.lastindex >= 2 else uv_match.group(1)
                current_task_has_uv = True

                # Validate status value
                valid_statuses = ['Not Started', 'Complete']
                if status_value not in valid_statuses:
                    warnings.append(f"Line {line_num}: User Verification Status has non-standard value '{status_value}' (expected: Not Started or Complete)")
                continue

            # Check for subtasks (these are valid, just continue)
            if subtask_pattern.match(line_stripped):
                continue

    # Check last task
    if current_task_line is not None:
        if not current_task_has_qa:
            errors.append(f"Line {current_task_line}: Task missing required 'QA Status' field")
        if not current_task_has_uv:
            errors.append(f"Line {current_task_line}: Task missing required 'User Verification Status' field")

    # Check if any tasks were found
    if not tasks_found:
        errors.append("No tasks found in file. Expected format: [ ] - [[Task description]]")

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
    tool_result = input_data.get("tool_result", "")

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

    # Look at the tool result to find file operations
    # The tool_result contains the agent's final report, we need to parse it for file paths
    # Since we don't have direct access to what files were modified, we'll need to look at
    # common task file locations or extract from the result

    # Common task file locations to check
    possible_task_files = [
        "tasks.md",
        "TASKS.md",
        "openspec/changes/*/tasks.md",
        "specs/*/tasks.md"
    ]

    # Try to find task files in the current directory and subdirectories
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
[ ] - [[Task description]]
  [ ] - [[Subtask 1]]
  [ ] - [[Subtask 2]]
  [ ] - QA Status: [Not Started]
  [ ] - User Verification Status: [Not Started]
```

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
