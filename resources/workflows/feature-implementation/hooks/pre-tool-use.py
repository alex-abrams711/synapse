#!/usr/bin/env python3
"""Pre-tool-use hook for blocking implementer work based on task status

This hook uses schema-aware task parsing from task_parser.py to enable
portable workflow logic across projects with different status conventions.
"""
import json
import sys
import re
from typing import List, Optional, Tuple

# Import shared task parsing utilities
from task_parser import (
    Task,
    load_synapse_config,
    find_active_tasks_file,
    parse_tasks_with_structure
)

def extract_task_reference_from_prompt(prompt: str) -> List[str]:
    """Extract potential task identifiers from implementer prompt"""
    potential_refs = []
    prompt_lower = prompt.lower()

    # Look for explicit task references
    task_patterns = [
        r'\btask\s+(\d+)\b',           # "task 1", "Task 2"
        r'\bt-(\d+)\b',                # "T-001", "t-123"
        r'\btask\s+([a-zA-Z][\w-]*)\b' # "task auth", "task user-mgmt"
    ]

    for pattern in task_patterns:
        matches = re.findall(pattern, prompt_lower)
        for match in matches:
            if isinstance(match, tuple):
                potential_refs.extend(match)
            else:
                potential_refs.append(match)

    # Extract meaningful keywords (3+ chars, not common words)
    words = re.findall(r'\b[a-zA-Z]{3,}\b', prompt_lower)
    stop_words = {'the', 'and', 'for', 'with', 'that', 'this', 'are', 'will', 'can', 'should', 'must', 'implement', 'create', 'add', 'update', 'fix'}
    keywords = [word for word in words if word not in stop_words]

    potential_refs.extend(keywords[:10])  # Add top keywords

    return list(set(potential_refs))  # Remove duplicates

def find_matching_task(prompt: str, parsed_tasks: List[Task]) -> Optional[Task]:
    """Find which task the implementer is trying to work on"""
    if not parsed_tasks:
        return None

    potential_refs = extract_task_reference_from_prompt(prompt)
    print(f"🔍 Extracted potential task references: {potential_refs}", file=sys.stderr)

    # Try exact task ID matching first
    for ref in potential_refs:
        for task in parsed_tasks:
            # Check direct ID match
            if ref.lower() in task.task_id.lower():
                print(f"✅ Found exact task ID match: '{ref}' → {task.task_id}", file=sys.stderr)
                return task

    # Try keyword matching against task keywords
    best_match = None
    best_score = 0

    for task in parsed_tasks:
        score = 0
        matched_keywords = []

        for ref in potential_refs:
            for keyword in task.keywords:
                if ref.lower() == keyword.lower() or ref.lower() in keyword.lower():
                    score += 1
                    matched_keywords.append(keyword)

        if score > best_score:
            best_score = score
            best_match = task

        if matched_keywords:
            print(f"🔍 Task '{task.task_id}' matched keywords: {matched_keywords} (score: {score})", file=sys.stderr)

    if best_match and best_score > 0:
        print(f"✅ Found best keyword match: {best_match.task_id} (score: {best_score})", file=sys.stderr)
        return best_match

    print("❓ No clear task match found - allowing as fallback", file=sys.stderr)
    return None

