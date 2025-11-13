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

    # Clear existing .claude subdirectories
    claude_dir = target_dir / ".claude"
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

    # Merge settings.json
    workflow_settings_path = workflow_dir / "settings.json"
    if workflow_settings_path.exists():
        try:
            with open(workflow_settings_path, 'r') as f:
                workflow_settings = json.load(f)

            # For now, just use workflow settings directly
            # TODO: Add user settings layer for preserving custom hooks
            claude_settings_path = claude_dir / "settings.json"

            # Convert relative paths to absolute in hooks
            if 'hooks' in workflow_settings:
                for hook_type, commands in workflow_settings['hooks'].items():
                    for i, cmd in enumerate(commands):
                        # Replace relative .claude/ paths with absolute paths
                        if '.claude/' in cmd:
                            workflow_settings['hooks'][hook_type][i] = cmd.replace(
                                '.claude/',
                                str(claude_dir) + '/'
                            )

            with open(claude_settings_path, 'w') as f:
                json.dump(workflow_settings, f, indent=2)
                f.write('\n')

            print(f"  ✓ Updated settings.json")
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
    if active_workflow == name and not force:
        print(f"Error: Cannot unload active workflow '{name}'", file=sys.stderr)
        print(f"Switch to a different workflow first, or use --force to unload anyway.", file=sys.stderr)
        return False

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
        help="Workflow name or subcommand (list, load, switch, loaded, active, unload, apply)"
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