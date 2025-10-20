"""
Synapse CLI - AI Workflow System for Claude Code Integration

A CLI tool that helps developers integrate AI workflow patterns with Claude Code.
Provides structured task planning and quality-gated development execution.
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

__version__ = "0.3.0"

# Exit codes
EXIT_SUCCESS = 0
EXIT_USER_ERROR = 1
EXIT_STATE_ERROR = 2
EXIT_SYSTEM_ERROR = 3
EXIT_VALIDATION_ERROR = 4


def get_resources_dir():
    """
    Locate the resources directory for packaged workflows.

    Works in both editable installs (pip install -e .) and regular installs.

    Returns:
        Path: Path to the resources directory

    Raises:
        FileNotFoundError: If resources directory cannot be found
    """
    # Try pkg_resources first (works for both installed and editable)
    try:
        import pkg_resources
        resources_path = pkg_resources.resource_filename('synapse_cli', 'resources')
        if os.path.exists(resources_path):
            return Path(resources_path)
    except (ImportError, KeyError):
        pass

    # Try importlib.resources for Python 3.9+
    try:
        from importlib import resources
        # In Python 3.9+, we need to use files() API
        if hasattr(resources, 'files'):
            package_path = resources.files('synapse_cli')
            resources_path = package_path / 'resources'
            if resources_path.exists():
                return Path(str(resources_path))
    except (ImportError, AttributeError, TypeError):
        pass

    # Fallback: Look relative to this file (for editable installs)
    # src/synapse_cli/__init__.py -> ../../resources
    current_file = Path(__file__).resolve()
    package_dir = current_file.parent
    src_dir = package_dir.parent
    project_root = src_dir.parent
    resources_path = project_root / 'resources'

    if resources_path.exists():
        return resources_path

    # If we still can't find it, raise error
    raise FileNotFoundError(
        "Could not locate resources directory. "
        "This may indicate a broken installation. "
        "Try reinstalling: pip install --force-reinstall synapse-cli"
    )


def validate_resources_dir(resources_dir):
    """
    Validate that the resources directory has the expected structure.

    Args:
        resources_dir: Path to resources directory

    Returns:
        bool: True if valid, False otherwise
    """
    required_paths = [
        resources_dir / 'commands' / 'synapse',
        resources_dir / 'workflows',
    ]

    for path in required_paths:
        if not path.exists():
            return False

    return True


def main():
    """Main entry point for the Synapse CLI."""
    parser = argparse.ArgumentParser(
        prog="synapse",
        description="AI Workflow System for Claude Code Integration",
        epilog="For more information, visit: https://github.com/alex-abrams711/synapse"
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available commands",
        help="Command to execute"
    )

    # Init command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize Synapse in a project directory"
    )
    init_parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Project directory (default: current directory)"
    )

    # Workflow command
    workflow_parser = subparsers.add_parser(
        "workflow",
        help="Manage workflows"
    )
    workflow_subparsers = workflow_parser.add_subparsers(
        dest="workflow_action",
        title="workflow actions",
        help="Workflow action to perform"
    )

    # Workflow list
    workflow_subparsers.add_parser(
        "list",
        help="List available workflows"
    )

    # Workflow status
    workflow_subparsers.add_parser(
        "status",
        help="Show active workflow status"
    )

    # Workflow remove
    workflow_subparsers.add_parser(
        "remove",
        help="Remove active workflow"
    )

    # Workflow apply (feature-planning, feature-implementation)
    for workflow_name in ["feature-planning", "feature-implementation"]:
        workflow_apply_parser = workflow_subparsers.add_parser(
            workflow_name,
            help=f"Apply {workflow_name} workflow"
        )
        workflow_apply_parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing files and switch from active workflow"
        )

    # Parse arguments
    args = parser.parse_args()

    # Handle no command
    if args.command is None:
        parser.print_help()
        return EXIT_SUCCESS

    # Route to command handlers
    try:
        if args.command == "init":
            return handle_init(args)
        elif args.command == "workflow":
            return handle_workflow(args)
        else:
            print(f"Error: Unknown command '{args.command}'", file=sys.stderr)
            parser.print_help()
            return EXIT_USER_ERROR
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return EXIT_USER_ERROR
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return EXIT_SYSTEM_ERROR


def handle_init(args):
    """Handle the init command."""
    directory = Path(args.directory).resolve()

    # Check if directory exists
    if not directory.exists():
        print(f"Error: Directory does not exist: {directory}", file=sys.stderr)
        return EXIT_USER_ERROR

    # Check if already initialized
    synapse_dir = directory / '.synapse'
    if synapse_dir.exists():
        print(f"Synapse is already initialized in: {directory}")
        print("Configuration found at: .synapse/config.json")
        return EXIT_SUCCESS

    try:
        # Create .synapse directory structure
        print(f"Initializing Synapse in: {directory}")
        synapse_dir.mkdir(parents=True, exist_ok=True)
        (synapse_dir / 'commands' / 'synapse').mkdir(parents=True, exist_ok=True)
        (synapse_dir / 'backups').mkdir(parents=True, exist_ok=True)

        # Create config.json
        project_name = directory.name
        config = {
            "synapse_version": __version__,
            "initialized_at": datetime.now().isoformat(),
            "project": {
                "name": project_name,
                "root_directory": str(directory)
            },
            "agent": {
                "type": "claude-code",
                "description": "Claude Code AI coding assistant"
            },
            "workflows": {
                "active_workflow": None,
                "applied_workflows": []
            },
            "settings": {
                "auto_backup": True,
                "strict_validation": True,
                "uv_required": True
            }
        }

        config_path = synapse_dir / 'config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        # Copy sense.md command
        try:
            resources_dir = get_resources_dir()
            sense_source = resources_dir / 'commands' / 'synapse' / 'sense.md'
            sense_dest = synapse_dir / 'commands' / 'synapse' / 'sense.md'

            if sense_source.exists():
                shutil.copy2(sense_source, sense_dest)
                print("✓ Copied sense command to .synapse/commands/synapse/")
            else:
                print("Warning: sense.md not found in resources", file=sys.stderr)

        except FileNotFoundError as e:
            print(f"Warning: Could not copy sense command: {e}", file=sys.stderr)

        # Success message
        print("\n✓ Synapse initialized successfully!")
        print("\nConfiguration created:")
        print("  - .synapse/config.json")
        print("  - .synapse/commands/synapse/sense.md")
        print("\nNext steps:")
        print("  1. Apply a workflow: synapse workflow feature-planning")
        print("  2. Or: synapse workflow feature-implementation")
        print("  3. List workflows: synapse workflow list")

        return EXIT_SUCCESS

    except PermissionError as e:
        print(f"Error: Permission denied: {e}", file=sys.stderr)
        print(f"Please check that you have write access to: {directory}", file=sys.stderr)
        return EXIT_SYSTEM_ERROR

    except Exception as e:
        print(f"Error during initialization: {e}", file=sys.stderr)
        # Clean up partial initialization
        if synapse_dir.exists():
            try:
                shutil.rmtree(synapse_dir)
                print("Cleaned up partial initialization", file=sys.stderr)
            except Exception:
                pass
        return EXIT_SYSTEM_ERROR


def handle_workflow(args):
    """Handle workflow commands."""
    if args.workflow_action is None:
        print("Error: No workflow action specified", file=sys.stderr)
        print("Use 'synapse workflow --help' for available actions")
        return EXIT_USER_ERROR

    if args.workflow_action == "list":
        print("Available workflows:")
        print("  - feature-planning")
        print("  - feature-implementation")
        return EXIT_SUCCESS

    elif args.workflow_action == "status":
        print("No active workflow")
        return EXIT_SUCCESS

    elif args.workflow_action == "remove":
        print("No workflow to remove")
        return EXIT_SUCCESS

    elif args.workflow_action in ["feature-planning", "feature-implementation"]:
        force_flag = "--force" if args.force else ""
        print(f"Applying workflow: {args.workflow_action} {force_flag}")
        print("(Implementation coming soon)")
        return EXIT_SUCCESS

    else:
        print(f"Error: Unknown workflow action '{args.workflow_action}'", file=sys.stderr)
        return EXIT_USER_ERROR


if __name__ == "__main__":
    sys.exit(main())
