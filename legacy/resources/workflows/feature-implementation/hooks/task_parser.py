#!/usr/bin/env python3
"""Shared task parsing utilities for Synapse hooks

This module provides common functionality for parsing tasks files and
matching tasks from prompts. Used by pre-tool-use.py, post-tool-use.py,
and verification-complete.py hooks.
"""
import os
import re
import json
import sys
from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class Task:
    """Represents a parsed task with its metadata and statuses"""
    task_id: str
    task_description: str

    # Raw status values from file
    dev_status: str
    qa_status: str
    user_verification_status: str

    # Checkbox states
    dev_status_checked: bool  # Checkbox state for Dev Status line
    qa_status_checked: bool  # Checkbox state for QA Status line
    user_verification_checked: bool  # Checkbox state for User Verification line

    # Semantic states (normalized) - set after parsing
    dev_state: str = "not_started"  # "not_started" | "in_progress" | "complete"
    qa_state: str = "not_started"
    uv_state: str = "not_started"

    keywords: List[str] = None
    line_number: int = 0
    qa_status_line_number: Optional[int] = None  # Line number of QA Status field

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []

def load_synapse_config() -> Optional[Dict]:
    """Load synapse configuration from .synapse/config.json

    Returns:
        Dict containing config, or None if not found/invalid
    """
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

def find_active_tasks_file(config: Dict) -> Optional[str]:
    """Extract active tasks file path from synapse config

    Args:
        config: Synapse configuration dictionary

    Returns:
        Path to active tasks file, or None if not found
    """
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
    """Extract searchable keywords from task description

    Args:
        description: Task description text

    Returns:
        List of up to 10 keywords
    """
    # Remove markdown formatting and extract meaningful words
    clean_desc = re.sub(r'\[\[|\]\]|Task \d+:|#|\*', '', description)
    words = re.findall(r'\b[a-zA-Z]{3,}\b', clean_desc.lower())

    # Filter out common stop words
    stop_words = {'the', 'and', 'for', 'with', 'that', 'this', 'are', 'will', 'can', 'should', 'must'}
    keywords = [word for word in words if word not in stop_words]

    return keywords[:10]  # Limit to top 10 keywords

def normalize_status_to_semantic(
    raw_status: str,
    field_name: str,
    config: Optional[Dict]
) -> str:
    """Normalize raw status value to semantic state using schema

    Args:
        raw_status: The status value from tasks file (e.g., "Complete", "Passed", "Done")
        field_name: Which field this is ("dev", "qa", "user_verification")
        config: Full synapse configuration dictionary with task_format_schema

    Returns:
        Semantic state: "not_started", "in_progress", or "complete"
    """
    if not config:
        # Fallback to keyword-based normalization
        status_lower = raw_status.lower()
        if any(kw in status_lower for kw in ['not start', 'pending', 'todo', 'waiting']):
            return 'not_started'
        elif any(kw in status_lower for kw in ['progress', 'working', 'active', 'ongoing']):
            return 'in_progress'
        elif any(kw in status_lower for kw in ['complete', 'done', 'finish', 'pass', 'verified']):
            return 'complete'
        return 'not_started'  # Default to not_started for unknown values

    # Extract schema from config
    workflows = config.get('third_party_workflows', {}).get('detected', [])
    if not workflows:
        return normalize_status_to_semantic(raw_status, field_name, None)

    schema = workflows[0].get('task_format_schema', {})
    if not schema:
        return normalize_status_to_semantic(raw_status, field_name, None)

    # Use schema to normalize
    status_semantics = schema.get('status_semantics', {})
    states = status_semantics.get('states', {}).get(field_name, {})

    # Check each semantic state for matching values
    for semantic_state, raw_values in states.items():
        if raw_status in raw_values:
            return semantic_state

    # Not found in schema - use fallback
    print(f"⚠️ Status '{raw_status}' for field '{field_name}' not found in schema, using fallback normalization", file=sys.stderr)
    return normalize_status_to_semantic(raw_status, field_name, None)

def get_canonical_status_value(
    semantic_state: str,
    field_name: str,
    config: Optional[Dict]
) -> str:
    """Get canonical status value for a semantic state

    Args:
        semantic_state: "not_started", "in_progress", or "complete"
        field_name: Which field ("dev", "qa", "user_verification")
        config: Full synapse configuration dictionary with task_format_schema

    Returns:
        Canonical status string (e.g., "Complete", "Passed", "Not Started")
    """
    if not config:
        # Fallback mapping
        mapping = {
            'not_started': 'Not Started',
            'in_progress': 'In Progress',
            'complete': 'Complete'
        }
        return mapping.get(semantic_state, 'Not Started')

    # Extract schema from config
    workflows = config.get('third_party_workflows', {}).get('detected', [])
    if not workflows:
        return get_canonical_status_value(semantic_state, field_name, None)

    schema = workflows[0].get('task_format_schema', {})
    if not schema:
        return get_canonical_status_value(semantic_state, field_name, None)

    status_semantics = schema.get('status_semantics', {})
    states = status_semantics.get('states', {}).get(field_name, {})

    # Get first value from the list (canonical value)
    values = states.get(semantic_state, [])
    if values:
        return values[0]

    # Fallback
    return get_canonical_status_value(semantic_state, field_name, None)

