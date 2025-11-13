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


def get_loaded_workflows_dir(target_dir: Path = None) -> Path:
    """Get the loaded workflows directory in .synapse.

    Args:
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        Path to the .synapse/workflows directory

    Note:
        This directory stores workflows that have been loaded into the project.
        Does not validate if the directory exists - caller should check.
    """
    if target_dir is None:
        target_dir = Path.cwd()

    return target_dir / ".synapse" / "workflows"


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


# User Settings Functions

def get_user_settings_path(target_dir: Path = None) -> Path:
    """Get the path to the user settings file.

    Args:
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        Path to the .synapse/user-settings.json file
    """
    if target_dir is None:
        target_dir = Path.cwd()

    return target_dir / ".synapse" / "user-settings.json"


def load_user_settings(target_dir: Path = None) -> Dict:
    """Load user-specific Claude Code settings.

    Args:
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        Dictionary with user settings, or empty dict if not found
    """
    user_settings_path = get_user_settings_path(target_dir)

    if not user_settings_path.exists():
        return {}

    try:
        with open(user_settings_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not read user settings: {e}", file=sys.stderr)
        return {}


def save_user_settings(user_settings: Dict, target_dir: Path = None) -> bool:
    """Save user-specific Claude Code settings.

    Args:
        user_settings: User settings dictionary
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        True if successful, False otherwise
    """
    user_settings_path = get_user_settings_path(target_dir)

    # Ensure .synapse directory exists
    synapse_dir = user_settings_path.parent
    if not synapse_dir.exists():
        try:
            synapse_dir.mkdir(parents=True)
        except IOError as e:
            print(f"Error: Could not create .synapse directory: {e}", file=sys.stderr)
            return False

    try:
        with open(user_settings_path, 'w') as f:
            json.dump(user_settings, f, indent=2)
            f.write('\n')
        return True
    except (TypeError, ValueError, IOError) as e:
        print(f"Error: Could not save user settings: {e}", file=sys.stderr)
        return False


def merge_settings(workflow_settings: Dict, user_settings: Dict, claude_dir: Path) -> Dict:
    """Merge workflow and user settings, with user settings taking precedence.

    This function merges workflow-provided settings with user-customized settings.
    For hooks, user hooks are appended after workflow hooks.

    Args:
        workflow_settings: Settings from the workflow
        user_settings: User-specific settings
        claude_dir: Path to .claude directory (for converting relative paths)

    Returns:
        Merged settings dictionary
    """
    import copy
    merged = copy.deepcopy(workflow_settings)

    # Merge hooks - user hooks are added after workflow hooks
    if 'hooks' in user_settings:
        if 'hooks' not in merged:
            merged['hooks'] = {}

        for hook_type, user_matchers in user_settings['hooks'].items():
            if hook_type not in merged['hooks']:
                merged['hooks'][hook_type] = []

            # Append user hooks to workflow hooks
            merged['hooks'][hook_type].extend(user_matchers)

    # Merge other top-level settings (user settings override workflow settings)
    for key, value in user_settings.items():
        if key != 'hooks':  # hooks are already handled
            merged[key] = value

    # Convert relative .claude/ paths to absolute paths in all hooks
    if 'hooks' in merged:
        for hook_type, matchers in merged['hooks'].items():
            for matcher_idx, matcher in enumerate(matchers):
                if 'hooks' in matcher:
                    for hook_idx, hook in enumerate(matcher['hooks']):
                        if 'command' in hook and '.claude/' in hook['command']:
                            merged['hooks'][hook_type][matcher_idx]['hooks'][hook_idx]['command'] = \
                                hook['command'].replace('.claude/', str(claude_dir) + '/')

    return merged


def extract_user_settings_from_active(target_dir: Path = None) -> bool:
    """Extract user settings from current .claude/settings.json to .synapse/user-settings.json.

    This is useful for preserving custom user settings before switching workflows.

    Args:
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        True if extraction successful, False otherwise
    """
    if target_dir is None:
        target_dir = Path.cwd()

    claude_settings_path = target_dir / ".claude" / "settings.json"

    if not claude_settings_path.exists():
        print("No .claude/settings.json found to extract from.")
        return False

    config = load_config(target_dir)
    if not config:
        print("Error: Synapse not initialized.", file=sys.stderr)
        return False

    active_workflow = config.get('workflows', {}).get('active_workflow')
    if not active_workflow:
        print("No active workflow - cannot determine which settings are user-added.")
        return False

    # Load current claude settings
    try:
        with open(claude_settings_path, 'r') as f:
            claude_settings = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error: Could not read .claude/settings.json: {e}", file=sys.stderr)
        return False

    # Load workflow settings to compare
    workflow_dir = get_loaded_workflows_dir(target_dir) / active_workflow
    workflow_settings_path = workflow_dir / "settings.json"

    if not workflow_settings_path.exists():
        print(f"Warning: Could not find workflow settings for '{active_workflow}'", file=sys.stderr)
        return False

    try:
        with open(workflow_settings_path, 'r') as f:
            workflow_settings = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error: Could not read workflow settings: {e}", file=sys.stderr)
        return False

    # Extract user-added settings by comparing with workflow settings
    user_settings = {}

    # For hooks, find user-added hooks (those not in workflow)
    if 'hooks' in claude_settings:
        import copy
        claude_dir = target_dir / ".claude"
        user_settings['hooks'] = {}

        for hook_type, matchers in claude_settings['hooks'].items():
            workflow_matchers = workflow_settings.get('hooks', {}).get(hook_type, [])

            # Convert workflow hooks to comparable format (with absolute paths)
            comparable_workflow_matchers = []
            for m in workflow_matchers:
                comparable = copy.deepcopy(m)
                if 'hooks' in comparable:
                    for h in comparable['hooks']:
                        if 'command' in h and '.claude/' in h['command']:
                            h['command'] = h['command'].replace('.claude/', str(claude_dir) + '/')
                comparable_workflow_matchers.append(comparable)

            # Find matchers that are not in workflow
            user_matchers = []
            for matcher in matchers:
                if matcher not in comparable_workflow_matchers:
                    # Convert absolute paths back to relative for portability
                    user_matcher = copy.deepcopy(matcher)
                    if 'hooks' in user_matcher:
                        for h in user_matcher['hooks']:
                            if 'command' in h:
                                h['command'] = h['command'].replace(str(claude_dir) + '/', '.claude/')
                    user_matchers.append(user_matcher)

            if user_matchers:
                user_settings['hooks'][hook_type] = user_matchers

    # Extract other top-level settings that differ from workflow
    for key, value in claude_settings.items():
        if key != 'hooks' and key not in workflow_settings:
            user_settings[key] = value

    # Save user settings
    if user_settings:
        if save_user_settings(user_settings, target_dir):
            print(f"✓ Extracted user settings to .synapse/user-settings.json")
            if 'hooks' in user_settings:
                hook_count = sum(len(m) for m in user_settings['hooks'].values())
                print(f"  Found {hook_count} user-defined hook(s)")
            return True
        else:
            return False
    else:
        print("No user-specific settings found to extract.")
        return True


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
    print(f"\nNext steps:")
    print(f"  1. List available workflows: synapse workflow list")
    print(f"  2. Load a workflow: synapse workflow load <name>")
    print(f"  3. Activate it: synapse workflow switch <name>")
    print(f"  (or use 'synapse workflow apply <name>' to do both at once)")


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
    print("\nUse 'synapse workflow load <name>' to load a workflow.")
    print("Use 'synapse workflow <name>' to apply a workflow directly (load + switch).")


def workflow_loaded_list() -> None:
    """List loaded workflows in the current project."""
    target_dir = Path.cwd()

    config = load_config(target_dir)
    if not config:
        print("Error: Synapse not initialized in this directory", file=sys.stderr)
        print("Run 'synapse init' first.", file=sys.stderr)
        sys.exit(1)

    loaded_workflows = config.get('workflows', {}).get('loaded_workflows', [])
    active_workflow = config.get('workflows', {}).get('active_workflow')

    if not loaded_workflows:
        print("No workflows loaded in this project.")
        print("\nTo load a workflow, use:")
        print("  synapse workflow load <name>")
        print("\nTo see available workflows, use:")
        print("  synapse workflow list")
        return

    print("Loaded workflows:\n")

    for workflow in loaded_workflows:
        name = workflow.get('name', 'unknown')
        version = workflow.get('version', 'unknown')
        loaded_at = workflow.get('loaded_at', 'unknown')
        customized = workflow.get('customized', False)

        # Mark active workflow
        active_marker = " [ACTIVE]" if name == active_workflow else ""

        print(f"  {name}{active_marker}")
        print(f"    Version: {version}")
        print(f"    Loaded: {loaded_at}")
        if customized:
            print(f"    Status: Customized")
        print()

    print(f"Total: {len(loaded_workflows)} workflow(s) loaded")

    if active_workflow:
        print(f"\nActive workflow: {active_workflow}")
        print(f"Use 'synapse workflow switch <name>' to switch to a different workflow.")
    else:
        print(f"\nNo active workflow.")
        print(f"Use 'synapse workflow switch <name>' to activate a loaded workflow.")


def workflow_active() -> None:
    """Show the currently active workflow."""
    target_dir = Path.cwd()

    config = load_config(target_dir)
    if not config:
        print("Error: Synapse not initialized in this directory", file=sys.stderr)
        print("Run 'synapse init' first.", file=sys.stderr)
        sys.exit(1)

    active_workflow = config.get('workflows', {}).get('active_workflow')
    last_switch = config.get('workflows', {}).get('last_switch')

    if not active_workflow:
        print("No active workflow.")
        print("\nTo see loaded workflows, use:")
        print("  synapse workflow loaded")
        print("\nTo switch to a workflow, use:")
        print("  synapse workflow switch <name>")
        return

    print(f"Active workflow: {active_workflow}")

    if last_switch:
        print(f"Last switched: {last_switch}")

    # Show workflow info if available
    loaded_workflows = config.get('workflows', {}).get('loaded_workflows', [])
    workflow_info = next((w for w in loaded_workflows if w.get('name') == active_workflow), None)

    if workflow_info:
        version = workflow_info.get('version', 'unknown')
        loaded_at = workflow_info.get('loaded_at', 'unknown')
        customized = workflow_info.get('customized', False)

        print(f"Version: {version}")
        print(f"Loaded: {loaded_at}")
        if customized:
            print(f"Status: Customized")

    print("\nTo switch to a different workflow, use:")
    print("  synapse workflow switch <name>")


def load_workflow(name: str, target_dir: Path = None, force: bool = False) -> bool:
    """Load a workflow into the project's .synapse/workflows/ directory.

    Args:
        name: Name of the workflow to load
        target_dir: Target project directory. Defaults to current directory.
        force: Force reload if workflow is already loaded

    Returns:
        True if workflow was loaded successfully, False otherwise
    """
    if target_dir is None:
        target_dir = Path.cwd()

    # Validate synapse is initialized
    config = load_config(target_dir)
    if not config:
        print(f"Error: Synapse not initialized in {target_dir}", file=sys.stderr)
        print("Run 'synapse init' first.", file=sys.stderr)
        return False

    # Validate workflow exists in resources
    if not validate_workflow_exists(name):
        print(f"Error: Workflow '{name}' not found", file=sys.stderr)
        print("Run 'synapse workflow list' to see available workflows.", file=sys.stderr)
        return False

    # Check if already loaded
    loaded_workflows = config.get('workflows', {}).get('loaded_workflows', [])
    already_loaded = any(w.get('name') == name for w in loaded_workflows)

    if already_loaded and not force:
        print(f"Workflow '{name}' is already loaded.", file=sys.stderr)
        print("Use --force to reload.", file=sys.stderr)
        return False

    # Get source workflow directory
    workflows_dir = get_workflows_dir()
    src_workflow_dir = workflows_dir / name

    # Get destination directory
    loaded_workflows_dir = get_loaded_workflows_dir(target_dir)
    dst_workflow_dir = loaded_workflows_dir / name

    # Create .synapse/workflows directory if it doesn't exist
    if not loaded_workflows_dir.exists():
        loaded_workflows_dir.mkdir(parents=True)
        print(f"Created {loaded_workflows_dir}")

    # If reloading, remove existing
    if dst_workflow_dir.exists():
        print(f"Removing existing workflow at {dst_workflow_dir}...")
        shutil.rmtree(dst_workflow_dir)

    # Copy workflow to .synapse/workflows/
    print(f"Loading workflow '{name}'...")
    try:
        shutil.copytree(src_workflow_dir, dst_workflow_dir)
        print(f"  ✓ Copied workflow to {dst_workflow_dir}")
    except Exception as e:
        print(f"Error: Failed to copy workflow: {e}", file=sys.stderr)
        return False

    # Update config.json to track loaded workflow
    workflow_info = get_workflow_info(name)
    workflow_entry = {
        "name": name,
        "loaded_at": datetime.now().isoformat(),
        "version": workflow_info.get("version") if workflow_info else "unknown",
        "customized": False
    }

    # Update loaded_workflows list
    if already_loaded:
        # Replace existing entry
        loaded_workflows = [w for w in loaded_workflows if w.get('name') != name]

    loaded_workflows.append(workflow_entry)

    # Ensure workflows section exists
    if 'workflows' not in config:
        config['workflows'] = {}

    config['workflows']['loaded_workflows'] = loaded_workflows

    # Save updated config
    if save_config(config, target_dir):
        print(f"  ✓ Updated config.json")
    else:
        print(f"  ⚠ Warning: Could not update config.json", file=sys.stderr)

    print(f"\nWorkflow '{name}' loaded successfully!")
    print(f"Use 'synapse workflow switch {name}' to activate it.")

    return True


def switch_workflow(name: str, target_dir: Path = None) -> bool:
    """Switch to a loaded workflow.

    Args:
        name: Name of the workflow to switch to
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        True if workflow was switched successfully, False otherwise
    """
    if target_dir is None:
        target_dir = Path.cwd()

    # Validate synapse is initialized
    config = load_config(target_dir)
    if not config:
        print(f"Error: Synapse not initialized in {target_dir}", file=sys.stderr)
        print("Run 'synapse init' first.", file=sys.stderr)
        return False

    # Check if workflow is loaded
    loaded_workflows = config.get('workflows', {}).get('loaded_workflows', [])
    workflow_loaded = any(w.get('name') == name for w in loaded_workflows)

    if not workflow_loaded:
        print(f"Error: Workflow '{name}' is not loaded", file=sys.stderr)
        print(f"Run 'synapse workflow load {name}' first.", file=sys.stderr)
        return False

    # Check if already active
    active_workflow = config.get('workflows', {}).get('active_workflow')
    if active_workflow == name:
        print(f"Workflow '{name}' is already active.")
        return True

    # Get loaded workflow directory
    loaded_workflows_dir = get_loaded_workflows_dir(target_dir)
    workflow_dir = loaded_workflows_dir / name

    if not workflow_dir.exists():
        print(f"Error: Workflow directory not found at {workflow_dir}", file=sys.stderr)
        print(f"The workflow may be corrupted. Try reloading it.", file=sys.stderr)
        return False

    print(f"Switching to workflow '{name}'...")

    # Preserve user customizations from existing .claude/settings.json
    claude_dir = target_dir / ".claude"
    claude_settings_path = claude_dir / "settings.json"
    current_user_customizations = {}

    if claude_settings_path.exists():
        try:
            with open(claude_settings_path, 'r') as f:
                current_claude_settings = json.load(f)

            if active_workflow:
                # We have an active workflow - compare to extract user customizations
                current_workflow_dir = get_loaded_workflows_dir(target_dir) / active_workflow
                current_workflow_settings_path = current_workflow_dir / "settings.json"

                if current_workflow_settings_path.exists():
                    with open(current_workflow_settings_path, 'r') as f:
                        current_workflow_settings = json.load(f)

                    # Extract user customizations by comparing
                    import copy

                    # For hooks, find user-added hooks
                    if 'hooks' in current_claude_settings:
                        current_user_customizations['hooks'] = {}

                        for hook_type, matchers in current_claude_settings['hooks'].items():
                            workflow_matchers = current_workflow_settings.get('hooks', {}).get(hook_type, [])

                            # Convert workflow hooks to comparable format (with absolute paths)
                            comparable_workflow_matchers = []
                            for m in workflow_matchers:
                                comparable = copy.deepcopy(m)
                                if 'hooks' in comparable:
                                    for h in comparable['hooks']:
                                        if 'command' in h and '.claude/' in h['command']:
                                            h['command'] = h['command'].replace('.claude/', str(claude_dir) + '/')
                                comparable_workflow_matchers.append(comparable)

                            # Find matchers that are not in workflow
                            user_matchers = []
                            for matcher in matchers:
                                if matcher not in comparable_workflow_matchers:
                                    # Convert absolute paths back to relative
                                    user_matcher = copy.deepcopy(matcher)
                                    if 'hooks' in user_matcher:
                                        for h in user_matcher['hooks']:
                                            if 'command' in h:
                                                h['command'] = h['command'].replace(str(claude_dir) + '/', '.claude/')
                                    user_matchers.append(user_matcher)

                            if user_matchers:
                                current_user_customizations['hooks'][hook_type] = user_matchers

                    # Extract other top-level settings
                    for key, value in current_claude_settings.items():
                        if key != 'hooks' and key not in current_workflow_settings:
                            current_user_customizations[key] = value
                        elif key != 'hooks' and current_claude_settings[key] != current_workflow_settings.get(key):
                            # Value differs from workflow default - it's a user customization
                            current_user_customizations[key] = value
            else:
                # No active workflow - treat entire .claude/settings.json as user customizations
                # This handles the case where user manually created settings or had a deactivated workflow
                import copy
                current_user_customizations = copy.deepcopy(current_claude_settings)
                # Convert absolute paths to relative in hooks for portability
                if 'hooks' in current_user_customizations:
                    for hook_type, matchers in current_user_customizations['hooks'].items():
                        for matcher_idx, matcher in enumerate(matchers):
                            if 'hooks' in matcher:
                                for hook_idx, hook in enumerate(matcher['hooks']):
                                    if 'command' in hook and str(claude_dir) in hook['command']:
                                        current_user_customizations['hooks'][hook_type][matcher_idx]['hooks'][hook_idx]['command'] = \
                                            hook['command'].replace(str(claude_dir) + '/', '.claude/')

        except Exception as e:
            print(f"  ⚠ Warning: Could not preserve existing settings: {e}", file=sys.stderr)

    # Clear existing .claude subdirectories
    if not claude_dir.exists():
        claude_dir.mkdir(parents=True)

    dirs_to_clear = [
        claude_dir / "agents",
        claude_dir / "hooks",
        claude_dir / "commands" / "synapse"
    ]

    for dir_path in dirs_to_clear:
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"  ✓ Cleared {dir_path.relative_to(target_dir)}")
            except Exception as e:
                print(f"  ⚠ Warning: Could not clear {dir_path}: {e}", file=sys.stderr)

    # Copy workflow directories to .claude/
    copy_count = 0
    directory_mappings = [
        ("agents", "agents"),
        ("hooks", "hooks"),
        ("commands/synapse", "commands/synapse"),
    ]

    for src_subdir, dst_subdir in directory_mappings:
        src_path = workflow_dir / src_subdir
        dst_path = claude_dir / dst_subdir

        if src_path.exists():
            try:
                # Create parent directory if needed
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(src_path, dst_path)
                print(f"  ✓ Copied {src_subdir}")

                # Make shell scripts executable in hooks
                if dst_subdir == "hooks":
                    for hook_file in dst_path.glob("*.sh"):
                        hook_file.chmod(0o755)

                copy_count += 1
            except Exception as e:
                print(f"  ⚠ Warning: Could not copy {src_subdir}: {e}", file=sys.stderr)

    # Merge settings.json (workflow + user settings)
    workflow_settings_path = workflow_dir / "settings.json"
    if workflow_settings_path.exists():
        try:
            with open(workflow_settings_path, 'r') as f:
                workflow_settings = json.load(f)

            # Load saved user settings from .synapse/user-settings.json
            saved_user_settings = load_user_settings(target_dir)

            # Combine current customizations with saved user settings
            import copy
            combined_user_settings = copy.deepcopy(saved_user_settings)

            # Merge current_user_customizations into combined_user_settings
            if current_user_customizations:
                # Merge hooks
                if 'hooks' in current_user_customizations:
                    if 'hooks' not in combined_user_settings:
                        combined_user_settings['hooks'] = {}
                    for hook_type, matchers in current_user_customizations['hooks'].items():
                        if hook_type not in combined_user_settings['hooks']:
                            combined_user_settings['hooks'][hook_type] = []
                        # Append current customizations
                        for matcher in matchers:
                            if matcher not in combined_user_settings['hooks'][hook_type]:
                                combined_user_settings['hooks'][hook_type].append(matcher)

                # Merge other top-level settings
                for key, value in current_user_customizations.items():
                    if key != 'hooks':
                        combined_user_settings[key] = value

            # Merge workflow and combined user settings
            merged_settings = merge_settings(workflow_settings, combined_user_settings, claude_dir)

            # Write merged settings
            claude_settings_path = claude_dir / "settings.json"
            with open(claude_settings_path, 'w') as f:
                json.dump(merged_settings, f, indent=2)
                f.write('\n')

            # Update saved user settings if we found new customizations
            if current_user_customizations:
                save_user_settings(combined_user_settings, target_dir)

            if combined_user_settings:
                print(f"  ✓ Merged workflow + user settings")
            else:
                print(f"  ✓ Applied workflow settings")
        except Exception as e:
            print(f"  ⚠ Warning: Could not merge settings.json: {e}", file=sys.stderr)

    # Update active_workflow in config
    if 'workflows' not in config:
        config['workflows'] = {}

    config['workflows']['active_workflow'] = name
    config['workflows']['last_switch'] = datetime.now().isoformat()

    if save_config(config, target_dir):
        print(f"  ✓ Updated active workflow in config.json")
    else:
        print(f"  ⚠ Warning: Could not update config.json", file=sys.stderr)

    print(f"\nSwitched to workflow '{name}' successfully!")
    print(f"Copied {copy_count} directory/directories")

    return True


