#!/usr/bin/env python3
"""
Pre-tool-use hook using Task Format Schema v2.0

This hook integrates TaskSchemaParser to block work based on task states.
Uses semantic states (not_started, in_progress, complete) for clean business logic.
"""
import json
import sys
import os
from typing import List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../src"))

from synapse_cli.parsers import (
    TaskSchemaParser,
    ParsedTask,
    SchemaValidationError,
)


def load_synapse_config():
    """Load synapse configuration from .synapse/config.json"""
    config_path = ".synapse/config.json"

    if not os.path.exists(config_path):
        print(f"⚠️  Synapse config not found at {config_path}", file=sys.stderr)
        return None

    try:
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}", file=sys.stderr)
        return None


def find_active_tasks_file(config):
    """Extract active tasks file path and schema from synapse config"""
    if not config:
        return None, None

    workflows = config.get("third_party_workflows", {}).get("detected", [])

    for workflow in workflows:
        tasks_file = workflow.get("active_tasks_file")
        if tasks_file:
            schema = workflow.get("task_format_schema")
            return tasks_file, schema

    return None, None


def check_task_blocking(
    target_task: Optional[ParsedTask], all_tasks: List[ParsedTask]
) -> Tuple[bool, str]:
    """
    Check if work should be blocked using semantic states.

    Clean business logic - works with semantic states instead of raw strings.
    """
    if not all_tasks:
        return False, ""

    if target_task:
        # Allow continued work on in-progress tasks
        if target_task.dev_state == "in_progress":
            print(
                f"✅ Allowing continued work on: {target_task.task_id}",
                file=sys.stderr,
            )
            return False, ""

        # Allow new tasks that haven't started
        if (
            target_task.dev_state == "not_started"
            and target_task.qa_state == "not_started"
            and target_task.uv_state == "not_started"
        ):
            # Check for blocking incomplete tasks
            blocking_in_progress = [
                t.task_id
                for t in all_tasks
                if t.task_id != target_task.task_id
                and t.dev_state == "in_progress"
            ]

            blocking_awaiting_qa = [
                t.task_id
                for t in all_tasks
                if t.task_id != target_task.task_id
                and t.dev_state == "complete"
                and (t.qa_state != "complete" or t.uv_state != "complete")
            ]

            if blocking_in_progress:
                return (
                    True,
                    f"Cannot start new task - others in progress: {', '.join(blocking_in_progress)}",
                )

            if blocking_awaiting_qa:
                return (
                    True,
                    f"Cannot start new task - others awaiting QA: {', '.join(blocking_awaiting_qa)}",
                )

            print(
                f"✅ Allowing work on new task: {target_task.task_id}",
                file=sys.stderr,
            )
            return False, ""

        # Block work on completed tasks awaiting QA
        if target_task.dev_state == "complete" and (
            target_task.qa_state != "complete" or target_task.uv_state != "complete"
        ):
            return (
                True,
                f"Task '{target_task.task_id}' needs QA/verification before re-implementation",
            )

    else:
        # No clear target task - check for any incomplete work
        blocking = [
            t.task_id
            for t in all_tasks
            if t.dev_state == "in_progress"
            or (
                t.dev_state == "complete"
                and (t.qa_state != "complete" or t.uv_state != "complete")
            )
        ]

        if blocking:
            return (
                True,
                f"Cannot start work - incomplete tasks: {', '.join(blocking)}",
            )

    return False, ""


def find_matching_task(
    prompt: str, parsed_tasks: List[ParsedTask]
) -> Optional[ParsedTask]:
    """Find which task the implementer is trying to work on"""
    if not parsed_tasks:
        return None

    prompt_lower = prompt.lower()

    # Try exact task ID matching first
    for task in parsed_tasks:
        if task.task_id.lower() in prompt_lower:
            print(
                f"✅ Found exact task ID match: {task.task_id}", file=sys.stderr
            )
            return task

    # Try keyword matching
    best_match = None
    best_score = 0

    for task in parsed_tasks:
        score = sum(1 for keyword in task.keywords if keyword in prompt_lower)
        if score > best_score:
            best_score = score
            best_match = task

    if best_match and best_score > 0:
        print(
            f"✅ Found keyword match: {best_match.task_id} (score: {best_score})",
            file=sys.stderr,
        )
        return best_match

    print("❓ No clear task match found", file=sys.stderr)
    return None


def main():
    print("🔍 Running task implementer pre-tool gate hook...", file=sys.stderr)

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(2)

    # Only process Task tool calls for implementer subagent
    if input_data.get("tool_name") != "Task":
        sys.exit(1)

    tool_input = input_data.get("tool_input", {})
    if tool_input.get("subagent_type") != "implementer":
        sys.exit(1)

    print("🔍 Implementer task detected - analyzing...", file=sys.stderr)

    # Load config and find active tasks file
    config = load_synapse_config()
    if not config:
        print("ℹ️  No synapse config - allowing task", file=sys.stderr)
        sys.exit(1)

    tasks_file_path, schema = find_active_tasks_file(config)
    if not tasks_file_path:
        print(
            "ℹ️  No task management system - allowing task", file=sys.stderr
        )
        sys.exit(1)

    # Parse tasks using schema
    try:
        parser = TaskSchemaParser(schema)
        parsed_tasks = parser.parse_tasks_file(tasks_file_path)

        if not parsed_tasks:
            print("ℹ️  No tasks found - allowing task", file=sys.stderr)
            sys.exit(1)

        print(f"📊 Parsed {len(parsed_tasks)} tasks", file=sys.stderr)

    except SchemaValidationError as e:
        print(f"❌ Schema validation failed: {e}", file=sys.stderr)
        print(
            "ℹ️  Falling back to allow (run 'synapse sense' to fix)",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error parsing tasks: {e}", file=sys.stderr)
        sys.exit(1)

    # Find target task
    prompt = tool_input.get("prompt", "")
    target_task = find_matching_task(prompt, parsed_tasks)

    # Check blocking conditions
    should_block, reason = check_task_blocking(target_task, parsed_tasks)

    if should_block:
        print(f"❌ Blocking: {reason}", file=sys.stderr)
        output = {"decision": "block", "reason": reason}
        print(json.dumps(output))
        sys.exit(2)

    print("✅ Allowing implementer task", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
