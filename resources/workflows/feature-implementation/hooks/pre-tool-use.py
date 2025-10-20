#!/usr/bin/env python3
import json
import sys
import os
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple

@dataclass
class Task:
    """Represents a parsed task with its metadata and statuses"""
    task_id: str
    task_description: str
    dev_status: str
    qa_status: str
    user_verification_status: str
    keywords: List[str]
    line_number: int

def load_synapse_config():
    """Load synapse configuration from .synapse/config.json"""
    config_path = ".synapse/config.json"

    if not os.path.exists(config_path):
        print(f"⚠️ Synapse config not found at {config_path}", file=sys.stderr)
        print("💡 Run 'synapse sense' to generate configuration", file=sys.stderr)
        return None

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            print(f"📋 Using synapse config from {config_path}", file=sys.stderr)
            return config

    except Exception as e:
        print(f"❌ Error loading config from {config_path}: {e}", file=sys.stderr)
        return None

def find_active_tasks_file(config):
    """Extract active tasks file path from synapse config"""
    if not config:
        return None

    third_party_workflows = config.get("third_party_workflows", {})
    detected_workflows = third_party_workflows.get("detected", [])

    if not detected_workflows:
        print("ℹ️ No third-party workflows detected - no task management system", file=sys.stderr)
        return None

    # Use the first detected workflow with an active_tasks_file
    for workflow in detected_workflows:
        active_tasks_file = workflow.get("active_tasks_file")
        if active_tasks_file:
            print(f"📝 Found active tasks file: {active_tasks_file}", file=sys.stderr)
            return active_tasks_file

    print("ℹ️ No active tasks file found in workflow configuration", file=sys.stderr)
    return None

def extract_keywords_from_description(description: str) -> List[str]:
    """Extract searchable keywords from task description"""
    # Remove markdown formatting and extract meaningful words
    clean_desc = re.sub(r'\[\[|\]\]|Task \d+:|#|\*', '', description)
    words = re.findall(r'\b[a-zA-Z]{3,}\b', clean_desc.lower())

    # Filter out common stop words
    stop_words = {'the', 'and', 'for', 'with', 'that', 'this', 'are', 'will', 'can', 'should', 'must'}
    keywords = [word for word in words if word not in stop_words]

    return keywords[:10]  # Limit to top 10 keywords

def parse_tasks_with_structure(tasks_file_path: str) -> List[Task]:
    """Parse tasks.md file and extract structured task information"""
    if not os.path.exists(tasks_file_path):
        print(f"⚠️ Tasks file not found: {tasks_file_path}", file=sys.stderr)
        return []

    try:
        with open(tasks_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        print(f"📖 Parsing task structure from {tasks_file_path}", file=sys.stderr)

        tasks = []
        current_task = None

        for i, line in enumerate(lines, 1):
            line = line.rstrip()

            # Check for top-level task (starts with [ ] - [[...)
            task_match = re.match(r'^(\[ \]|\[x\]) - \[\[(.*?)\]\]', line)
            if task_match:
                # Save previous task if exists
                if current_task:
                    tasks.append(current_task)

                # Extract task ID and description
                full_desc = task_match.group(2)

                # Try to extract task ID (e.g., "Task 1:", "T-001:", etc.)
                id_match = re.match(r'^(Task \d+|T-\d+|\d+):\s*(.*)', full_desc)
                if id_match:
                    task_id = id_match.group(1)
                    task_description = id_match.group(2)
                else:
                    # Use first few words as ID if no clear pattern
                    words = full_desc.split()[:3]
                    task_id = ' '.join(words)
                    task_description = full_desc

                # Extract keywords for matching
                keywords = extract_keywords_from_description(full_desc)

                # Initialize new task
                current_task = Task(
                    task_id=task_id,
                    task_description=task_description,
                    dev_status="Not Started",
                    qa_status="Not Started",
                    user_verification_status="Not Started",
                    keywords=keywords,
                    line_number=i
                )
                continue

            # Check for status lines (indented with 2+ spaces)
            if current_task and line.startswith('  '):
                dev_match = re.search(r'Dev Status: \[(.*?)\]', line)
                if dev_match:
                    current_task.dev_status = dev_match.group(1).strip()
                    continue

                qa_match = re.search(r'QA Status: \[(.*?)\]', line)
                if qa_match:
                    current_task.qa_status = qa_match.group(1).strip()
                    continue

                user_match = re.search(r'User Verification Status: \[(.*?)\]', line)
                if user_match:
                    current_task.user_verification_status = user_match.group(1).strip()
                    continue

        # Don't forget the last task
        if current_task:
            tasks.append(current_task)

        print(f"📊 Parsed {len(tasks)} structured tasks", file=sys.stderr)
        for task in tasks:
            print(f"  - {task.task_id}: Dev={task.dev_status}, QA={task.qa_status}, User={task.user_verification_status}", file=sys.stderr)

        return tasks

    except Exception as e:
        print(f"❌ Error parsing tasks file {tasks_file_path}: {e}", file=sys.stderr)
        return []

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
    """Check if work on specific task should be blocked"""
    if not all_tasks:
        return False, ""

    if target_task:
        print(f"🎯 Checking blocking conditions for target task: {target_task.task_id}", file=sys.stderr)

        # Allow continued work on task with Dev Status "In Progress"
        if target_task.dev_status == "In Progress":
            print(f"✅ Allowing continued work on in-progress task: {target_task.task_id}", file=sys.stderr)
            return False, ""

        # Allow work on task that's ready for dev (all statuses are "Not Started")
        if (target_task.dev_status == "Not Started" and
            target_task.qa_status == "Not Started" and
            target_task.user_verification_status == "Not Started"):

            # But check if there are other incomplete tasks blocking this
            blocking_tasks = []
            for task in all_tasks:
                if task.task_id == target_task.task_id:
                    continue  # Skip the target task

                # Block if other task has incomplete pipeline
                if (task.dev_status == "Complete" and
                    (task.qa_status not in ["Not Started", "QA Passed"] or
                     task.user_verification_status not in ["Not Started", "Complete"])):
                    blocking_tasks.append(f"{task.task_id} (awaiting QA/User Verification)")
                elif task.dev_status == "In Progress":
                    blocking_tasks.append(f"{task.task_id} (dev in progress)")

            if blocking_tasks:
                reason = f"Cannot start new task '{target_task.task_id}' - other tasks need completion: {', '.join(blocking_tasks)}"
                return True, reason

            print(f"✅ Allowing work on new task: {target_task.task_id}", file=sys.stderr)
            return False, ""

        # Block work on task that's completed dev but not fully verified
        if (target_task.dev_status == "Complete" and
            (target_task.qa_status != "QA Passed" or target_task.user_verification_status != "Complete")):
            reason = f"Task '{target_task.task_id}' has completed development but needs QA/User Verification before implementer can work on it again"
            return True, reason

    else:
        # No clear target task identified - use conservative blocking
        print("🤔 No target task identified - checking for any incomplete pipelines", file=sys.stderr)

        blocking_tasks = []
        for task in all_tasks:
            if task.dev_status == "In Progress":
                blocking_tasks.append(f"{task.task_id} (dev in progress)")
            elif (task.dev_status == "Complete" and
                  (task.qa_status not in ["Not Started", "QA Passed"] or
                   task.user_verification_status not in ["Not Started", "Complete"])):
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

    # Parse structured tasks
    parsed_tasks = parse_tasks_with_structure(tasks_file_path)
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