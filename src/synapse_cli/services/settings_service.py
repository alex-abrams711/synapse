"""Settings merging and management."""
from pathlib import Path
from typing import Optional, Dict, List, Any
import json
import re
import sys

from ..infrastructure.resources import get_resource_manager


class SettingsService:
    """Handles settings.json merging and hook path conversion."""

    def __init__(self):
        self.resource_manager = get_resource_manager()

    def convert_hook_paths_to_absolute(
        self,
        hooks_config: Dict,
        target_dir: Path
    ) -> Dict:
        """
        Convert relative .claude/ paths to absolute in hook commands.

        Args:
            hooks_config: Hooks configuration from settings.json
            target_dir: Target project directory

        Returns:
            Modified hooks_config with absolute paths
        """
        for hook_type, matchers in hooks_config.items():
            for matcher_group in matchers:
                for hook in matcher_group.get('hooks', []):
                    if 'command' in hook:
                        command = hook['command']

                        # Pattern: .claude/... paths
                        pattern = r'(^|\s)(\.claude/[^\s]+)'

                        def replace_with_absolute(match):
                            prefix = match.group(1)
                            relative_path = match.group(2)
                            absolute_path = str((target_dir / relative_path).resolve())
                            return f"{prefix}{absolute_path}"

                        hook['command'] = re.sub(pattern, replace_with_absolute, command)

        return hooks_config

    def merge_settings_json(
        self,
        workflow_name: str,
        target_dir: Path
    ) -> Dict[str, Any]:
        """
        Merge workflow settings.json with existing settings.

        Args:
            workflow_name: Workflow to apply
            target_dir: Target project directory

        Returns:
            Dictionary with merge results:
            {
                'merged': bool,
                'created': bool,
                'hooks_added': list,
                'settings_updated': list,
                'error': str or None
            }
        """
        workflow_dir = self.resource_manager.workflows_dir / workflow_name
        workflow_settings_file = workflow_dir / "settings.json"

        result = {
            'merged': False,
            'created': False,
            'hooks_added': [],
            'settings_updated': [],
            'error': None
        }

        # If no settings.json, nothing to merge
        if not workflow_settings_file.exists():
            return result

        # Load workflow settings
        try:
            with open(workflow_settings_file, 'r') as f:
                workflow_settings = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            result['error'] = f"Invalid workflow settings: {e}"
            return result

        # Convert hook paths
        if 'hooks' in workflow_settings:
            workflow_settings['hooks'] = self.convert_hook_paths_to_absolute(
                workflow_settings['hooks'],
                target_dir
            )

        # Load existing settings
        claude_dir = target_dir / ".claude"
        target_settings_file = claude_dir / "settings.json"

        claude_dir.mkdir(parents=True, exist_ok=True)

        existing_settings = {}
        if target_settings_file.exists():
            try:
                with open(target_settings_file, 'r') as f:
                    existing_settings = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                result['error'] = f"Invalid existing settings: {e}"
                return result
        else:
            result['created'] = True

        # Merge settings
        merged_settings = existing_settings.copy()

        # Special handling for hooks
        if 'hooks' in workflow_settings:
            hooks_added = self._merge_hooks(
                workflow_settings['hooks'],
                merged_settings.setdefault('hooks', {})
            )
            result['hooks_added'] = hooks_added

        # Merge other settings
        for key, value in workflow_settings.items():
            if key != 'hooks':
                if key not in merged_settings or merged_settings[key] != value:
                    merged_settings[key] = value
                    result['settings_updated'].append(key)

        # Save merged settings
        try:
            with open(target_settings_file, 'w') as f:
                json.dump(merged_settings, f, indent=2)
                f.write('\n')
        except IOError as e:
            result['error'] = f"Could not write settings: {e}"
            return result

        result['merged'] = True
        return result

    def _merge_hooks(
        self,
        workflow_hooks: Dict,
        existing_hooks: Dict
    ) -> List[Dict]:
        """
        Merge workflow hooks into existing hooks.

        Args:
            workflow_hooks: Hooks from workflow settings
            existing_hooks: Existing hooks configuration

        Returns:
            List of hooks that were added
        """
        hooks_added = []

        for hook_type, workflow_matchers in workflow_hooks.items():
            if hook_type not in existing_hooks:
                existing_hooks[hook_type] = []

            existing_matchers = existing_hooks[hook_type]

            # Track existing commands
            existing_commands = set()
            for matcher_group in existing_matchers:
                for hook in matcher_group.get('hooks', []):
                    if 'command' in hook:
                        existing_commands.add(hook['command'])

            # Merge workflow matchers
            for workflow_matcher in workflow_matchers:
                matcher_pattern = workflow_matcher.get('matcher', '')

                # Find existing matcher group
                matching_group = None
                for existing_matcher in existing_matchers:
                    if existing_matcher.get('matcher', '') == matcher_pattern:
                        matching_group = existing_matcher
                        break

                # Create new group if needed
                if matching_group is None:
                    matching_group = {
                        'matcher': matcher_pattern,
                        'hooks': []
                    }
                    existing_matchers.append(matching_group)

                # Add workflow hooks (avoid duplicates)
                for workflow_hook in workflow_matcher.get('hooks', []):
                    command = workflow_hook.get('command', '')
                    if command and command not in existing_commands:
                        matching_group['hooks'].append(workflow_hook)
                        existing_commands.add(command)
                        hooks_added.append({
                            'hook_type': hook_type,
                            'matcher': matcher_pattern,
                            'command': command,
                            'type': workflow_hook.get('type', 'command')
                        })

        return hooks_added

    def remove_hooks_from_settings(
        self,
        hooks_to_remove: List[Dict],
        target_dir: Path
    ) -> bool:
        """
        Remove specific hooks from settings.json.

        Args:
            hooks_to_remove: List of hook definitions to remove
            target_dir: Target project directory

        Returns:
            True if successful, False otherwise
        """
        settings_file = target_dir / ".claude" / "settings.json"

        if not settings_file.exists():
            return True

        try:
            with open(settings_file, 'r') as f:
                settings = json.load(f)

            if 'hooks' not in settings:
                return True

            hooks = settings['hooks']

            # Commands to remove
            commands_to_remove = {
                hook.get('command', '') for hook in hooks_to_remove
                if hook.get('command')
            }

            # Remove hooks
            for hook_type, matchers in hooks.items():
                for matcher_group in matchers:
                    original_hooks = matcher_group.get('hooks', [])
                    filtered_hooks = [
                        hook for hook in original_hooks
                        if hook.get('command', '') not in commands_to_remove
                    ]
                    matcher_group['hooks'] = filtered_hooks

            # Clean up empty groups and types
            for hook_type in list(hooks.keys()):
                hooks[hook_type] = [
                    mg for mg in hooks[hook_type] if mg.get('hooks')
                ]
                if not hooks[hook_type]:
                    del hooks[hook_type]

            # Save
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
                f.write('\n')

            return True
        except (json.JSONDecodeError, IOError):
            return False


# Singleton instance
_settings_service = SettingsService()


def get_settings_service() -> SettingsService:
    """Get the global settings service instance."""
    return _settings_service