def check_task_specific_blocking(target_task: Optional[Task], all_tasks: List[Task]) -> Tuple[bool, str]:
    """Check if work on specific task should be blocked - uses semantic states"""
    if not all_tasks:
        return False, ""

    if target_task:
        print(f"🎯 Checking blocking conditions for target task: {target_task.task_id}", file=sys.stderr)
        print(f"   States: dev={target_task.dev_state}, qa={target_task.qa_state}, uv={target_task.uv_state}", file=sys.stderr)

        # Allow continued work on task with Dev State "in_progress"
        if target_task.dev_state == "in_progress":
            print(f"✅ Allowing continued work on in-progress task: {target_task.task_id}", file=sys.stderr)
            return False, ""

        # Allow work on task that's ready for dev (all semantic states are "not_started")
        if (target_task.dev_state == "not_started" and
            target_task.qa_state == "not_started" and
            target_task.uv_state == "not_started"):

            # But check if there are other incomplete tasks blocking this
            blocking_tasks = []
            for task in all_tasks:
                if task.task_id == target_task.task_id:
                    continue  # Skip the target task

                # Block if other task has incomplete pipeline (using semantic states)
                if (task.dev_state == "complete" and
                    (task.qa_state != "complete" or task.uv_state != "complete")):
                    blocking_tasks.append(f"{task.task_id} (awaiting QA/User Verification)")
                elif task.dev_state == "in_progress":
                    blocking_tasks.append(f"{task.task_id} (dev in progress)")

            if blocking_tasks:
                reason = f"Cannot start new task '{target_task.task_id}' - other tasks need completion: {', '.join(blocking_tasks)}"
                return True, reason

            print(f"✅ Allowing work on new task: {target_task.task_id}", file=sys.stderr)
            return False, ""

        # Block work on task that's completed dev but not fully verified
        if (target_task.dev_state == "complete" and
            (target_task.qa_state != "complete" or target_task.uv_state != "complete")):
            reason = f"Task '{target_task.task_id}' has completed development but needs QA/User Verification before implementer can work on it again"
            return True, reason

    else:
        # No clear target task identified - use conservative blocking
        print("🤔 No target task identified - checking for any incomplete pipelines", file=sys.stderr)

        blocking_tasks = []
        for task in all_tasks:
            if task.dev_state == "in_progress":
                blocking_tasks.append(f"{task.task_id} (dev in progress)")
            elif (task.dev_state == "complete" and
                  (task.qa_state != "complete" or task.uv_state != "complete")):
                blocking_tasks.append(f"{task.task_id} (awaiting QA/User Verification)")

        if blocking_tasks:
            reason = f"Cannot start work - incomplete task pipelines found: {', '.join(blocking_tasks)}. Please complete existing tasks first."
            return True, reason

    return False, ""

def main():
    print("🔍 Running task implementer pre-tool gate hook...", file=sys.stderr)

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(2)

    # Parse PreToolUse data
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
        print("Not an implementer task call - skipping.", file=sys.stderr)
        sys.exit(0)

    print("🔍 Implementer task call detected - analyzing task requirements...", file=sys.stderr)

    # Load synapse configuration
    config = load_synapse_config()
    if not config:
        # If no config, we can't check task status, so allow (user needs to run synapse sense first)
        print("ℹ️ No synapse configuration - allowing task to proceed", file=sys.stderr)
        sys.exit(0)

    # Find active tasks file
    tasks_file_path = find_active_tasks_file(config)
    if not tasks_file_path:
        # No task management system detected, allow task to proceed
        print("ℹ️ No task management system detected - allowing task to proceed", file=sys.stderr)
        sys.exit(0)

    # Parse structured tasks with schema-aware normalization
    parsed_tasks = parse_tasks_with_structure(tasks_file_path, config)
    if not parsed_tasks:
        # No tasks found or error parsing, allow task to proceed
        print("ℹ️ No structured tasks found - allowing task to proceed", file=sys.stderr)
        sys.exit(0)

    # Extract implementer prompt for task matching
    implementer_prompt = tool_input.get("prompt", "")
    if not implementer_prompt:
        print("⚠️ No implementer prompt found - using conservative blocking", file=sys.stderr)

    # Find which task the implementer is trying to work on
    target_task = find_matching_task(implementer_prompt, parsed_tasks)

    # Check task-specific blocking conditions
    should_block, reason = check_task_specific_blocking(target_task, parsed_tasks)

    if should_block:
        print(f"❌ Blocking implementer task: {reason}", file=sys.stderr)
        output = {
            "decision": "block",
            "reason": reason
        }
        print(json.dumps(output))
        sys.exit(2)

    # Allow task to proceed
    if target_task:
        print(f"✅ Allowing implementer to work on task: {target_task.task_id}", file=sys.stderr)
    else:
        print("✅ No blocking conditions found - allowing implementer task to proceed", file=sys.stderr)
    sys.exit(0)

if __name__ == "__main__":
    main()
