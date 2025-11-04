#!/usr/bin/env python3
"""Synapse CLI - AI-first workflow system with quality gates."""

__version__ = "0.1.0"

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Set


def get_resources_dir() -> Path:
    """Get the resources directory from the installed package.

    Resources are now at the package root level, not inside the CLI module.
    """
    # The package is installed at src/synapse_cli/
    # Resources are at the package root: <install_prefix>/resources/
    package_dir = Path(__file__).parent  # src/synapse_cli/

    # Try relative to package installation
    # When installed via pip, the structure is:
    # site-packages/synapse_cli/__init__.py
    # site-packages/../../../resources/ (for editable installs)
    # OR for wheel installs: site-packages/synapse_resources/

    # First try looking for adjacent resources directory (editable install)
    resources_dir = package_dir.parent.parent / "resources"

    # If not found, try installed package data location
    if not resources_dir.exists():
        # Check if resources are bundled with the package
        resources_dir = package_dir.parent / "synapse_resources"

    if not resources_dir.exists():
        print(f"Error: Resources directory not found.", file=sys.stderr)
        print(f"Searched locations:", file=sys.stderr)
        print(f"  - {package_dir.parent.parent / 'resources'}", file=sys.stderr)
        print(f"  - {package_dir.parent / 'synapse_resources'}", file=sys.stderr)
        sys.exit(1)

    return resources_dir


def get_workflows_dir() -> Path:
    """Get the workflows directory from resources.

    Returns:
        Path to the workflows directory

    Raises:
        SystemExit: If workflows directory doesn't exist
    """
    resources_dir = get_resources_dir()
    workflows_dir = resources_dir / "workflows"

    if not workflows_dir.exists():
        print(f"Error: Workflows directory not found at {workflows_dir}", file=sys.stderr)
        sys.exit(1)

    return workflows_dir


def discover_workflows() -> List[str]:
    """Discover available workflows by scanning the workflows directory.

    Returns:
        List of workflow names (directory names)
    """
    workflows_dir = get_workflows_dir()

    # Get all subdirectories that contain a settings.json file
    workflows = []
    for item in workflows_dir.iterdir():
        if item.is_dir() and (item / "settings.json").exists():
            workflows.append(item.name)

    return sorted(workflows)


def validate_workflow_exists(workflow_name: str) -> bool:
    """Validate that a workflow exists.

    Args:
        workflow_name: Name of the workflow to validate

    Returns:
        True if workflow exists, False otherwise
    """
    workflows_dir = get_workflows_dir()
    workflow_dir = workflows_dir / workflow_name

    return workflow_dir.is_dir() and (workflow_dir / "settings.json").exists()


def get_workflow_info(workflow_name: str) -> Optional[Dict]:
    """Get workflow metadata from settings.json.

    Args:
        workflow_name: Name of the workflow

    Returns:
        Dictionary with workflow metadata, or None if not found
    """
    workflows_dir = get_workflows_dir()
    settings_file = workflows_dir / workflow_name / "settings.json"

    if not settings_file.exists():
        return None

    try:
        with open(settings_file, 'r') as f:
            settings = json.load(f)
            return settings.get("workflow_metadata", {})
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not read workflow metadata: {e}", file=sys.stderr)
        return None


def get_config_path(target_dir: Path = None) -> Path:
    """Get the path to the synapse config file.

    Args:
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        Path to the config.json file
    """
    if target_dir is None:
        target_dir = Path.cwd()

    return target_dir / ".synapse" / "config.json"


def load_config(target_dir: Path = None) -> Optional[Dict]:
    """Load the synapse config file.

    Args:
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        Dictionary with config data, or None if config doesn't exist or is invalid
    """
    config_path = get_config_path(target_dir)

    if not config_path.exists():
        return None

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not read synapse config: {e}", file=sys.stderr)
        return None


def save_config(config: Dict, target_dir: Path = None) -> bool:
    """Save the synapse config file.

    Args:
        config: Config data to save
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        True if successful, False otherwise
    """
    config_path = get_config_path(target_dir)

    # Ensure .synapse directory exists
    synapse_dir = config_path.parent
    if not synapse_dir.exists():
        try:
            synapse_dir.mkdir(parents=True)
        except IOError as e:
            print(f"Error: Could not create .synapse directory: {e}", file=sys.stderr)
            return False

    # Validate config can be serialized
    try:
        config_json = json.dumps(config, indent=2)
    except (TypeError, ValueError) as e:
        print(f"Error: Config cannot be serialized to JSON: {e}", file=sys.stderr)
        return False

    # Write config
    try:
        with open(config_path, 'w') as f:
            f.write(config_json)
            f.write('\n')  # Add trailing newline
        return True
    except IOError as e:
        print(f"Error: Could not write synapse config: {e}", file=sys.stderr)
        return False


def get_manifest_path(target_dir: Path = None) -> Path:
    """Get the path to the workflow manifest file.

    Args:
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        Path to the workflow-manifest.json file
    """
    if target_dir is None:
        target_dir = Path.cwd()

    return target_dir / ".synapse" / "workflow-manifest.json"


