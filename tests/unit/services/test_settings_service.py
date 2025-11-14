"""Unit tests for services/settings_service.py."""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, PropertyMock
from synapse_cli.services.settings_service import SettingsService, get_settings_service


class TestSettingsService:
    """Test SettingsService class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def settings_service(self):
        """Create SettingsService instance for testing."""
        return SettingsService()

    @pytest.fixture
    def mock_resource_manager(self, settings_service, temp_dir):
        """Mock resource manager with temp workflows directory."""
        mock = Mock()
        workflows_dir = temp_dir / "workflows"
        workflows_dir.mkdir()
        type(mock).workflows_dir = PropertyMock(return_value=workflows_dir)
        settings_service.resource_manager = mock
        return mock

    def test_singleton_pattern(self):
        """Test that get_settings_service returns the same instance."""
        service1 = get_settings_service()
        service2 = get_settings_service()
        assert service1 is service2

    def test_convert_hook_paths_to_absolute_simple(self, settings_service, temp_dir):
        """Test convert_hook_paths_to_absolute with simple paths."""
        hooks_config = {
            "user_prompt_submit": [
                {
                    "matcher": "**/*.py",
                    "hooks": [
                        {
                            "type": "command",
                            "command": ".claude/hooks/test.py"
                        }
                    ]
                }
            ]
        }

        result = settings_service.convert_hook_paths_to_absolute(hooks_config, temp_dir)

        expected_path = str((temp_dir / ".claude/hooks/test.py").resolve())
        assert result["user_prompt_submit"][0]["hooks"][0]["command"] == expected_path

    def test_convert_hook_paths_to_absolute_with_arguments(self, settings_service, temp_dir):
        """Test convert_hook_paths_to_absolute with command arguments."""
        hooks_config = {
            "user_prompt_submit": [
                {
                    "matcher": "**/*.py",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python .claude/hooks/test.py --arg value"
                        }
                    ]
                }
            ]
        }

        result = settings_service.convert_hook_paths_to_absolute(hooks_config, temp_dir)

        expected_path = str((temp_dir / ".claude/hooks/test.py").resolve())
        expected_command = f"python {expected_path} --arg value"
        assert result["user_prompt_submit"][0]["hooks"][0]["command"] == expected_command

    def test_convert_hook_paths_to_absolute_multiple_paths(self, settings_service, temp_dir):
        """Test convert_hook_paths_to_absolute with multiple paths in command."""
        hooks_config = {
            "user_prompt_submit": [
                {
                    "matcher": "**/*.py",
                    "hooks": [
                        {
                            "type": "command",
                            "command": ".claude/hooks/test1.py && .claude/hooks/test2.py"
                        }
                    ]
                }
            ]
        }

        result = settings_service.convert_hook_paths_to_absolute(hooks_config, temp_dir)

        path1 = str((temp_dir / ".claude/hooks/test1.py").resolve())
        path2 = str((temp_dir / ".claude/hooks/test2.py").resolve())
        expected_command = f"{path1} && {path2}"
        assert result["user_prompt_submit"][0]["hooks"][0]["command"] == expected_command

    def test_convert_hook_paths_to_absolute_no_claude_paths(self, settings_service, temp_dir):
        """Test convert_hook_paths_to_absolute with no .claude paths."""
        hooks_config = {
            "user_prompt_submit": [
                {
                    "matcher": "**/*.py",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python test.py"
                        }
                    ]
                }
            ]
        }

        result = settings_service.convert_hook_paths_to_absolute(hooks_config, temp_dir)

        # Should remain unchanged
        assert result["user_prompt_submit"][0]["hooks"][0]["command"] == "python test.py"

    def test_convert_hook_paths_to_absolute_empty_hooks(self, settings_service, temp_dir):
        """Test convert_hook_paths_to_absolute with empty hooks."""
        hooks_config = {}

        result = settings_service.convert_hook_paths_to_absolute(hooks_config, temp_dir)

        assert result == {}

    def test_merge_settings_json_new_file(
        self, settings_service, mock_resource_manager, temp_dir
    ):
        """Test merge_settings_json creating new settings file."""
        workflow_dir = mock_resource_manager.workflows_dir / "test-workflow"
        workflow_dir.mkdir()

        workflow_settings = {
            "key1": "value1",
            "key2": "value2"
        }
        (workflow_dir / "settings.json").write_text(json.dumps(workflow_settings))

        result = settings_service.merge_settings_json("test-workflow", temp_dir)

        assert result['merged'] is True
        assert result['created'] is True
        assert result['error'] is None
        assert 'key1' in result['settings_updated']
        assert 'key2' in result['settings_updated']

        # Verify file was created
        settings_file = temp_dir / ".claude" / "settings.json"
        assert settings_file.exists()

        with open(settings_file, 'r') as f:
            saved_settings = json.load(f)
        assert saved_settings == workflow_settings

    def test_merge_settings_json_existing_file(
        self, settings_service, mock_resource_manager, temp_dir
    ):
        """Test merge_settings_json with existing settings file."""
        workflow_dir = mock_resource_manager.workflows_dir / "test-workflow"
        workflow_dir.mkdir()

        workflow_settings = {
            "new_key": "new_value"
        }
        (workflow_dir / "settings.json").write_text(json.dumps(workflow_settings))

        # Create existing settings
        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir()
        existing_settings = {
            "existing_key": "existing_value"
        }
        (claude_dir / "settings.json").write_text(json.dumps(existing_settings))

        result = settings_service.merge_settings_json("test-workflow", temp_dir)

        assert result['merged'] is True
        assert result['created'] is False
        assert 'new_key' in result['settings_updated']

        # Verify both keys exist
        with open(claude_dir / "settings.json", 'r') as f:
            saved_settings = json.load(f)
        assert saved_settings['existing_key'] == 'existing_value'
        assert saved_settings['new_key'] == 'new_value'

    def test_merge_settings_json_no_workflow_settings(
        self, settings_service, mock_resource_manager, temp_dir
    ):
        """Test merge_settings_json when workflow has no settings.json."""
        workflow_dir = mock_resource_manager.workflows_dir / "test-workflow"
        workflow_dir.mkdir()
        # Don't create settings.json

        result = settings_service.merge_settings_json("test-workflow", temp_dir)

        assert result['merged'] is False
        assert result['created'] is False
        assert result['error'] is None

    def test_merge_settings_json_invalid_workflow_settings(
        self, settings_service, mock_resource_manager, temp_dir
    ):
        """Test merge_settings_json with invalid workflow settings."""
        workflow_dir = mock_resource_manager.workflows_dir / "test-workflow"
        workflow_dir.mkdir()
        (workflow_dir / "settings.json").write_text("invalid json {")

        result = settings_service.merge_settings_json("test-workflow", temp_dir)

        assert result['merged'] is False
        assert result['error'] is not None
        assert "Invalid workflow settings" in result['error']

    def test_merge_settings_json_invalid_existing_settings(
        self, settings_service, mock_resource_manager, temp_dir
    ):
        """Test merge_settings_json with invalid existing settings."""
        workflow_dir = mock_resource_manager.workflows_dir / "test-workflow"
        workflow_dir.mkdir()
        (workflow_dir / "settings.json").write_text('{"key": "value"}')

        # Create invalid existing settings
        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir()
        (claude_dir / "settings.json").write_text("invalid json {")

        result = settings_service.merge_settings_json("test-workflow", temp_dir)

        assert result['merged'] is False
        assert result['error'] is not None
        assert "Invalid existing settings" in result['error']

    def test_merge_settings_json_with_hooks(
        self, settings_service, mock_resource_manager, temp_dir
    ):
        """Test merge_settings_json with hooks."""
        workflow_dir = mock_resource_manager.workflows_dir / "test-workflow"
        workflow_dir.mkdir()

        workflow_settings = {
            "hooks": {
                "user_prompt_submit": [
                    {
                        "matcher": "**/*.py",
                        "hooks": [
                            {
                                "type": "command",
                                "command": ".claude/hooks/test.py"
                            }
                        ]
                    }
                ]
            }
        }
        (workflow_dir / "settings.json").write_text(json.dumps(workflow_settings))

        result = settings_service.merge_settings_json("test-workflow", temp_dir)

        assert result['merged'] is True
        assert len(result['hooks_added']) == 1
        assert result['hooks_added'][0]['hook_type'] == 'user_prompt_submit'

    def test_merge_hooks_new_hook_type(self, settings_service):
        """Test _merge_hooks with new hook type."""
        workflow_hooks = {
            "user_prompt_submit": [
                {
                    "matcher": "**/*.py",
                    "hooks": [
                        {"type": "command", "command": "test.py"}
                    ]
                }
            ]
        }
        existing_hooks = {}

        hooks_added = settings_service._merge_hooks(workflow_hooks, existing_hooks)

        assert len(hooks_added) == 1
        assert hooks_added[0]['hook_type'] == 'user_prompt_submit'
        assert hooks_added[0]['command'] == 'test.py'
        assert 'user_prompt_submit' in existing_hooks

    def test_merge_hooks_existing_hook_type(self, settings_service):
        """Test _merge_hooks with existing hook type."""
        workflow_hooks = {
            "user_prompt_submit": [
                {
                    "matcher": "**/*.py",
                    "hooks": [
                        {"type": "command", "command": "new.py"}
                    ]
                }
            ]
        }
        existing_hooks = {
            "user_prompt_submit": [
                {
                    "matcher": "**/*.py",
                    "hooks": [
                        {"type": "command", "command": "existing.py"}
                    ]
                }
            ]
        }

        hooks_added = settings_service._merge_hooks(workflow_hooks, existing_hooks)

        assert len(hooks_added) == 1
        assert hooks_added[0]['command'] == 'new.py'
        # Should have both hooks
        all_hooks = existing_hooks["user_prompt_submit"][0]["hooks"]
        assert len(all_hooks) == 2

    def test_merge_hooks_duplicate_command(self, settings_service):
        """Test _merge_hooks skips duplicate commands."""
        workflow_hooks = {
            "user_prompt_submit": [
                {
                    "matcher": "**/*.py",
                    "hooks": [
                        {"type": "command", "command": "test.py"}
                    ]
                }
            ]
        }
        existing_hooks = {
            "user_prompt_submit": [
                {
                    "matcher": "**/*.py",
                    "hooks": [
                        {"type": "command", "command": "test.py"}
                    ]
                }
            ]
        }

        hooks_added = settings_service._merge_hooks(workflow_hooks, existing_hooks)

        assert len(hooks_added) == 0
        # Should still have only one hook
        all_hooks = existing_hooks["user_prompt_submit"][0]["hooks"]
        assert len(all_hooks) == 1

    def test_merge_hooks_different_matcher(self, settings_service):
        """Test _merge_hooks with different matcher patterns."""
        workflow_hooks = {
            "user_prompt_submit": [
                {
                    "matcher": "**/*.ts",
                    "hooks": [
                        {"type": "command", "command": "ts-hook.py"}
                    ]
                }
            ]
        }
        existing_hooks = {
            "user_prompt_submit": [
                {
                    "matcher": "**/*.py",
                    "hooks": [
                        {"type": "command", "command": "py-hook.py"}
                    ]
                }
            ]
        }

        hooks_added = settings_service._merge_hooks(workflow_hooks, existing_hooks)

        assert len(hooks_added) == 1
        # Should have two matcher groups
        assert len(existing_hooks["user_prompt_submit"]) == 2

    def test_remove_hooks_from_settings_no_file(self, settings_service, temp_dir):
        """Test remove_hooks_from_settings when file doesn't exist."""
        hooks_to_remove = [{"command": "test.py"}]

        result = settings_service.remove_hooks_from_settings(hooks_to_remove, temp_dir)

        assert result is True

    def test_remove_hooks_from_settings_no_hooks_key(self, settings_service, temp_dir):
        """Test remove_hooks_from_settings when settings has no hooks."""
        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir()
        settings_file = claude_dir / "settings.json"
        settings_file.write_text('{"other_key": "value"}')

        hooks_to_remove = [{"command": "test.py"}]

        result = settings_service.remove_hooks_from_settings(hooks_to_remove, temp_dir)

        assert result is True

    def test_remove_hooks_from_settings_removes_hook(self, settings_service, temp_dir):
        """Test remove_hooks_from_settings removes specified hooks."""
        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir()

        settings = {
            "hooks": {
                "user_prompt_submit": [
                    {
                        "matcher": "**/*.py",
                        "hooks": [
                            {"type": "command", "command": "keep.py"},
                            {"type": "command", "command": "remove.py"}
                        ]
                    }
                ]
            }
        }
        settings_file = claude_dir / "settings.json"
        settings_file.write_text(json.dumps(settings))

        hooks_to_remove = [{"command": "remove.py"}]

        result = settings_service.remove_hooks_from_settings(hooks_to_remove, temp_dir)

        assert result is True

        # Verify hook was removed
        with open(settings_file, 'r') as f:
            updated_settings = json.load(f)

        hooks = updated_settings["hooks"]["user_prompt_submit"][0]["hooks"]
        assert len(hooks) == 1
        assert hooks[0]["command"] == "keep.py"

    def test_remove_hooks_from_settings_cleanup_empty_groups(self, settings_service, temp_dir):
        """Test remove_hooks_from_settings cleans up empty groups."""
        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir()

        settings = {
            "hooks": {
                "user_prompt_submit": [
                    {
                        "matcher": "**/*.py",
                        "hooks": [
                            {"type": "command", "command": "remove.py"}
                        ]
                    }
                ]
            }
        }
        settings_file = claude_dir / "settings.json"
        settings_file.write_text(json.dumps(settings))

        hooks_to_remove = [{"command": "remove.py"}]

        result = settings_service.remove_hooks_from_settings(hooks_to_remove, temp_dir)

        assert result is True

        # Verify empty hook type was removed
        with open(settings_file, 'r') as f:
            updated_settings = json.load(f)

        assert "user_prompt_submit" not in updated_settings["hooks"]

    def test_remove_hooks_from_settings_invalid_json(self, settings_service, temp_dir):
        """Test remove_hooks_from_settings with invalid JSON."""
        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir()
        settings_file = claude_dir / "settings.json"
        settings_file.write_text("invalid json {")

        hooks_to_remove = [{"command": "test.py"}]

        result = settings_service.remove_hooks_from_settings(hooks_to_remove, temp_dir)

        assert result is False