def unload_workflow(name: str, target_dir: Path = None, force: bool = False) -> bool:
    """Unload a workflow from the project.

    Args:
        name: Name of the workflow to unload
        target_dir: Target project directory. Defaults to current directory.
        force: Force unload even if workflow is currently active

    Returns:
        True if workflow was unloaded successfully, False otherwise
    """
    if target_dir is None:
        target_dir = Path.cwd()

    # Validate synapse is initialized
    config = load_config(target_dir)
    if not config:
        print(f"Error: Synapse not initialized in {target_dir}", file=sys.stderr)
        print("Run 'synapse init' first.", file=sys.stderr)
        return False

    # Check if workflow is loaded
    loaded_workflows = config.get('workflows', {}).get('loaded_workflows', [])
    workflow_loaded = any(w.get('name') == name for w in loaded_workflows)

    if not workflow_loaded:
        print(f"Error: Workflow '{name}' is not loaded", file=sys.stderr)
        return False

    # Check if workflow is currently active
    active_workflow = config.get('workflows', {}).get('active_workflow')
    if active_workflow == name:
        if not force:
            print(f"Error: Cannot unload active workflow '{name}'", file=sys.stderr)
            print(f"Options:", file=sys.stderr)
            print(f"  - Deactivate first: synapse workflow deactivate", file=sys.stderr)
            print(f"  - Switch to another workflow: synapse workflow switch <name>", file=sys.stderr)
            print(f"  - Force unload: synapse workflow unload {name} --force", file=sys.stderr)
            return False
        else:
            # Force unload: deactivate first
            print(f"Force unloading active workflow '{name}'...")
            print(f"Deactivating workflow first...")
            if not deactivate_workflow(target_dir):
                print(f"Error: Failed to deactivate workflow", file=sys.stderr)
                return False
            print()

    print(f"Unloading workflow '{name}'...")

    # Remove workflow directory
    loaded_workflows_dir = get_loaded_workflows_dir(target_dir)
    workflow_dir = loaded_workflows_dir / name

    if workflow_dir.exists():
        try:
            shutil.rmtree(workflow_dir)
            print(f"  ✓ Removed workflow directory")
        except Exception as e:
            print(f"Error: Could not remove workflow directory: {e}", file=sys.stderr)
            return False
    else:
        print(f"  ⚠ Warning: Workflow directory not found (may already be removed)")

    # Update config.json
    loaded_workflows = [w for w in loaded_workflows if w.get('name') != name]
    config['workflows']['loaded_workflows'] = loaded_workflows

    # Clear active_workflow if this was the active one
    if active_workflow == name:
        config['workflows']['active_workflow'] = None
        print(f"  ✓ Cleared active workflow")

    if save_config(config, target_dir):
        print(f"  ✓ Updated config.json")
    else:
        print(f"  ⚠ Warning: Could not update config.json", file=sys.stderr)

    print(f"\nWorkflow '{name}' unloaded successfully!")

    return True