def load_manifest(target_dir: Path = None) -> Optional[Dict]:
    """Load the workflow manifest file.

    Args:
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        Dictionary with manifest data, or None if manifest doesn't exist or is invalid
    """
    manifest_path = get_manifest_path(target_dir)

    if not manifest_path.exists():
        return None

    try:
        with open(manifest_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not read workflow manifest: {e}", file=sys.stderr)
        return None


def save_manifest(manifest: Dict, target_dir: Path = None) -> bool:
    """Save the workflow manifest file.

    Args:
        manifest: Manifest data to save
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        True if successful, False otherwise
    """
    manifest_path = get_manifest_path(target_dir)

    # Ensure .synapse directory exists
    synapse_dir = manifest_path.parent
    if not synapse_dir.exists():
        try:
            synapse_dir.mkdir(parents=True)
        except IOError as e:
            print(f"Error: Could not create .synapse directory: {e}", file=sys.stderr)
            return False

    # Validate manifest can be serialized
    try:
        manifest_json = json.dumps(manifest, indent=2)
    except (TypeError, ValueError) as e:
        print(f"Error: Manifest cannot be serialized to JSON: {e}", file=sys.stderr)
        return False

    # Write manifest
    try:
        with open(manifest_path, 'w') as f:
            f.write(manifest_json)
            f.write('\n')  # Add trailing newline
        return True
    except IOError as e:
        print(f"Error: Could not write workflow manifest: {e}", file=sys.stderr)
        return False


def update_config_workflow_tracking(
    workflow_name: str,
    target_dir: Path = None
) -> bool:
    """Update config.json workflow tracking when applying a workflow.

    Args:
        workflow_name: Name of the workflow being applied
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        True if successful, False otherwise
    """
    if target_dir is None:
        target_dir = Path.cwd()

    # Load existing config
    config = load_config(target_dir)
    if config is None:
        print("Warning: Could not load config.json for workflow tracking", file=sys.stderr)
        return False

    # Update active workflow
    config['workflows']['active_workflow'] = workflow_name

    # Add to applied workflows history with timestamp
    workflow_entry = {
        'name': workflow_name,
        'applied_at': datetime.now().isoformat()
    }

    # Check if workflow already in history (avoid duplicates)
    applied_workflows = config['workflows'].get('applied_workflows', [])
    if not any(w.get('name') == workflow_name for w in applied_workflows):
        applied_workflows.append(workflow_entry)
        config['workflows']['applied_workflows'] = applied_workflows

    # Save updated config
    return save_config(config, target_dir)


def clear_config_workflow_tracking(target_dir: Path = None) -> bool:
    """Clear active workflow from config.json when removing a workflow.

    Args:
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        True if successful, False otherwise
    """
    if target_dir is None:
        target_dir = Path.cwd()

    # Load existing config
    config = load_config(target_dir)
    if config is None:
        print("Warning: Could not load config.json for workflow tracking", file=sys.stderr)
        return False

    # Clear active workflow
    config['workflows']['active_workflow'] = None

    # Keep applied_workflows history intact for audit trail

    # Save updated config
    return save_config(config, target_dir)


def create_manifest(
    workflow_name: str,
    copied_files: Dict[str, List[Path]],
    hooks_added: List[Dict],
    settings_updated: List[str],
    target_dir: Path = None
) -> Dict:
    """Create a new workflow manifest.

    Args:
        workflow_name: Name of the workflow being applied
        copied_files: Dictionary mapping directory type to list of copied file paths
        hooks_added: List of hook definitions that were added to settings.json
        settings_updated: List of setting keys that were updated in settings.json
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        Dictionary containing the manifest data
    """
    if target_dir is None:
        target_dir = Path.cwd()

    # Flatten copied files and convert to relative paths for portability
    all_copied_files = []
    for dir_type, file_list in copied_files.items():
        for file_path in file_list:
            try:
                # Store relative path from target directory
                rel_path = file_path.relative_to(target_dir)
                all_copied_files.append({
                    'path': str(rel_path),
                    'type': dir_type
                })
            except ValueError:
                # If file is not relative to target_dir, store absolute path
                all_copied_files.append({
                    'path': str(file_path),
                    'type': dir_type
                })

    manifest = {
        'workflow_name': workflow_name,
        'applied_at': datetime.now().isoformat(),
        'synapse_version': __version__,
        'files_copied': all_copied_files,
        'hooks_added': hooks_added,
        'settings_updated': settings_updated
    }

    return manifest


def update_manifest_for_workflow_switch(
    new_workflow_name: str,
    copied_files: Dict[str, List[Path]],
    hooks_added: List[Dict],
    settings_updated: List[str],
    target_dir: Path = None
) -> bool:
    """Update the manifest when switching workflows.

    This replaces the existing manifest with new tracking information.

    Args:
        new_workflow_name: Name of the new workflow being applied
        copied_files: Dictionary mapping directory type to list of copied file paths
        hooks_added: List of hook definitions that were added to settings.json
        settings_updated: List of setting keys that were updated
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        True if successful, False otherwise
    """
    manifest = create_manifest(
        new_workflow_name,
        copied_files,
        hooks_added,
        settings_updated,
        target_dir
    )

    return save_manifest(manifest, target_dir)


def get_backup_dir(target_dir: Path = None) -> Path:
    """Get the backup directory path.

    Args:
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        Path to the backup directory (.synapse/backups/)
    """
    if target_dir is None:
        target_dir = Path.cwd()

    return target_dir / ".synapse" / "backups"


def create_backup(target_dir: Path = None) -> Optional[Path]:
    """Create a backup of the .claude directory before applying a workflow.

    Args:
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        Path to the created backup directory, or None if backup failed
    """
    if target_dir is None:
        target_dir = Path.cwd()

    claude_dir = target_dir / ".claude"

    # If .claude directory doesn't exist, no backup needed
    if not claude_dir.exists():
        return None

    backup_root = get_backup_dir(target_dir)

    # Create backup directory if it doesn't exist
    if not backup_root.exists():
        try:
            backup_root.mkdir(parents=True)
        except IOError as e:
            print(f"Warning: Could not create backup directory: {e}", file=sys.stderr)
            return None

    # Create timestamped backup directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = backup_root / f"claude_backup_{timestamp}"

    try:
        # Copy entire .claude directory
        shutil.copytree(claude_dir, backup_dir, dirs_exist_ok=False)
        return backup_dir
    except (IOError, OSError) as e:
        print(f"Warning: Could not create backup: {e}", file=sys.stderr)
        return None


def get_latest_backup(target_dir: Path = None) -> Optional[Path]:
    """Get the path to the most recent backup.

    Args:
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        Path to the latest backup directory, or None if no backups exist
    """
    if target_dir is None:
        target_dir = Path.cwd()

    backup_root = get_backup_dir(target_dir)

    if not backup_root.exists():
        return None

    # Find all backup directories
    backup_dirs = [
        d for d in backup_root.iterdir()
        if d.is_dir() and d.name.startswith("claude_backup_")
    ]

    if not backup_dirs:
        return None

    # Sort by modification time (newest first) as fallback to name sorting
    backup_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    return backup_dirs[0]


def restore_from_backup(backup_path: Path, target_dir: Path = None) -> bool:
    """Restore .claude directory from a backup.

    Args:
        backup_path: Path to the backup directory to restore from
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        True if restoration was successful, False otherwise
    """
    if target_dir is None:
        target_dir = Path.cwd()

    if not backup_path.exists():
        print(f"Error: Backup directory not found: {backup_path}", file=sys.stderr)
        return False

    claude_dir = target_dir / ".claude"

    try:
        # Remove existing .claude directory if it exists
        if claude_dir.exists():
            shutil.rmtree(claude_dir)

        # Copy backup to .claude location
        shutil.copytree(backup_path, claude_dir)
        return True
    except (IOError, OSError) as e:
        print(f"Error: Could not restore backup: {e}", file=sys.stderr)
        return False


def remove_workflow_files_from_manifest(manifest: Dict, target_dir: Path = None) -> bool:
    """Remove workflow files using the tracking manifest as a fallback method.

    Args:
        manifest: Manifest dictionary containing tracked files and hooks
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        True if removal was successful, False otherwise
    """
    if target_dir is None:
        target_dir = Path.cwd()

    try:
        files_removed = 0
        files_failed = 0

        # Remove tracked files
        files_copied = manifest.get('files_copied', [])
        if files_copied:
            print(f"    Removing {len(files_copied)} tracked files...")
            for file_info in files_copied:
                file_path = Path(file_info['path'])
                # Handle both relative and absolute paths
                if not file_path.is_absolute():
                    file_path = target_dir / file_path

                if file_path.exists():
                    try:
                        file_path.unlink()
                        files_removed += 1
                        print(f"      - {file_info['path']}")
                    except IOError as e:
                        files_failed += 1
                        print(f"      ! Failed to remove {file_info['path']}: {e}")

        # Remove hooks from settings.json
        hooks_added = manifest.get('hooks_added', [])
        if hooks_added:
            print(f"    Removing {len(hooks_added)} hooks from settings.json...")
            if remove_hooks_from_settings(hooks_added, target_dir):
                print("      ✓ Hooks removed successfully")
            else:
                print("      ! Failed to remove some hooks")
                files_failed += 1

        # Clean up empty directories
        print("    Cleaning up empty directories...")
        cleanup_empty_directories(target_dir / ".claude")

        if files_failed == 0:
            print(f"    ✓ Successfully removed {files_removed} files and {len(hooks_added)} hooks")
            return True
        else:
            print(f"    ⚠ Removed {files_removed} files, but {files_failed} operations failed")
            return False

    except Exception as e:
        print(f"    ✗ Selective removal failed: {e}")
        return False


def remove_hooks_from_settings(hooks_to_remove: List[Dict], target_dir: Path = None) -> bool:
    """Remove specific hooks from .claude/settings.json.

    Args:
        hooks_to_remove: List of hook definitions to remove
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        True if successful, False otherwise
    """
    if target_dir is None:
        target_dir = Path.cwd()

    settings_file = target_dir / ".claude" / "settings.json"

    if not settings_file.exists():
        return True  # No settings file, nothing to remove

    try:
        # Load current settings
        with open(settings_file, 'r') as f:
            settings = json.load(f)

        if 'hooks' not in settings:
            return True  # No hooks section, nothing to remove

        hooks = settings['hooks']

        # Create a set of commands to remove for quick lookup
        commands_to_remove = {hook.get('command', '') for hook in hooks_to_remove if hook.get('command')}

        # Process each hook type
        for hook_type, matchers in hooks.items():
            for matcher_group in matchers:
                # Remove hooks with matching commands
                original_hooks = matcher_group.get('hooks', [])
                filtered_hooks = [
                    hook for hook in original_hooks
                    if hook.get('command', '') not in commands_to_remove
                ]
                matcher_group['hooks'] = filtered_hooks

        # Remove empty matcher groups and hook types
        for hook_type in list(hooks.keys()):
            # Remove empty matcher groups
            hooks[hook_type] = [
                matcher_group for matcher_group in hooks[hook_type]
                if matcher_group.get('hooks')
            ]
            # Remove hook type if no matchers left
            if not hooks[hook_type]:
                del hooks[hook_type]

        # Write updated settings
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
            f.write('\n')

        return True

    except (json.JSONDecodeError, IOError) as e:
        print(f"        Error updating settings.json: {e}")
        return False


def cleanup_empty_directories(root_dir: Path) -> None:
    """Recursively remove empty directories.

    Args:
        root_dir: Root directory to start cleanup from
    """
    if not root_dir.exists() or not root_dir.is_dir():
        return

    try:
        # Get all directories in reverse order (deepest first)
        all_dirs = []
        for dir_path in root_dir.rglob("*"):
            if dir_path.is_dir():
                all_dirs.append(dir_path)

        # Sort by depth (deepest first) to remove leaf directories first
        all_dirs.sort(key=lambda x: len(x.parts), reverse=True)

        for dir_path in all_dirs:
            if dir_path.exists() and dir_path.is_dir():
                try:
                    # Only remove if empty and not the root directory
                    if dir_path != root_dir and not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        print(f"      Removed empty directory: {dir_path.relative_to(root_dir.parent)}")
                except OSError:
                    # Directory not empty or permission error, skip
                    pass

    except Exception:
        # Ignore errors during cleanup
        pass


# Validation Functions

def validate_synapse_initialized(target_dir: Path = None) -> bool:
    """Validate that synapse has been initialized in the target directory.

    Args:
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        True if synapse is initialized, False otherwise
    """
    if target_dir is None:
        target_dir = Path.cwd()

    synapse_dir = target_dir / ".synapse"
    config_file = synapse_dir / "config.json"

    return synapse_dir.exists() and config_file.exists()


def validate_claude_code_available(target_dir: Path = None) -> bool:
    """Validate that Claude Code directory structure exists.

    Args:
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        True if .claude directory exists or can be created, False otherwise
    """
    if target_dir is None:
        target_dir = Path.cwd()

    claude_dir = target_dir / ".claude"

    # .claude directory can exist or be created - both are valid
    return True  # Claude directory will be created if needed


def check_uv_available() -> bool:
    """Check if uv is available in the system PATH.

    Returns:
        True if uv is available, False otherwise
    """
    try:
        result = subprocess.run(['uv', '--version'],
                              capture_output=True,
                              text=True,
                              timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False


def validate_settings_json_after_merge(settings_json: str) -> bool:
    """Validate that settings JSON is valid after merging.

    Args:
        settings_json: JSON string to validate

    Returns:
        True if JSON is valid, False otherwise
    """
    try:
        json.loads(settings_json)
        return True
    except json.JSONDecodeError:
        return False


def validate_workflow_preconditions(workflow_name: str, target_dir: Path = None) -> None:
    """Validate all preconditions before applying a workflow.

    Args:
        workflow_name: Name of the workflow to validate
        target_dir: Target project directory. Defaults to current directory.

    Raises:
        SystemExit: If any validation fails (fail-fast behavior)
    """
    if target_dir is None:
        target_dir = Path.cwd()

    # 1. Validate synapse is initialized
    if not validate_synapse_initialized(target_dir):
        print("Error: Synapse has not been initialized in this directory.", file=sys.stderr)
        print("Please run 'synapse init' first to initialize the project.", file=sys.stderr)
        sys.exit(1)

    # 2. Validate workflow exists
    if not validate_workflow_exists(workflow_name):
        print(f"Error: Workflow '{workflow_name}' not found.", file=sys.stderr)
        print("\nAvailable workflows:", file=sys.stderr)
        workflows = discover_workflows()
        if workflows:
            for workflow in workflows:
                print(f"  - {workflow}", file=sys.stderr)
        else:
            print("  No workflows available", file=sys.stderr)
        sys.exit(1)

    # 3. Check uv availability (warning only)
    if not check_uv_available():
        print("Warning: 'uv' is not available in your PATH.", file=sys.stderr)
        print("Some workflow features may not work correctly without uv.", file=sys.stderr)
        print("Install uv from https://docs.astral.sh/uv/ for best experience.", file=sys.stderr)
        print()

    # 4. Check if workflow switching is needed
    config = load_config(target_dir)
    if config and config.get('workflows', {}).get('active_workflow'):
        current_workflow = config['workflows']['active_workflow']
        if current_workflow != workflow_name:
            print(f"Warning: Active workflow '{current_workflow}' will be replaced.", file=sys.stderr)
            print(f"Switching to workflow '{workflow_name}'.", file=sys.stderr)
            try:
                response = input("Continue with workflow switch? (y/n): ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n\nWorkflow application cancelled by user.", file=sys.stderr)
                sys.exit(1)

            if response != 'y':
                print("Workflow application cancelled.", file=sys.stderr)
                sys.exit(1)
            print()  # Add blank line for readability


def validate_removal_preconditions(target_dir: Path = None) -> None:
    """Validate preconditions before removing a workflow.

    Args:
        target_dir: Target project directory. Defaults to current directory.

    Raises:
        SystemExit: If any validation fails (fail-fast behavior)
    """
    if target_dir is None:
        target_dir = Path.cwd()

    # 1. Validate synapse is initialized
    if not validate_synapse_initialized(target_dir):
        print("Error: Synapse has not been initialized in this directory.", file=sys.stderr)
        print("Please run 'synapse init' first to initialize the project.", file=sys.stderr)
        sys.exit(1)

    # 2. Check if there's an active workflow to remove
    config = load_config(target_dir)
    manifest = load_manifest(target_dir)

    has_config_workflow = config and config.get('workflows', {}).get('active_workflow')
    has_manifest = manifest is not None

    if not has_config_workflow and not has_manifest:
        print("No active workflow found to remove.", file=sys.stderr)
        print("\nTo apply a workflow, use:", file=sys.stderr)
        print("  synapse workflow <name>", file=sys.stderr)
        sys.exit(0)  # Not an error, just nothing to do


def prompt_agent_selection() -> Dict[str, str]:
    """Prompt user to select their AI coding assistant.

    Returns:
        Dictionary with 'type' and 'description' keys for the selected agent.

    Raises:
        SystemExit: If user selects 'none' or provides invalid input.
    """
    print("\nSelect your AI coding assistant:")
    print("  1. Claude Code")
    print("  2. None")
    print()

    while True:
        try:
            choice = input("Enter your choice (1 or 2): ").strip()

            if choice == "1":
                return {
                    "type": "claude-code",
                    "description": "Claude Code AI coding assistant with Synapse integration"
                }
            elif choice == "2":
                print("\nError: Synapse requires an AI coding assistant to function.", file=sys.stderr)
                print("Please install Claude Code and try again.", file=sys.stderr)
                sys.exit(1)
            else:
                print("Invalid choice. Please enter 1 or 2.", file=sys.stderr)
        except (EOFError, KeyboardInterrupt):
            print("\n\nInitialization cancelled by user.", file=sys.stderr)
            sys.exit(1)


def init_synapse(target_dir: Path = None) -> None:
    """Initialize synapse in the target directory.

    Args:
        target_dir: Directory to initialize synapse in. Defaults to current directory.
    """
    if target_dir is None:
        target_dir = Path.cwd()

    synapse_dir = target_dir / ".synapse"

    # Check if .synapse already exists
    if synapse_dir.exists():
        print(f"Error: .synapse directory already exists at {synapse_dir}", file=sys.stderr)
        print("Remove it first or run 'synapse init' in a different directory.", file=sys.stderr)
        sys.exit(1)

    # Get resources from package
    resources_dir = get_resources_dir()

    print(f"Initializing synapse in {target_dir}")

    # Prompt for AI agent selection
    agent_info = prompt_agent_selection()

    # Create .synapse directory structure
    synapse_dir.mkdir(parents=True)

    # Create baseline config.json
    config_template_path = resources_dir / "settings" / "config-template.json"
    config_dst_path = synapse_dir / "config.json"

    if config_template_path.exists():
        try:
            # Load template
            with open(config_template_path, 'r') as f:
                config = json.load(f)

            # Populate with current values
            config['synapse_version'] = __version__
            config['initialized_at'] = datetime.now().isoformat()
            config['project']['root_directory'] = str(target_dir.absolute())

            # Detect project name from directory
            config['project']['name'] = target_dir.name

            # Set selected agent information
            config['agent']['type'] = agent_info['type']
            config['agent']['description'] = agent_info['description']

            # Write config
            with open(config_dst_path, 'w') as f:
                json.dump(config, f, indent=2)
                f.write('\n')

            print(f"  ✓ Created config.json at {config_dst_path}")
            print(f"  ✓ Configured AI agent: {agent_info['type']}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"  Warning: Could not create config.json: {e}", file=sys.stderr)
    else:
        print(f"  Warning: Baseline config template not found at {config_template_path}", file=sys.stderr)

    print(f"\nSynapse initialized successfully!")
    print(f"\nDirectory structure created:")
    print(f"  {synapse_dir}/")
    print(f"  └── config.json")
    print(f"\nUse 'synapse workflow <name>' to apply agents, hooks, and commands.")


def workflow_list() -> None:
    """List available workflows."""
    print("Available workflows:\n")

    workflows = discover_workflows()

    if not workflows:
        print("No workflows found.")
        return

    # Display each workflow with its metadata
    for workflow_name in workflows:
        info = get_workflow_info(workflow_name)

        # Display workflow name
        print(f"  {workflow_name}")

        # Display description if available
        if info and info.get("description"):
            print(f"    {info['description']}")

        # Display version if available
        if info and info.get("version"):
            print(f"    Version: {info['version']}")

        print()  # Blank line between workflows

    print(f"Total: {len(workflows)} workflow(s)")
    print("\nUse 'synapse workflow <name>' to apply a workflow.")


def workflow_status() -> None:
    """Show active workflow and associated artifacts."""
    target_dir = Path.cwd()

    # Load both config and manifest for comprehensive status
    config = load_config(target_dir)
    manifest = load_manifest(target_dir)

    # Check if we have any workflow information
    has_config_workflow = config and config.get('workflows', {}).get('active_workflow')
    has_manifest = manifest is not None

    if not has_config_workflow and not has_manifest:
        print("No active workflow found.")
        print("\nTo apply a workflow, use:")
        print("  synapse workflow <name>")
        print("\nTo list available workflows, use:")
        print("  synapse workflow list")
        return

    print("Active Workflow Status")
    print("=" * 60)

    # Show config-level workflow tracking
    if config and 'workflows' in config:
        active_workflow = config['workflows'].get('active_workflow')
        if active_workflow:
            print(f"\nActive Workflow: {active_workflow}")

        # Show workflow history
        applied_workflows = config['workflows'].get('applied_workflows', [])
        if applied_workflows:
            print(f"\nWorkflow History ({len(applied_workflows)} applied):")
            print("-" * 60)
            for entry in applied_workflows:
                workflow_name = entry.get('name', 'unknown')
                applied_at = entry.get('applied_at', 'unknown')
                print(f"  {workflow_name} (applied: {applied_at})")

    # Show detailed manifest information
    if manifest:
        print("\n" + "=" * 60)
        print("Detailed Workflow Artifacts")
        print("=" * 60)
        print(f"\nWorkflow: {manifest['workflow_name']}")
        print(f"Applied: {manifest['applied_at']}")
        print(f"Synapse Version: {manifest['synapse_version']}")

        # Show copied files
        if manifest['files_copied']:
            print(f"\nFiles Copied ({len(manifest['files_copied'])} total):")
            print("-" * 60)

            # Group by type
            files_by_type = {}
            for file_info in manifest['files_copied']:
                file_type = file_info['type']
                if file_type not in files_by_type:
                    files_by_type[file_type] = []
                files_by_type[file_type].append(file_info['path'])

            for file_type in sorted(files_by_type.keys()):
                print(f"\n{file_type.capitalize()}:")
                for file_path in sorted(files_by_type[file_type]):
                    print(f"  {file_path}")
        else:
            print("\nNo files copied")

        # Show hooks added
        if manifest['hooks_added']:
            print(f"\nHooks Added ({len(manifest['hooks_added'])} total):")
            print("-" * 60)
            for hook in manifest['hooks_added']:
                print(f"  {hook.get('name', 'unnamed')} ({hook.get('trigger', 'no trigger')})")
        else:
            print("\nNo hooks added")

        # Show settings updated
        if manifest['settings_updated']:
            print(f"\nSettings Updated ({len(manifest['settings_updated'])} keys):")
            print("-" * 60)
            for setting in sorted(manifest['settings_updated']):
                print(f"  {setting}")
        else:
            print("\nNo settings updated")
    else:
        print("\n" + "=" * 60)
        print("\nWarning: Workflow manifest not found.")
        print("Detailed artifact tracking is not available.")

    # Warn if config and manifest are out of sync
    if has_config_workflow and has_manifest:
        config_workflow = config['workflows']['active_workflow']
        manifest_workflow = manifest['workflow_name']
        if config_workflow != manifest_workflow:
            print("\n" + "=" * 60)
            print("WARNING: Workflow tracking inconsistency detected!")
            print(f"  Config shows: {config_workflow}")
            print(f"  Manifest shows: {manifest_workflow}")
            print("  Consider re-applying the workflow to fix this.")

    print("\n" + "=" * 60)
    print("\nTo remove this workflow, use:")
    print("  synapse workflow remove")


def workflow_remove() -> None:
    """Remove current workflow.

    Attempts backup restoration first, falls back to selective removal via manifest.
    """
    target_dir = Path.cwd()

    # Validate preconditions (this includes checking for active workflow)
    validate_removal_preconditions(target_dir)

    # Load current workflow state
    config = load_config(target_dir)
    manifest = load_manifest(target_dir)

    # Determine what workflow artifacts exist
    has_config_workflow = config and config.get('workflows', {}).get('active_workflow')
    has_manifest = manifest is not None

    # Show what will be removed
    print("Workflow Removal")
    print("=" * 60)

    if has_config_workflow:
        workflow_name = config['workflows']['active_workflow']
        print(f"\nActive workflow: {workflow_name}")

    if has_manifest:
        print(f"\nWorkflow artifacts tracked:")
        print(f"  Files: {len(manifest.get('files_copied', []))} copied")
        print(f"  Hooks: {len(manifest.get('hooks_added', []))} added")
        print(f"  Settings: {len(manifest.get('settings_updated', []))} updated")

    # Check for available backup
    latest_backup = get_latest_backup(target_dir)
    if latest_backup:
        print(f"\nLatest backup found: {latest_backup}")
        print("  Will restore from backup (recommended)")
    else:
        print("\nNo backup found.")
        if has_manifest:
            print("  Will attempt selective removal using manifest (fallback)")
        else:
            print("  Manual cleanup will be required")

    # Prompt for confirmation
    print("\n" + "=" * 60)
    try:
        response = input("\nProceed with workflow removal? (y/n): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n\nOperation cancelled.")
        return

    if response != 'y':
        print("Operation cancelled.")
        return

    # Perform removal
    print("\nRemoving workflow...")

    removal_success = False

    # Try backup restoration first
    if latest_backup:
        print(f"\nRestoring from backup: {latest_backup}")
        if restore_from_backup(latest_backup, target_dir):
            print("  ✓ Successfully restored from backup")
            removal_success = True
        else:
            print("  ✗ Backup restoration failed, falling back to selective removal")

    # Fall back to selective removal if backup restoration failed or no backup exists
    if not removal_success and has_manifest:
        print("\nAttempting selective removal using manifest...")
        if remove_workflow_files_from_manifest(manifest, target_dir):
            print("  ✓ Successfully removed workflow files using manifest")
            removal_success = True
        else:
            print("  ✗ Selective removal failed")

    # Clear workflow tracking from config regardless of removal method
    print("\nClearing workflow tracking...")
    if clear_config_workflow_tracking(target_dir):
        print("  ✓ Workflow tracking cleared from config.json")
    else:
        print("  ⚠ Warning: Could not clear workflow tracking", file=sys.stderr)

    # Remove manifest file if removal was successful
    if removal_success:
        manifest_path = get_manifest_path(target_dir)
        if manifest_path.exists():
            try:
                manifest_path.unlink()
                print("  ✓ Workflow manifest removed")
            except IOError:
                print("  ⚠ Warning: Could not remove workflow manifest", file=sys.stderr)

    # Final status
    print("\n" + "=" * 60)
    if removal_success:
        print("Workflow removed successfully!")
    else:
        print("Workflow removal incomplete. Manual cleanup may be required.")
        if has_manifest:
            print(f"\nReview .synapse/workflow-manifest.json for files that may need manual removal.")
        print("\nFiles that may need manual cleanup:")
        print("  - Files in .claude/agents/")
        print("  - Files in .claude/hooks/")
        print("  - Files in .claude/commands/synapse/")
        print("  - Hook configurations in .claude/settings.json")


def copy_directory_with_conflicts(
    src_dir: Path,
    dst_dir: Path,
    force: bool = False
) -> Tuple[List[Path], List[Path], List[Path]]:
    """Copy directory contents from source to destination with conflict detection.

    Args:
        src_dir: Source directory to copy from
        dst_dir: Destination directory to copy to
        force: If True, overwrite existing files; if False, skip them

    Returns:
        Tuple of (copied_files, skipped_files, created_dirs):
        - copied_files: List of files that were successfully copied
        - skipped_files: List of files that were skipped due to conflicts
        - created_dirs: List of directories that were created

    Note:
        This function only copies files, not the directory itself.
        The destination directory will be created if it doesn't exist.
    """
    copied_files: List[Path] = []
    skipped_files: List[Path] = []
    created_dirs: List[Path] = []

    # Create destination directory if it doesn't exist
    if not dst_dir.exists():
        dst_dir.mkdir(parents=True)
        created_dirs.append(dst_dir)

    # Walk through source directory
    for src_item in src_dir.rglob("*"):
        # Skip if it's the source directory itself
        if src_item == src_dir:
            continue

        # Calculate relative path from source
        rel_path = src_item.relative_to(src_dir)
        dst_item = dst_dir / rel_path

        if src_item.is_dir():
            # Create directory if it doesn't exist
            if not dst_item.exists():
                dst_item.mkdir(parents=True)
                created_dirs.append(dst_item)
        else:
            # Handle file copying
            if dst_item.exists():
                if force:
                    # Overwrite existing file
                    shutil.copy2(src_item, dst_item)
                    copied_files.append(dst_item)
                else:
                    # Skip existing file
                    skipped_files.append(dst_item)
            else:
                # Copy new file
                shutil.copy2(src_item, dst_item)
                copied_files.append(dst_item)

    return copied_files, skipped_files, created_dirs


def merge_settings_json(
    workflow_name: str,
    target_dir: Path
) -> Dict[str, any]:
    """Merge workflow settings.json with existing .claude/settings.json.

    Args:
        workflow_name: Name of the workflow to apply
        target_dir: Target project directory (contains or will contain .claude/)

    Returns:
        Dictionary with merge results:
        {
            'merged': bool,           # Whether merge was performed
            'created': bool,          # Whether settings.json was created new
            'hooks_added': list,      # List of hook definitions that were added
            'settings_updated': list, # List of top-level keys updated
            'error': str or None      # Error message if merge failed
        }

    Note:
        - Hook arrays are appended (workflow hooks added to existing)
        - Other settings: workflow settings take precedence
        - Returns early with merged=False if workflow has no settings.json
        - Validates resulting JSON and returns error if invalid
    """
    workflows_dir = get_workflows_dir()
    workflow_settings_file = workflows_dir / workflow_name / "settings.json"

    # Result dictionary
    result = {
        'merged': False,
        'created': False,
        'hooks_added': [],
        'settings_updated': [],
        'error': None
    }

    # If workflow has no settings.json, nothing to merge
    if not workflow_settings_file.exists():
        return result

    # Load workflow settings
    try:
        with open(workflow_settings_file, 'r') as f:
            workflow_settings = json.load(f)
    except json.JSONDecodeError as e:
        result['error'] = f"Invalid JSON in workflow settings.json: {e}"
        return result
    except IOError as e:
        result['error'] = f"Could not read workflow settings.json: {e}"
        return result

    # Target settings file
    claude_dir = target_dir / ".claude"
    target_settings_file = claude_dir / "settings.json"

    # Create .claude directory if it doesn't exist
    if not claude_dir.exists():
        claude_dir.mkdir(parents=True)

    # Load existing settings or start with empty dict
    existing_settings = {}
    if target_settings_file.exists():
        try:
            with open(target_settings_file, 'r') as f:
                existing_settings = json.load(f)
        except json.JSONDecodeError as e:
            result['error'] = f"Invalid JSON in existing settings.json: {e}"
            return result
        except IOError as e:
            result['error'] = f"Could not read existing settings.json: {e}"
            return result
    else:
        result['created'] = True

    # Merge settings
    merged_settings = existing_settings.copy()

    # Special handling for hooks: merge Claude Code hook structure
    if 'hooks' in workflow_settings:
        workflow_hooks = workflow_settings['hooks']

        # Initialize hooks structure if it doesn't exist
        if 'hooks' not in merged_settings:
            merged_settings['hooks'] = {}
        existing_hooks = merged_settings['hooks']

        # Ensure existing_hooks is a dict (handle migration from old format)
        if isinstance(existing_hooks, list):
            # Convert old format to new format - start with empty dict
            existing_hooks = {}
            merged_settings['hooks'] = existing_hooks

        hooks_added_list = []

        # Merge each hook type (UserPromptSubmit, PostToolUse, etc.)
        for hook_type, workflow_matchers in workflow_hooks.items():
            if hook_type not in existing_hooks:
                existing_hooks[hook_type] = []

            existing_matchers = existing_hooks[hook_type]

            # Track existing hook commands to avoid duplicates
            existing_commands = set()
            for matcher_group in existing_matchers:
                for hook in matcher_group.get('hooks', []):
                    if 'command' in hook:
                        existing_commands.add(hook['command'])

            # Merge workflow matchers for this hook type
            for workflow_matcher in workflow_matchers:
                # Check if we should merge with existing matcher or add new one
                matcher_pattern = workflow_matcher.get('matcher', '')

                # Find existing matcher group with same pattern
                matching_group = None
                for existing_matcher in existing_matchers:
                    if existing_matcher.get('matcher', '') == matcher_pattern:
                        matching_group = existing_matcher
                        break

                # If no matching group found, create new one
                if matching_group is None:
                    new_matcher_group = {
                        'matcher': matcher_pattern,
                        'hooks': []
                    }
                    existing_matchers.append(new_matcher_group)
                    matching_group = new_matcher_group

                # Add workflow hooks to the matching group (avoid duplicates)
                for workflow_hook in workflow_matcher.get('hooks', []):
                    command = workflow_hook.get('command', '')
                    if command and command not in existing_commands:
                        matching_group['hooks'].append(workflow_hook)
                        existing_commands.add(command)
                        hooks_added_list.append({
                            'hook_type': hook_type,
                            'matcher': matcher_pattern,
                            'command': command,
                            'type': workflow_hook.get('type', 'command')
                        })

        result['hooks_added'] = hooks_added_list

    # Merge other settings (workflow takes precedence)
    for key, value in workflow_settings.items():
        if key != 'hooks':  # Already handled
            if key not in merged_settings or merged_settings[key] != value:
                merged_settings[key] = value
                result['settings_updated'].append(key)

    # Validate the merged JSON by attempting to serialize it
    try:
        merged_json = json.dumps(merged_settings, indent=2)
    except (TypeError, ValueError) as e:
        result['error'] = f"Merged settings cannot be serialized to JSON: {e}"
        return result

    # Additional validation of the resulting JSON structure
    if not validate_settings_json_after_merge(merged_json):
        result['error'] = "Merged settings produced invalid JSON structure"
        return result

    # Write merged settings
    try:
        with open(target_settings_file, 'w') as f:
            f.write(merged_json)
            f.write('\n')  # Add trailing newline
    except IOError as e:
        result['error'] = f"Could not write merged settings.json: {e}"
        return result

    result['merged'] = True
    return result


def apply_workflow_directories(
    workflow_name: str,
    target_dir: Path,
    force: bool = False
) -> Dict[str, Tuple[List[Path], List[Path], List[Path]]]:
    """Apply workflow directories to target .claude directory.

    Copies agents/ and hooks/ from the workflow, and commands/synapse/ from top-level resources to .claude/

    Args:
        workflow_name: Name of the workflow to apply
        target_dir: Target project directory (contains or will contain .claude/)
        force: If True, overwrite existing files; if False, skip conflicts

    Returns:
        Dictionary mapping directory type to (copied_files, skipped_files, created_dirs)
        Keys: 'agents', 'hooks', 'commands'

    Raises:
        SystemExit: If workflow directory doesn't exist
    """
    workflows_dir = get_workflows_dir()
    workflow_dir = workflows_dir / workflow_name

    if not workflow_dir.exists():
        print(f"Error: Workflow directory not found: {workflow_dir}", file=sys.stderr)
        sys.exit(1)

    # Target .claude directory
    claude_dir = target_dir / ".claude"

    # Create .claude if it doesn't exist
    if not claude_dir.exists():
        claude_dir.mkdir(parents=True)
        print(f"Created .claude directory at {claude_dir}")

    results = {}

    # Define directory mappings: (source_root, source_subdir, target_subdir, display_name)
    directory_mappings = [
        (workflow_dir, "agents", "agents", "agents"),
        (workflow_dir, "hooks", "hooks", "hooks"),
        (workflow_dir, "commands/synapse", "commands/synapse", "commands"),
    ]

    for src_root, src_subdir, dst_subdir, display_name in directory_mappings:
        src_path = src_root / src_subdir
        dst_path = claude_dir / dst_subdir

        if src_path.exists():
            copied, skipped, created = copy_directory_with_conflicts(
                src_path, dst_path, force
            )
            results[display_name] = (copied, skipped, created)

            # Make shell scripts executable in hooks
            if display_name == "hooks":
                for hook_file in dst_path.glob("*.sh"):
                    hook_file.chmod(0o755)
        else:
            # Directory doesn't exist, skip it
            results[display_name] = ([], [], [])

    return results


def workflow_apply(name: str, force: bool = False) -> None:
    """Apply a workflow to the current project.

    Args:
        name: Name of the workflow to apply
        force: Force overwrite of existing files
    """
    target_dir = Path.cwd()

    # Validate all preconditions (fail-fast)
    validate_workflow_preconditions(name, target_dir)

    # Get workflow info for display
    info = get_workflow_info(name)
    print(f"Applying workflow: {name}")
    if info and info.get("description"):
        print(f"  {info['description']}")

    if force:
        print("\nForce mode enabled - will overwrite existing files")

    # Create backup of existing .claude directory before applying workflow
    print("\nCreating backup of existing .claude directory...")
    backup_path = create_backup(target_dir)
    if backup_path:
        print(f"  Backup created at: {backup_path}")
    else:
        print("  No existing .claude directory found - no backup needed")

    print("\nCopying workflow directories...")

    # Apply workflow directories to current directory
    results = apply_workflow_directories(name, target_dir, force)

    # Display results for each directory type
    print("\nDirectory Results:")
    print("-" * 60)

    total_copied = 0
    total_skipped = 0
    has_conflicts = False

    for dir_type in ["agents", "hooks", "commands"]:
        copied, skipped, created = results.get(dir_type, ([], [], []))

        if not copied and not skipped:
            continue

        print(f"\n{dir_type.capitalize()}:")

        if copied:
            total_copied += len(copied)
            print(f"  Copied {len(copied)} file(s):")
            for file in copied:
                print(f"    + {file}")

        if skipped:
            total_skipped += len(skipped)
            has_conflicts = True
            print(f"  Skipped {len(skipped)} file(s) (already exist):")
            for file in skipped:
                print(f"    ! {file}")

    # Merge settings.json
    print("\n" + "=" * 60)
    print("Merging settings.json...")
    print("-" * 60)

    merge_result = merge_settings_json(name, target_dir)

    if merge_result['error']:
        print(f"\nError: Failed to merge settings.json", file=sys.stderr)
        print(f"  {merge_result['error']}", file=sys.stderr)
        sys.exit(1)

    if merge_result['merged']:
        settings_file = target_dir / ".claude" / "settings.json"
        if merge_result['created']:
            print(f"\nCreated new settings.json at {settings_file}")
        else:
            print(f"\nMerged settings into {settings_file}")

        if len(merge_result['hooks_added']) > 0:
            print(f"  Added {len(merge_result['hooks_added'])} hook(s)")

        if merge_result['settings_updated']:
            print(f"  Updated settings: {', '.join(merge_result['settings_updated'])}")
    else:
        print("\nNo settings.json in workflow - skipping merge")

    # Save workflow tracking manifest
    print("\n" + "=" * 60)
    print("Saving workflow manifest...")
    print("-" * 60)

    # Collect all copied files for manifest
    copied_files_for_manifest = {}
    for dir_type in ["agents", "hooks", "commands"]:
        copied, skipped, created = results.get(dir_type, ([], [], []))
        if copied:
            copied_files_for_manifest[dir_type] = copied

    # Create and save manifest
    manifest = create_manifest(
        workflow_name=name,
        copied_files=copied_files_for_manifest,
        hooks_added=merge_result['hooks_added'],
        settings_updated=merge_result['settings_updated'],
        target_dir=target_dir
    )

    if save_manifest(manifest, target_dir):
        manifest_path = get_manifest_path(target_dir)
        print(f"\nWorkflow manifest saved to {manifest_path}")
    else:
        print(f"\nWarning: Could not save workflow manifest", file=sys.stderr)

    # Update config.json workflow tracking
    print("\n" + "=" * 60)
    print("Updating workflow tracking in config.json...")
    print("-" * 60)

    if update_config_workflow_tracking(name, target_dir):
        config_path = get_config_path(target_dir)
        print(f"\nWorkflow tracking updated in {config_path}")
        print(f"  Active workflow: {name}")
    else:
        print(f"\nWarning: Could not update config.json workflow tracking", file=sys.stderr)
        print(f"  Workflow is still tracked in manifest file", file=sys.stderr)

    # Summary
    print("\n" + "=" * 60)
    print(f"Summary: {total_copied} file(s) copied, {total_skipped} file(s) skipped")

    if has_conflicts:
        print("\nWarning: Some files were skipped because they already exist.")
        print("Use 'synapse workflow <name> --force' to overwrite existing files.")

    print("\nWorkflow applied successfully!")


def validate_quality() -> None:
    """Validate that quality commands will properly fail when they should."""
    # Run validation script
    resources_dir = get_resources_dir()
    validation_script = resources_dir / "workflows" / "feature-implementation" / "hooks" / "validate_quality_commands.py"

    if not validation_script.exists():
        print(f"Error: Validation script not found at {validation_script}", file=sys.stderr)
        sys.exit(1)

    try:
        result = subprocess.run(
            [sys.executable, str(validation_script)],
            cwd=Path.cwd(),
            timeout=120
        )
        sys.exit(result.returncode)
    except subprocess.TimeoutExpired:
        print("Error: Validation timed out after 120 seconds", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error running validation: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Synapse - AI-first workflow system with quality gates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  synapse init                      Initialize synapse in current directory
  synapse init /path/to/project     Initialize synapse in specific directory
  synapse workflow list             List available workflows
  synapse workflow status           Show active workflow
  synapse workflow remove           Remove current workflow
  synapse workflow development      Apply development workflow
  synapse validate-quality          Validate quality commands configuration
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize synapse in a project")
    init_parser.add_argument(
        "directory",
        nargs="?",
        type=Path,
        default=None,
        help="Directory to initialize synapse in (default: current directory)"
    )

    # Workflow command
    workflow_parser = subparsers.add_parser(
        "workflow",
        help="Manage workflow configurations"
    )

    # First positional argument is the workflow name or subcommand
    workflow_parser.add_argument(
        "workflow_name_or_command",
        help="Workflow name to apply, or subcommand (list, status, remove)"
    )

    # Optional --force flag for applying workflows
    workflow_parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite of existing files when applying a workflow"
    )

    # Validate-quality command
    validate_quality_parser = subparsers.add_parser(
        "validate-quality",
        help="Validate that quality commands will properly fail when they should"
    )

    # Parse arguments
    args = parser.parse_args()

    if args.command == "init":
        init_synapse(args.directory)
    elif args.command == "workflow":
        # Handle workflow subcommands and workflow application
        workflow_arg = args.workflow_name_or_command

        if workflow_arg == "list":
            workflow_list()
        elif workflow_arg == "status":
            workflow_status()
        elif workflow_arg == "remove":
            workflow_remove()
        else:
            # Apply workflow by name
            workflow_apply(workflow_arg, args.force)
    elif args.command == "validate-quality":
        validate_quality()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()