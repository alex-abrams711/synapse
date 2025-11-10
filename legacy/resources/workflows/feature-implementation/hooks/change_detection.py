#!/usr/bin/env python3
"""
Change detection module for monorepo quality check optimization.

This module provides git-based change detection to identify which projects
in a monorepo have been modified, allowing quality checks to run only on
affected projects rather than all projects.
"""

import os
import subprocess
from typing import Dict, Any, List, Set, Tuple


def get_changed_files_from_git(detection_method: str = "uncommitted") -> List[str]:
    """
    Get list of changed files using git.

    Args:
        detection_method: One of "uncommitted", "since_main", "last_commit",
                         "staged", "all_changes"

    Returns:
        List of file paths relative to repo root, or empty list if git unavailable

    Detection methods:
        - uncommitted: Changes not yet committed (git diff HEAD)
        - since_main: Changes since main/master branch (git diff origin/main...HEAD)
        - last_commit: Changes in the last commit (git diff HEAD~1...HEAD)
        - staged: Only staged changes (git diff --cached)
        - all_changes: All changes including untracked (git status --porcelain)
    """
    commands = {
        "uncommitted": ["git", "diff", "--name-only", "HEAD"],
        "since_main": ["git", "diff", "--name-only", "origin/main...HEAD"],
        "last_commit": ["git", "diff", "--name-only", "HEAD~1...HEAD"],
        "staged": ["git", "diff", "--name-only", "--cached"],
        "all_changes": ["git", "status", "--porcelain", "--untracked-files=all"]
    }

    # Try origin/main first, fall back to origin/master if main doesn't exist
    if detection_method == "since_main":
        # Try main first
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--verify", "origin/main"],
                capture_output=True,
                timeout=2,
                cwd=os.getcwd()
            )
            if result.returncode != 0:
                # Try master as fallback
                result = subprocess.run(
                    ["git", "rev-parse", "--verify", "origin/master"],
                    capture_output=True,
                    timeout=2,
                    cwd=os.getcwd()
                )
                if result.returncode == 0:
                    commands["since_main"] = ["git", "diff", "--name-only", "origin/master...HEAD"]
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            pass  # Will try with main and handle failure later

    try:
        cmd = commands.get(detection_method, commands["uncommitted"])
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5,
            cwd=os.getcwd()
        )

        if result.returncode != 0:
            return []

        # Parse output based on command
        if detection_method == "all_changes":
            # Parse git status porcelain format: "XY filename"
            # X = status in index, Y = status in working tree
            # Don't strip the whole stdout - it removes leading spaces from status codes
            lines = result.stdout.split('\n')
            files = []
            for line in lines:
                # Check if line has content (but don't strip yet - status codes matter)
                if line and len(line) > 3:
                    # Skip the first 3 characters (status codes and space)
                    # Handle renamed files: "R  old -> new"
                    if '->' in line:
                        # Extract new filename from rename
                        filename = line[3:].split('->')[-1].strip()
                    else:
                        filename = line[3:].strip()
                    if filename:
                        files.append(filename)
            return files
        else:
            # Parse git diff format: one filename per line
            return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]

    except subprocess.TimeoutExpired:
        # Git command took too long
        return []
    except subprocess.SubprocessError:
        # Git command failed
        return []
    except FileNotFoundError:
        # Git not installed
        return []
    except Exception:
        # Any other error
        return []


def normalize_path(path: str) -> str:
    """
    Normalize a file path for cross-platform comparison.

    Args:
        path: File path to normalize

    Returns:
        Normalized path with forward slashes
    """
    # Convert backslashes to forward slashes
    normalized = path.replace("\\", "/")

    # Remove leading ./ if present
    if normalized.startswith("./"):
        normalized = normalized[2:]

    return normalized


