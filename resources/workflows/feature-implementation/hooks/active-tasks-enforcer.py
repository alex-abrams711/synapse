#!/usr/bin/env python3
"""
PreToolUse Hook - Active Tasks Enforcer

Ensures active_tasks is set before editing source code files.
Prevents work from being done without proper tracking and verification.

Exit Codes:
  0 - Success: Either active_tasks is set OR file is not a source file
  2 - Block: Attempting to edit source code without active_tasks set
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional


# Timeout protection (30 seconds max)
import signal


def timeout_handler(signum, frame):
    print("ERROR: Hook timed out after 30 seconds", file=sys.stderr)
    sys.exit(0)  # Don't block on timeout


signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)


# Early logging
print("🔍 Active tasks enforcer: Checking if work tracking is enabled...", file=sys.stderr)


# Reserved task codes that don't need to exist in tasks.md
# These are special codes for ad-hoc work that still requires tracking
RESERVED_TASK_CODES = {"ADHOC"}


# File patterns that are considered "source code" requiring active_tasks
SOURCE_EXTENSIONS = {
    # Programming languages
    '.py', '.js', '.ts', '.tsx', '.jsx', '.mjs', '.cjs',
    '.java', '.kt', '.scala',
    '.go',
    '.rs',
    '.c', '.cpp', '.cc', '.h', '.hpp',
    '.cs',
    '.rb',
    '.php',
    '.swift',
    '.m', '.mm',

    # Web/Style
    '.html', '.htm', '.vue', '.svelte',
    '.css', '.scss', '.sass', '.less',

    # Data/Config that affects functionality
    '.sql',
    '.graphql', '.gql',

    # Shell scripts
    '.sh', '.bash', '.zsh',
}

# File patterns that should NEVER require active_tasks (allowed without tracking)
ALWAYS_ALLOW_PATTERNS = [
    '.synapse/',           # Workflow config
    '.claude/',            # Claude config
    'README.md',           # Documentation
    'CHANGELOG.md',
    'CONTRIBUTING.md',
    'LICENSE',
    '.gitignore',
    '.env.example',
    '.env.sample',
    'docs/',               # Documentation directories
    'doc/',
    '.vscode/',            # IDE config
    '.idea/',
    '.git/',               # Git internals
]

# Task file patterns (should be allowed - managed by planning workflow)
TASK_FILE_PATTERNS = [
    'tasks.md',
    'openspec/changes/',
    'specs/',
]


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


def get_active_tasks(config: Optional[Dict]) -> List[str]:
    """Extract active_tasks from config."""
    if not config:
        return []

    workflow = config.get("third_party_workflow")
    if not workflow:
        return []

    return workflow.get("active_tasks", [])


def get_project_paths(config: Optional[Dict]) -> List[str]:
    """Extract project paths from quality-config for smarter detection."""
    if not config:
        return []

    quality_config = config.get("quality-config", {})
    mode = quality_config.get("mode", "single")

    paths = []

    if mode == "monorepo":
        projects = quality_config.get("projects", {})
        for project_name, project_config in projects.items():
            project_path = project_config.get("path")
            if project_path:
                paths.append(project_path)
    elif mode == "single":
        # Single mode - check for explicit path or use root
        project = config.get("project", {})
        root_dir = project.get("root_directory", ".")
        if root_dir and root_dir != ".":
            paths.append(root_dir)

    return paths


def is_always_allowed(file_path: str) -> bool:
    """Check if file matches always-allowed patterns."""
    normalized_path = file_path.replace('\\', '/')

    for pattern in ALWAYS_ALLOW_PATTERNS:
        if pattern in normalized_path:
            return True

    return False


def is_task_file(file_path: str) -> bool:
    """Check if file is a task file (should be allowed)."""
    normalized_path = file_path.replace('\\', '/')

    for pattern in TASK_FILE_PATTERNS:
        if pattern in normalized_path:
            return True

    return False


def is_source_file(file_path: str, project_paths: List[str]) -> bool:
    """
    Determine if file is a source file requiring active_tasks.

    Logic:
    1. If in always-allowed patterns → NOT source
    2. If is task file → NOT source
    3. If has source extension → IS source
    4. If in project paths (from quality-config) → IS source
    5. Otherwise → NOT source (conservative)
    """
    # Check always-allowed patterns
    if is_always_allowed(file_path):
        return False

    # Check task file patterns
    if is_task_file(file_path):
        return False

    # Check file extension
    path_obj = Path(file_path)
    extension = path_obj.suffix.lower()

    if extension in SOURCE_EXTENSIONS:
        return True

    # Check if file is within project paths
    if project_paths:
        normalized_file = os.path.normpath(file_path)
        for project_path in project_paths:
            normalized_project = os.path.normpath(project_path)
            try:
                # Check if file is under project path
                Path(normalized_file).relative_to(normalized_project)
                return True
            except ValueError:
                # Not under this project path
                continue

    # Conservative default: not a source file
    return False


def generate_block_message(file_path: str, tool_name: str) -> str:
    """Generate concise block message."""
    lines = []
    lines.append("")
    lines.append("="*70)
    lines.append("❌ EDIT BLOCKED - Active Tasks Not Set")
    lines.append("="*70)
    lines.append("")
    lines.append(f"Cannot edit source file: {file_path}")
    lines.append("")
    lines.append("Set active_tasks in .synapse/config.json before editing source code.")
    lines.append("")
    lines.append('For planned tasks: "active_tasks": ["T001", "T002"]')
    lines.append('For ad-hoc work:   "active_tasks": ["ADHOC"]')
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

    # Parse PreToolUse data
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only process Edit and Write tool calls
    if tool_name not in ["Edit", "Write"]:
        print(f"Not an Edit/Write tool call (tool: {tool_name}) - allowing.", file=sys.stderr)
        sys.exit(0)

    # Extract file path
    file_path = tool_input.get("file_path", "")
    if not file_path:
        print("No file_path in tool input - allowing.", file=sys.stderr)
        sys.exit(0)

    # Load config
    config = load_config()

    # Get active_tasks
    active_tasks = get_active_tasks(config)

    # If active_tasks is set, allow all edits
    if active_tasks:
        # Check if using reserved codes
        reserved_in_use = [t for t in active_tasks if t in RESERVED_TASK_CODES]
        if reserved_in_use:
            print(f"✅ Active tasks set ({', '.join(active_tasks)}) - allowing edit (ad-hoc work).", file=sys.stderr)
        else:
            print(f"✅ Active tasks set ({len(active_tasks)} tasks) - allowing edit.", file=sys.stderr)
        sys.exit(0)

    print(f"⚠️  No active tasks set - checking if {file_path} is source file...", file=sys.stderr)

    # Get project paths for smarter detection
    project_paths = get_project_paths(config)

    # Check if file is a source file
    if not is_source_file(file_path, project_paths):
        print("✅ Not a source file (config/docs/tasks) - allowing edit.", file=sys.stderr)
        sys.exit(0)

    # Source file edit without active_tasks → BLOCK
    print("❌ Source file edit without active_tasks - blocking.", file=sys.stderr)
    block_message = generate_block_message(file_path, tool_name)
    print(block_message, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
