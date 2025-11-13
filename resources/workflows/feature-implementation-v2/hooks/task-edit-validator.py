#!/usr/bin/env python3
"""
PostToolUse Hook - Task Edit Validator

Prevents agents from modifying User Verification (UV) status fields.
UV fields are USER-ONLY and should never be updated by agents.

Exit Codes:
  0 - Success: No UV field modifications detected
  2 - Block: UV field modification detected
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple


# Timeout protection (30 seconds max for quick validation)
import signal


def timeout_handler(signum, frame):
    print("ERROR: Hook timed out after 30 seconds", file=sys.stderr)
    sys.exit(0)  # Don't block on timeout


signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)


# Early logging for debugging
print("🔍 Task edit validator: Checking for UV field modifications...", file=sys.stderr)


def load_config() -> Optional[Dict]:
    """Load .synapse/config.json, return None if not found."""
    config_path = Path(".synapse/config.json")

    if not config_path.exists():
        return None

    try:
        with open(config_path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"⚠️  Invalid JSON in config.json: {e}", file=sys.stderr)
        return None


def get_task_file_path(config: Optional[Dict]) -> Optional[str]:
    """Extract task file path from config."""
    if not config:
        return None

    workflow = config.get("third_party_workflow")
    if not workflow:
        return None

    return workflow.get("active_tasks_file")


def extract_uv_fields(text: str) -> Dict[str, str]:
    """
    Extract all UV field values from text.

    Returns:
        Dict mapping task_code -> UV status value
        Example: {"T001": "Not Started", "T002": "Verified"}
    """
    # Pattern: [ ] - T001-UV - User Verification Status: [Status Value]
    uv_pattern = re.compile(
        r'^\s*\[[ xX]\]\s*-\s*(T\d{3,})-UV\s*-\s*User Verification Status:\s*\[([^\]]+)\]',
        re.MULTILINE
    )

    uv_fields = {}
    for match in uv_pattern.finditer(text):
        task_code = match.group(1)
        status_value = match.group(2)
        uv_fields[task_code] = status_value

    return uv_fields


def detect_uv_changes(old_text: str, new_text: str) -> Tuple[bool, Dict]:
    """
    Detect if UV fields were modified between old and new text.

    Returns:
        (has_changes, change_details)
    """
    old_uv = extract_uv_fields(old_text)
    new_uv = extract_uv_fields(new_text)

    changes = {}

    # Check for modified UV values
    for task_code, old_value in old_uv.items():
        new_value = new_uv.get(task_code)
        if new_value is not None and new_value != old_value:
            changes[task_code] = {
                "old": old_value,
                "new": new_value,
                "type": "modified"
            }

    # Check for added UV fields (new tasks with UV fields)
    for task_code, new_value in new_uv.items():
        if task_code not in old_uv:
            changes[task_code] = {
                "old": None,
                "new": new_value,
                "type": "added"
            }

    has_changes = len(changes) > 0
    return has_changes, changes


def generate_block_message(changes: Dict, file_path: str) -> str:
    """Generate concise block message for UV field modifications."""
    lines = []
    lines.append("")
    lines.append("="*70)
    lines.append("❌ EDIT BLOCKED - User Verification Field Modification Detected")
    lines.append("="*70)
    lines.append("")

    for task_code, change in changes.items():
        if change["type"] == "modified":
            lines.append(f"{task_code}-UV: [{change['old']}] → [{change['new']}]")
        elif change["type"] == "added":
            lines.append(f"{task_code}-UV: New value [{change['new']}]")

    lines.append("")
    lines.append("UV fields are USER-ONLY. Revert UV changes and update DS/QA only.")
    lines.append("")
    lines.append("="*70)

    return "\n".join(lines)


def main():
    """Main hook execution."""

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"⚠️  Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(0)  # Don't block on JSON errors

    # Parse PostToolUse data
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only process Edit and Write tool calls
    if tool_name not in ["Edit", "Write"]:
        print(f"Not an Edit/Write tool call (tool: {tool_name}) - skipping.", file=sys.stderr)
        sys.exit(0)

    # Extract file path
    file_path = tool_input.get("file_path", "")
    if not file_path:
        print("No file_path in tool input - skipping.", file=sys.stderr)
        sys.exit(0)

    # Load config to get task file path
    config = load_config()
    task_file_path = get_task_file_path(config)

    # If no config or no task file configured, allow all edits
    if not task_file_path:
        print("No task file configured - allowing edit.", file=sys.stderr)
        sys.exit(0)

    # Normalize paths for comparison
    file_path_normalized = os.path.normpath(file_path)
    task_file_path_normalized = os.path.normpath(task_file_path)

    # Only validate if editing the task file
    if file_path_normalized != task_file_path_normalized:
        print(f"Not editing task file (editing: {file_path}) - allowing.", file=sys.stderr)
        sys.exit(0)

    print(f"✓ Editing task file ({file_path}) - validating UV fields...", file=sys.stderr)

    # Handle Edit tool
    if tool_name == "Edit":
        old_string = tool_input.get("old_string", "")
        new_string = tool_input.get("new_string", "")

        if not old_string or not new_string:
            print("Missing old_string or new_string - skipping validation.", file=sys.stderr)
            sys.exit(0)

        has_changes, changes = detect_uv_changes(old_string, new_string)

    # Handle Write tool
    elif tool_name == "Write":
        # For Write, we need to compare against current file content
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            # New file being created - check if it has UV fields set to non-default
            content = tool_input.get("content", "")
            uv_fields = extract_uv_fields(content)

            # Allow if all UV fields are [Not Started] (default for new tasks)
            non_default_uv = {k: v for k, v in uv_fields.items() if v != "Not Started"}

            if non_default_uv:
                has_changes = True
                changes = {k: {"old": None, "new": v, "type": "added"} for k, v in non_default_uv.items()}
            else:
                has_changes = False
                changes = {}
        else:
            # File exists - compare old vs new
            try:
                with open(file_path_obj) as f:
                    old_content = f.read()
            except Exception as e:
                print(f"⚠️  Failed to read existing file: {e}", file=sys.stderr)
                sys.exit(0)  # Don't block on read errors

            new_content = tool_input.get("content", "")
            has_changes, changes = detect_uv_changes(old_content, new_content)

    # Determine exit code
    if has_changes:
        # Generate and print block message
        block_message = generate_block_message(changes, file_path)
        print(block_message, file=sys.stderr)
        sys.exit(2)  # Block the edit
    else:
        print("✅ No UV field modifications detected - allowing edit.", file=sys.stderr)
        sys.exit(0)  # Allow the edit


if __name__ == "__main__":
    main()