def parse_tasks_with_structure(tasks_file_path: str, config: Optional[Dict] = None) -> List[Task]:
    """Parse tasks.md file and extract structured task information

    Args:
        tasks_file_path: Path to tasks markdown file
        config: Optional synapse configuration with task_format_schema for status normalization

    Returns:
        List of parsed Task objects with normalized semantic states
    """
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

            # Check for top-level task - support two formats:
            # Format 1: [ ] - [[Task 1: Description]]
            # Format 2: - [x] T001 - Description

            task_match = re.match(r'^(\[ \]|\[x\]|\[X\]) - \[\[(.*?)\]\]', line)
            task_match_alt = re.match(r'^- (\[ \]|\[x\]|\[X\]) (T\d+) - (.+)', line)

            if task_match:
                # Format 1: [ ] - [[Task 1: Description]]
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
                    dev_status_checked=False,
                    qa_status_checked=False,
                    user_verification_checked=False,
                    keywords=keywords,
                    line_number=i
                )
                continue

            elif task_match_alt:
                # Format 2: - [x] T001 - Description
                # Save previous task if exists
                if current_task:
                    tasks.append(current_task)

                task_id = task_match_alt.group(2)  # T001, T002, etc.
                task_description = task_match_alt.group(3)

                # Extract keywords for matching
                keywords = extract_keywords_from_description(task_description)

                # Initialize new task
                current_task = Task(
                    task_id=task_id,
                    task_description=task_description,
                    dev_status="Not Started",
                    qa_status="Not Started",
                    user_verification_status="Not Started",
                    dev_status_checked=False,
                    qa_status_checked=False,
                    user_verification_checked=False,
                    keywords=keywords,
                    line_number=i
                )
                continue

            # Check for status lines (indented with 2+ spaces)
            # Support two formats:
            # Format 1: "  [ ] - Dev Status: [Complete]" (checkbox first)
            # Format 2: "  - [x] Dev Status: [Complete]" (dash first)
            if current_task and line.startswith('  '):
                # Check for Dev Status with checkbox state
                dev_match = re.match(r'^\s*(\[ \]|\[x\]|\[X\])\s*-\s*Dev Status: \[(.*?)\]', line)
                dev_match_alt = re.match(r'^\s*-\s*(\[ \]|\[x\]|\[X\])\s*Dev Status: \[(.*?)\]', line)

                if dev_match:
                    checkbox = dev_match.group(1)
                    current_task.dev_status = dev_match.group(2).strip()
                    current_task.dev_status_checked = checkbox in ['[x]', '[X]']
                    continue
                elif dev_match_alt:
                    checkbox = dev_match_alt.group(1)
                    current_task.dev_status = dev_match_alt.group(2).strip()
                    current_task.dev_status_checked = checkbox in ['[x]', '[X]']
                    continue

                # Check for QA Status with checkbox state
                qa_match = re.match(r'^\s*(\[ \]|\[x\]|\[X\])\s*-\s*QA Status: \[(.*?)\]', line)
                qa_match_alt = re.match(r'^\s*-\s*(\[ \]|\[x\]|\[X\])\s*QA Status: \[(.*?)\]', line)

                if qa_match:
                    checkbox = qa_match.group(1)
                    current_task.qa_status = qa_match.group(2).strip()
                    current_task.qa_status_checked = checkbox in ['[x]', '[X]']
                    current_task.qa_status_line_number = i
                    continue
                elif qa_match_alt:
                    checkbox = qa_match_alt.group(1)
                    current_task.qa_status = qa_match_alt.group(2).strip()
                    current_task.qa_status_checked = checkbox in ['[x]', '[X]']
                    current_task.qa_status_line_number = i
                    continue

                # Check for User Verification Status with checkbox state
                user_match = re.match(r'^\s*(\[ \]|\[x\]|\[X\])\s*-\s*User Verification Status: \[(.*?)\]', line)
                user_match_alt = re.match(r'^\s*-\s*(\[ \]|\[x\]|\[X\])\s*User Verification Status: \[(.*?)\]', line)

                if user_match:
                    checkbox = user_match.group(1)
                    current_task.user_verification_status = user_match.group(2).strip()
                    current_task.user_verification_checked = checkbox in ['[x]', '[X]']
                    continue
                elif user_match_alt:
                    checkbox = user_match_alt.group(1)
                    current_task.user_verification_status = user_match_alt.group(2).strip()
                    current_task.user_verification_checked = checkbox in ['[x]', '[X]']
                    continue

        # Don't forget the last task
        if current_task:
            tasks.append(current_task)

        # Normalize status values to semantic states
        for task in tasks:
            task.dev_state = normalize_status_to_semantic(
                task.dev_status, 'dev', config
            )
            task.qa_state = normalize_status_to_semantic(
                task.qa_status, 'qa', config
            )
            task.uv_state = normalize_status_to_semantic(
                task.user_verification_status, 'user_verification', config
            )

        print(f"📊 Parsed {len(tasks)} structured tasks", file=sys.stderr)
        for task in tasks:
            print(f"  - {task.task_id}: Dev={task.dev_status} ({task.dev_state}), QA={task.qa_status} ({task.qa_state}), User={task.user_verification_status} ({task.uv_state})", file=sys.stderr)

        return tasks

    except Exception as e:
        print(f"❌ Error parsing tasks file {tasks_file_path}: {e}", file=sys.stderr)
        return []

def find_matching_task(prompt: str, parsed_tasks: List[Task]) -> Optional[Task]:
    """Find which task matches the given prompt

    Tries exact task ID matching first, then keyword matching.

    Args:
        prompt: The agent prompt to match against
        parsed_tasks: List of parsed tasks to search

    Returns:
        Matching Task object, or None if no match found
    """
    if not parsed_tasks:
        return None

    prompt_lower = prompt.lower()

    # Try exact task ID matching first
    for task in parsed_tasks:
        if task.task_id.lower() in prompt_lower:
            print(f"✅ Found exact task ID match: {task.task_id}", file=sys.stderr)
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
        print(f"✅ Found keyword match: {best_match.task_id} (score: {best_score})", file=sys.stderr)
        return best_match

    print("❓ No clear task match found", file=sys.stderr)
    return None