def get_affected_projects(
    projects_config: Dict[str, Any],
    optimization_config: Dict[str, Any]
) -> Tuple[Set[str], str]:
    """
    Determine which projects have been affected by recent changes.

    This function uses git to detect changed files and maps them to their
    owning projects. It includes multiple fallback mechanisms to ensure
    safety when detection is uncertain.

    Args:
        projects_config: The "projects" object from quality-config
        optimization_config: The "optimization" object from quality-config

    Returns:
        Tuple of (set of affected project names, detection reason string)

    Detection reasons:
        - "optimization disabled in config": check_affected_only is false
        - "SYNAPSE_CHECK_ALL_PROJECTS=1 environment variable": env override
        - "no changes detected (fallback to all)": git returned no changes
        - "no changes detected (configured to skip)": no changes and skip enabled
        - "git detection (METHOD)": successful detection with method name
        - "changes detected but no projects matched (fallback)": safety fallback
        - "force-check projects included": includes forced projects

    Safety features:
        - Falls back to all projects when git unavailable
        - Falls back to all projects when no changes detected (unless disabled)
        - Always includes force_check_projects
        - Handles git repository edge cases gracefully
    """
    check_affected_only = optimization_config.get("check_affected_only", True)

    # Check for manual override first
    if not check_affected_only:
        return set(projects_config.keys()), "optimization disabled in config"

    # Check environment variable override for checking all projects
    if os.getenv("SYNAPSE_CHECK_ALL_PROJECTS") == "1":
        return set(projects_config.keys()), "SYNAPSE_CHECK_ALL_PROJECTS=1 environment variable"

    # Get detection method (with environment variable override)
    detection_method = os.getenv("SYNAPSE_DETECTION_METHOD")
    if not detection_method:
        detection_method = optimization_config.get("detection_method", "uncommitted")
    else:
        # Validate environment variable value
        valid_methods = ["uncommitted", "since_main", "last_commit", "staged", "all_changes"]
        if detection_method not in valid_methods:
            # Invalid method - fall back to default
            detection_method = "uncommitted"

    # Get changed files
    changed_files = get_changed_files_from_git(detection_method)

    if not changed_files:
        # No changes detected - use fallback behavior
        fallback = optimization_config.get("fallback_to_all", True)
        if fallback:
            return set(projects_config.keys()), "no changes detected (fallback to all)"
        else:
            return set(), "no changes detected (configured to skip)"

    # Map files to projects
    affected = set()

    for file_path in changed_files:
        # Normalize the file path
        normalized_file = normalize_path(file_path)

        for project_name, project_config in projects_config.items():
            project_dir = project_config.get("directory", "")

            if not project_dir:
                continue

            # Normalize the project directory
            normalized_dir = normalize_path(project_dir)

            # Ensure directory ends with /
            if not normalized_dir.endswith("/"):
                normalized_dir += "/"

            # Check if file is within this project directory
            if normalized_file.startswith(normalized_dir):
                affected.add(project_name)
                break  # File belongs to this project, move to next file

    # Add force-check projects (e.g., shared libraries)
    force_check = optimization_config.get("force_check_projects", [])
    if force_check:
        # Only add force-check projects that exist in the config
        valid_force_check = [p for p in force_check if p in projects_config]
        affected.update(valid_force_check)

    if not affected:
        # Changes detected but no projects matched - this is unusual
        # Fall back to all projects for safety
        return set(projects_config.keys()), "changes detected but no projects matched (fallback)"

    # Build detection reason
    reason = f"git detection ({detection_method})"
    if force_check:
        reason += ", force-check projects included"

    return affected, reason


def get_verbose_detection_info(
    changed_files: List[str],
    projects_config: Dict[str, Any],
    affected_projects: Set[str]
) -> str:
    """
    Generate detailed information about change detection for debugging.

    Args:
        changed_files: List of changed files from git
        projects_config: The projects configuration
        affected_projects: Set of affected project names

    Returns:
        Formatted string with detailed detection information
    """
    lines = []
    lines.append("Change Detection Details:")
    lines.append(f"  Changed files: {len(changed_files)}")

    if changed_files:
        lines.append("  Files (first 10):")
        for f in changed_files[:10]:
            lines.append(f"    - {f}")
        if len(changed_files) > 10:
            lines.append(f"    ... and {len(changed_files) - 10} more")

    lines.append(f"  Affected projects: {len(affected_projects)}/{len(projects_config)}")
    lines.append("  Projects:")
    for project_name in sorted(affected_projects):
        project_dir = projects_config[project_name].get("directory", "N/A")
        # Count files in this project
        file_count = sum(
            1 for f in changed_files
            if normalize_path(f).startswith(normalize_path(project_dir))
        )
        lines.append(f"    - {project_name} ({project_dir}): {file_count} file(s)")

    skipped = set(projects_config.keys()) - affected_projects
    if skipped:
        lines.append(f"  Skipped projects: {len(skipped)}")
        for project_name in sorted(skipped):
            lines.append(f"    - {project_name}")

    return "\n".join(lines)


# For testing and debugging
if __name__ == "__main__":
    import sys

    # Simple CLI for testing
    if len(sys.argv) > 1:
        method = sys.argv[1]
    else:
        method = "uncommitted"

    print(f"Detection method: {method}")
    print()

    files = get_changed_files_from_git(method)
    print(f"Changed files: {len(files)}")
    for f in files[:20]:  # Show first 20
        print(f"  - {f}")
    if len(files) > 20:
        print(f"  ... and {len(files) - 20} more")
