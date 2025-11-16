"""CLI interface for Synapse.

Provides command-line argument parsing and command dispatching.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .commands.init import get_init_command
from .commands.workflow import get_workflow_command


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser.

    Returns:
        Configured ArgumentParser instance
    """
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

    return parser


def dispatch_command(args: argparse.Namespace) -> int:
    """Dispatch parsed arguments to the appropriate command handler.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    if args.command == "init":
        # Handle init command
        init_cmd = get_init_command(__version__)
        init_cmd.execute(args.directory)
        return 0

    elif args.command == "workflow":
        # Handle workflow subcommands and workflow application
        workflow_cmd = get_workflow_command(__version__)
        workflow_arg = args.workflow_name_or_command

        if workflow_arg == "list":
            workflow_cmd.list()
            return 0

        elif workflow_arg == "status":
            workflow_cmd.status()
            return 0

        elif workflow_arg == "remove":
            success = workflow_cmd.remove()
            return 0 if success else 1

        else:
            # Apply workflow by name
            success = workflow_cmd.apply(workflow_arg, force=args.force)
            return 0 if success else 1

    else:
        # No command provided, show help
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    try:
        return dispatch_command(args)
    except SystemExit as e:
        # Commands may call sys.exit(), catch and return the code
        return e.code if e.code is not None else 1
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.", file=sys.stderr)
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