def deactivate_workflow(target_dir: Path = None) -> bool:
    """Deactivate the currently active workflow without unloading it.

    This clears the .claude/ directories and sets active_workflow to None,
    but keeps the workflow loaded in .synapse/workflows/ for easy reactivation.

    Args:
        target_dir: Target project directory. Defaults to current directory.

    Returns:
        True if workflow was deactivated successfully, False otherwise
    """
    if target_dir is None:
        target_dir = Path.cwd()

    # Validate synapse is initialized
    config = load_config(target_dir)
    if not config:
        print(f"Error: Synapse not initialized in {target_dir}", file=sys.stderr)
        print("Run 'synapse init' first.", file=sys.stderr)
        return False

    # Check if there's an active workflow
    active_workflow = config.get('workflows', {}).get('active_workflow')
    if not active_workflow:
        print("No active workflow to deactivate.")
        return True

    print(f"Deactivating workflow '{active_workflow}'...")

    # Clear .claude/ subdirectories
    claude_dir = target_dir / ".claude"
    dirs_to_clear = [
        claude_dir / "agents",
        claude_dir / "hooks",
        claude_dir / "commands" / "synapse"
    ]

    for dir_path in dirs_to_clear:
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"  ✓ Cleared {dir_path.relative_to(target_dir)}")
            except Exception as e:
                print(f"  ⚠ Warning: Could not clear {dir_path}: {e}", file=sys.stderr)

    # Clear settings.json (or remove workflow-specific settings)
    settings_path = claude_dir / "settings.json"
    if settings_path.exists():
        try:
            settings_path.unlink()
            print(f"  ✓ Removed settings.json")
        except Exception as e:
            print(f"  ⚠ Warning: Could not remove settings.json: {e}", file=sys.stderr)

    # Update config.json
    config['workflows']['active_workflow'] = None
    config['workflows']['last_switch'] = datetime.now().isoformat()

    if save_config(config, target_dir):
        print(f"  ✓ Updated config.json")
    else:
        print(f"  ⚠ Warning: Could not update config.json", file=sys.stderr)

    print(f"\nWorkflow '{active_workflow}' deactivated successfully!")
    print(f"The workflow is still loaded and can be reactivated with:")
    print(f"  synapse workflow switch {active_workflow}")

    return True


