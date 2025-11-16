"""Init command for Synapse CLI.

Handles project initialization and configuration.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from ..infrastructure.config_store import ConfigStore
from ..infrastructure.resources import ResourceManager


class InitCommand:
    """Command for initializing Synapse in a project directory."""

    def __init__(
        self,
        synapse_version: str,
        resource_manager: Optional[ResourceManager] = None,
        config_store: Optional[ConfigStore] = None
    ):
        """Initialize the init command.

        Args:
            synapse_version: Version string for Synapse CLI
            resource_manager: Resource manager instance (optional, uses singleton if not provided)
            config_store: Config store instance (optional, uses singleton if not provided)
        """
        self.synapse_version = synapse_version

        # Use provided dependencies or fall back to singletons
        if resource_manager is None:
            from ..infrastructure.resources import get_resource_manager
            resource_manager = get_resource_manager()
        self.resource_manager = resource_manager

        if config_store is None:
            from ..infrastructure.config_store import get_config_store
            config_store = get_config_store()
        self.config_store = config_store

    def execute(self, target_dir: Optional[Path] = None) -> None:
        """Execute the init command.

        Args:
            target_dir: Directory to initialize synapse in. Defaults to current directory.

        Raises:
            SystemExit: If directory is already initialized or initialization fails
        """
        if target_dir is None:
            target_dir = Path.cwd()

        synapse_dir = target_dir / ".synapse"

        # Check if .synapse already exists
        if synapse_dir.exists():
            print(f"Error: .synapse directory already exists at {synapse_dir}", file=sys.stderr)
            print("Remove it first or run 'synapse init' in a different directory.", file=sys.stderr)
            sys.exit(1)

        print(f"Initializing synapse in {target_dir}")

        # Prompt for AI agent selection
        agent_info = self._prompt_agent_selection()

        # Create .synapse directory structure
        synapse_dir.mkdir(parents=True)

        # Create baseline config.json
        if not self._create_config(target_dir, agent_info):
            sys.exit(1)

        print(f"\nSynapse initialized successfully!")
        print(f"\nDirectory structure created:")
        print(f"  {synapse_dir}/")
        print(f"  └── config.json")
        print(f"\nUse 'synapse workflow <name>' to apply agents, hooks, and commands.")

    def _prompt_agent_selection(self) -> Dict[str, str]:
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

    def _create_config(self, target_dir: Path, agent_info: Dict[str, str]) -> bool:
        """Create config.json from template.

        Args:
            target_dir: Target project directory
            agent_info: Agent information dictionary

        Returns:
            True if successful, False otherwise
        """
        resources_dir = self.resource_manager.resources_dir
        config_template_path = resources_dir / "settings" / "config-template.json"
        config_dst_path = target_dir / ".synapse" / "config.json"

        if not config_template_path.exists():
            print(f"  Warning: Baseline config template not found at {config_template_path}", file=sys.stderr)
            return False

        try:
            # Load template
            with open(config_template_path, 'r') as f:
                config = json.load(f)

            # Populate with current values
            config['synapse_version'] = self.synapse_version
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
            return True

        except (json.JSONDecodeError, IOError) as e:
            print(f"  Warning: Could not create config.json: {e}", file=sys.stderr)
            return False


# Singleton instance
_init_command_instance: Optional[InitCommand] = None


def get_init_command(synapse_version: str) -> InitCommand:
    """Get or create the singleton InitCommand instance.

    Args:
        synapse_version: Version string for Synapse CLI

    Returns:
        The singleton InitCommand instance
    """
    global _init_command_instance
    if _init_command_instance is None:
        _init_command_instance = InitCommand(synapse_version)
    return _init_command_instance
