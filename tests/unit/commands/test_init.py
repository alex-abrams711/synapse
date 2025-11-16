"""Unit tests for InitCommand."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open
from datetime import datetime

from synapse_cli.commands.init import InitCommand


class TestInitCommand:
    """Tests for InitCommand class."""

    @pytest.fixture
    def mock_resource_manager(self):
        """Create a mock ResourceManager."""
        mock = Mock()
        mock.resources_dir = Path("/fake/resources")
        return mock

    @pytest.fixture
    def mock_config_store(self):
        """Create a mock ConfigStore."""
        return Mock()

    @pytest.fixture
    def init_command(self, mock_resource_manager, mock_config_store):
        """Create an InitCommand instance with mocked dependencies."""
        return InitCommand(
            synapse_version="0.1.0",
            resource_manager=mock_resource_manager,
            config_store=mock_config_store
        )

    def test_execute_success(self, init_command, tmp_path, mock_resource_manager, capsys):
        """Test successful initialization."""
        target_dir = tmp_path / "test_project"
        target_dir.mkdir()

        # Mock the template file
        template_content = {
            "synapse_version": "",
            "initialized_at": "",
            "project": {
                "name": "",
                "root_directory": ""
            },
            "agent": {
                "type": "",
                "description": ""
            },
            "workflows": {}
        }

        # Store original exists method
        original_exists = Path.exists

        def mock_exists(self):
            # Return True only for the template path, otherwise use original
            if str(self).endswith("config-template.json"):
                return True
            return original_exists(self)

        with patch('builtins.input', return_value="1"), \
             patch('builtins.open', mock_open(read_data=json.dumps(template_content))), \
             patch.object(Path, 'exists', mock_exists):

            init_command.execute(target_dir)

        # Verify .synapse directory was created
        assert (target_dir / ".synapse").exists()

        # Verify output
        captured = capsys.readouterr()
        assert "Initializing synapse" in captured.out
        assert "Synapse initialized successfully!" in captured.out

    def test_execute_already_initialized(self, init_command, tmp_path):
        """Test initialization when .synapse already exists."""
        target_dir = tmp_path / "test_project"
        target_dir.mkdir()
        synapse_dir = target_dir / ".synapse"
        synapse_dir.mkdir()

        with pytest.raises(SystemExit) as exc_info:
            init_command.execute(target_dir)

        assert exc_info.value.code == 1

    def test_execute_defaults_to_cwd(self, init_command, tmp_path, monkeypatch):
        """Test that execute defaults to current working directory."""
        # Change to tmp_path
        monkeypatch.chdir(tmp_path)

        with patch.object(init_command, '_prompt_agent_selection', return_value={'type': 'claude-code', 'description': 'test'}), \
             patch.object(init_command, '_create_config', return_value=True):
            init_command.execute()

        assert (tmp_path / ".synapse").exists()

    def test_prompt_agent_selection_claude_code(self, init_command):
        """Test agent selection - Claude Code."""
        with patch('builtins.input', return_value="1"):
            result = init_command._prompt_agent_selection()

        assert result['type'] == 'claude-code'
        assert 'Claude Code' in result['description']

    def test_prompt_agent_selection_none(self, init_command):
        """Test agent selection - None (should exit)."""
        with patch('builtins.input', return_value="2"):
            with pytest.raises(SystemExit) as exc_info:
                init_command._prompt_agent_selection()

        assert exc_info.value.code == 1

    def test_prompt_agent_selection_invalid_then_valid(self, init_command, capsys):
        """Test agent selection with invalid input then valid."""
        with patch('builtins.input', side_effect=["invalid", "3", "1"]):
            result = init_command._prompt_agent_selection()

        assert result['type'] == 'claude-code'

        # Verify invalid input messages were shown
        captured = capsys.readouterr()
        assert "Invalid choice" in captured.err

    def test_prompt_agent_selection_eof(self, init_command):
        """Test agent selection with EOF (Ctrl+D)."""
        with patch('builtins.input', side_effect=EOFError()):
            with pytest.raises(SystemExit) as exc_info:
                init_command._prompt_agent_selection()

        assert exc_info.value.code == 1

    def test_prompt_agent_selection_keyboard_interrupt(self, init_command):
        """Test agent selection with KeyboardInterrupt (Ctrl+C)."""
        with patch('builtins.input', side_effect=KeyboardInterrupt()):
            with pytest.raises(SystemExit) as exc_info:
                init_command._prompt_agent_selection()

        assert exc_info.value.code == 1

    def test_create_config_success(self, init_command, tmp_path, mock_resource_manager):
        """Test successful config creation."""
        target_dir = tmp_path / "test_project"
        synapse_dir = target_dir / ".synapse"
        synapse_dir.mkdir(parents=True)

        agent_info = {
            "type": "claude-code",
            "description": "Test agent"
        }

        template_content = {
            "synapse_version": "",
            "initialized_at": "",
            "project": {
                "name": "",
                "root_directory": ""
            },
            "agent": {
                "type": "",
                "description": ""
            },
            "workflows": {}
        }

        template_path = mock_resource_manager.resources_dir / "settings" / "config-template.json"

        # Mock file operations
        with patch.object(Path, 'exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(template_content))) as mock_file:

            result = init_command._create_config(target_dir, agent_info)

        assert result is True

        # Verify write was called
        assert mock_file.called

    def test_create_config_template_not_found(self, init_command, tmp_path, mock_resource_manager, capsys):
        """Test config creation when template doesn't exist."""
        target_dir = tmp_path / "test_project"
        synapse_dir = target_dir / ".synapse"
        synapse_dir.mkdir(parents=True)

        agent_info = {"type": "claude-code", "description": "Test"}

        with patch.object(Path, 'exists', return_value=False):
            result = init_command._create_config(target_dir, agent_info)

        assert result is False

        captured = capsys.readouterr()
        assert "Warning: Baseline config template not found" in captured.err

    def test_create_config_json_decode_error(self, init_command, tmp_path, mock_resource_manager, capsys):
        """Test config creation with invalid JSON in template."""
        target_dir = tmp_path / "test_project"
        synapse_dir = target_dir / ".synapse"
        synapse_dir.mkdir(parents=True)

        agent_info = {"type": "claude-code", "description": "Test"}

        with patch.object(Path, 'exists', return_value=True), \
             patch('builtins.open', mock_open(read_data="invalid json")):

            result = init_command._create_config(target_dir, agent_info)

        assert result is False

        captured = capsys.readouterr()
        assert "Could not create config.json" in captured.err

    def test_create_config_io_error(self, init_command, tmp_path, mock_resource_manager, capsys):
        """Test config creation with IO error."""
        target_dir = tmp_path / "test_project"
        synapse_dir = target_dir / ".synapse"
        synapse_dir.mkdir(parents=True)

        agent_info = {"type": "claude-code", "description": "Test"}

        with patch.object(Path, 'exists', return_value=True), \
             patch('builtins.open', side_effect=IOError("Permission denied")):

            result = init_command._create_config(target_dir, agent_info)

        assert result is False

        captured = capsys.readouterr()
        assert "Could not create config.json" in captured.err

    def test_execute_config_creation_failure(self, init_command, tmp_path):
        """Test that execute exits when config creation fails."""
        target_dir = tmp_path / "test_project"
        target_dir.mkdir()

        with patch.object(init_command, '_prompt_agent_selection', return_value={'type': 'claude-code', 'description': 'test'}), \
             patch.object(init_command, '_create_config', return_value=False):

            with pytest.raises(SystemExit) as exc_info:
                init_command.execute(target_dir)

            assert exc_info.value.code == 1