def workflow_apply(name: str, force: bool = False) -> None:
    """Apply a workflow to the current project.

    This is a convenience command that combines load + switch.
    For backward compatibility with the old apply/remove workflow.

    Args:
        name: Name of the workflow to apply
        force: Force reload if workflow is already loaded
    """
    target_dir = Path.cwd()

    # Get workflow info for display
    info = get_workflow_info(name)
    print(f"Applying workflow: {name}")
    if info and info.get("description"):
        print(f"  {info['description']}")
    print()

    # Check if workflow is already loaded
    config = load_config(target_dir)
    if config:
        loaded_workflows = config.get('workflows', {}).get('loaded_workflows', [])
        already_loaded = any(w.get('name') == name for w in loaded_workflows)

        if already_loaded and not force:
            print(f"Workflow '{name}' is already loaded.")
            print(f"Switching to it...\n")
            # Just switch, don't reload
            if switch_workflow(name, target_dir):
                print("\n" + "=" * 60)
                print(f"Workflow '{name}' is now active!")
                return
            else:
                sys.exit(1)

    # Load the workflow
    print("Step 1: Loading workflow")
    print("-" * 60)
    if not load_workflow(name, target_dir, force=force):
        print("\nError: Failed to load workflow", file=sys.stderr)
        sys.exit(1)

    # Switch to the workflow
    print("\n" + "=" * 60)
    print("Step 2: Switching to workflow")
    print("-" * 60)
    if not switch_workflow(name, target_dir):
        print("\nError: Failed to switch to workflow", file=sys.stderr)
        sys.exit(1)

    print("\n" + "=" * 60)
    print(f"Workflow '{name}' applied successfully!")
    print("\nYou can now:")
    print(f"  - Switch to other loaded workflows with: synapse workflow switch <name>")
    print(f"  - See loaded workflows with: synapse workflow loaded")
    print(f"  - Unload this workflow with: synapse workflow unload {name}")


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
  synapse init                                Initialize synapse in current directory
  synapse init /path/to/project               Initialize synapse in specific directory

  # Workflow management
  synapse workflow list                       List available workflows
  synapse workflow load <name>                Load a workflow into project
  synapse workflow switch <name>              Switch to a loaded workflow
  synapse workflow loaded                     Show loaded workflows
  synapse workflow active                     Show active workflow
  synapse workflow deactivate                 Deactivate active workflow (keeps it loaded)
  synapse workflow extract-user-settings      Extract user settings from active workflow
  synapse workflow unload <name>              Unload a workflow
  synapse workflow apply <name>               Apply workflow (convenience: load + switch)

  # Quality validation
  synapse validate-quality                    Validate quality commands configuration
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
        help="Workflow name or subcommand (list, load, switch, loaded, active, deactivate, extract-user-settings, unload, apply)"
    )

    # Second optional positional argument for workflow name (when using subcommands)
    workflow_parser.add_argument(
        "workflow_name",
        nargs="?",
        default=None,
        help="Workflow name (required for load, switch, unload, apply subcommands)"
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
        workflow_cmd = args.workflow_name_or_command
        workflow_name = args.workflow_name

        # List available workflows from resources
        if workflow_cmd == "list":
            workflow_list()

        # Load a workflow into .synapse/workflows/
        elif workflow_cmd == "load":
            if not workflow_name:
                print("Error: Missing workflow name", file=sys.stderr)
                print("Usage: synapse workflow load <name>", file=sys.stderr)
                sys.exit(1)
            load_workflow(workflow_name, force=args.force)

        # Switch to a loaded workflow
        elif workflow_cmd == "switch":
            if not workflow_name:
                print("Error: Missing workflow name", file=sys.stderr)
                print("Usage: synapse workflow switch <name>", file=sys.stderr)
                sys.exit(1)
            switch_workflow(workflow_name)

        # Show loaded workflows
        elif workflow_cmd == "loaded":
            workflow_loaded_list()

        # Show active workflow
        elif workflow_cmd == "active":
            workflow_active()

        # Deactivate the active workflow
        elif workflow_cmd == "deactivate":
            deactivate_workflow()

        # Extract user settings from active workflow
        elif workflow_cmd == "extract-user-settings":
            extract_user_settings_from_active()

        # Unload a workflow
        elif workflow_cmd == "unload":
            if not workflow_name:
                print("Error: Missing workflow name", file=sys.stderr)
                print("Usage: synapse workflow unload <name>", file=sys.stderr)
                sys.exit(1)
            unload_workflow(workflow_name, force=args.force)

        # Apply workflow (convenience: load + switch in one command)
        elif workflow_cmd == "apply":
            if not workflow_name:
                print("Error: Missing workflow name", file=sys.stderr)
                print("Usage: synapse workflow apply <name>", file=sys.stderr)
                sys.exit(1)
            workflow_apply(workflow_name, args.force)

        else:
            # Treat as workflow name for apply behavior
            # This allows: synapse workflow <name> (shorthand for apply)
            if validate_workflow_exists(workflow_cmd):
                workflow_apply(workflow_cmd, args.force)
            else:
                print(f"Error: Unknown workflow or subcommand '{workflow_cmd}'", file=sys.stderr)
                print("Run 'synapse workflow list' to see available workflows.", file=sys.stderr)
                print("Run 'synapse --help' to see available subcommands.", file=sys.stderr)
                sys.exit(1)
    elif args.command == "validate-quality":
        validate_quality()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()