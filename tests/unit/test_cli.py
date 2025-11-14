"""Unit tests for CLI module."""

import pytest
import argparse
from pathlib import Path
from unittest.mock import Mock, patch
from io import StringIO

from synapse_cli.cli import create_parser, dispatch_command, main


class TestCreateParser:
    """Tests for create_parser function."""

    def test_create_parser_structure(self):
        """Test that parser is created with correct structure."""
        parser = create_parser()

        assert parser.description == "Synapse - AI-first workflow system with quality gates"
        assert parser.epilog is not None
        assert "synapse init" in parser.epilog

    def test_parser_init_command(self):
        """Test init command parsing."""
        parser = create_parser()
        args = parser.parse_args(['init'])

        assert args.command == 'init'
        assert args.directory is None

    def test_parser_init_command_with_directory(self, tmp_path):
        """Test init command parsing with directory."""
        parser = create_parser()
        args = parser.parse_args(['init', str(tmp_path)])

        assert args.command == 'init'
        assert args.directory == tmp_path

    def test_parser_workflow_list(self):
        """Test workflow list command parsing."""
        parser = create_parser()
        args = parser.parse_args(['workflow', 'list'])

        assert args.command == 'workflow'
        assert args.workflow_name_or_command == 'list'
        assert args.force is False

    def test_parser_workflow_status(self):
        """Test workflow status command parsing."""
        parser = create_parser()
        args = parser.parse_args(['workflow', 'status'])

        assert args.command == 'workflow'
        assert args.workflow_name_or_command == 'status'

    def test_parser_workflow_remove(self):
        """Test workflow remove command parsing."""
        parser = create_parser()
        args = parser.parse_args(['workflow', 'remove'])

        assert args.command == 'workflow'
        assert args.workflow_name_or_command == 'remove'

    def test_parser_workflow_apply(self):
        """Test workflow apply command parsing."""
        parser = create_parser()
        args = parser.parse_args(['workflow', 'feature-planning'])

        assert args.command == 'workflow'
        assert args.workflow_name_or_command == 'feature-planning'
        assert args.force is False

    def test_parser_workflow_apply_with_force(self):
        """Test workflow apply command parsing with --force."""
        parser = create_parser()
        args = parser.parse_args(['workflow', 'feature-planning', '--force'])

        assert args.command == 'workflow'
        assert args.workflow_name_or_command == 'feature-planning'
        assert args.force is True

    def test_parser_no_command(self):
        """Test parser with no command."""
        parser = create_parser()
        args = parser.parse_args([])

        assert args.command is None


class TestDispatchCommand:
    """Tests for dispatch_command function."""

    @pytest.fixture
    def mock_init_command(self):
        """Create a mock InitCommand."""
        mock = Mock()
        mock.execute = Mock()
        return mock

    @pytest.fixture
    def mock_workflow_command(self):
        """Create a mock WorkflowCommand."""
        mock = Mock()
        mock.list = Mock()
        mock.status = Mock()
        mock.apply = Mock(return_value=True)
        mock.remove = Mock(return_value=True)
        return mock

    def test_dispatch_init_command(self, mock_init_command, tmp_path):
        """Test dispatching init command."""
        args = argparse.Namespace(command='init', directory=tmp_path)

        with patch('synapse_cli.cli.get_init_command', return_value=mock_init_command):
            exit_code = dispatch_command(args)

        assert exit_code == 0
        mock_init_command.execute.assert_called_once_with(tmp_path)

    def test_dispatch_init_command_no_directory(self, mock_init_command):
        """Test dispatching init command without directory."""
        args = argparse.Namespace(command='init', directory=None)

        with patch('synapse_cli.cli.get_init_command', return_value=mock_init_command):
            exit_code = dispatch_command(args)

        assert exit_code == 0
        mock_init_command.execute.assert_called_once_with(None)

    def test_dispatch_workflow_list(self, mock_workflow_command):
        """Test dispatching workflow list command."""
        args = argparse.Namespace(
            command='workflow',
            workflow_name_or_command='list',
            force=False
        )

        with patch('synapse_cli.cli.get_workflow_command', return_value=mock_workflow_command):
            exit_code = dispatch_command(args)

        assert exit_code == 0
        mock_workflow_command.list.assert_called_once()

    def test_dispatch_workflow_status(self, mock_workflow_command):
        """Test dispatching workflow status command."""
        args = argparse.Namespace(
            command='workflow',
            workflow_name_or_command='status',
            force=False
        )

        with patch('synapse_cli.cli.get_workflow_command', return_value=mock_workflow_command):
            exit_code = dispatch_command(args)

        assert exit_code == 0
        mock_workflow_command.status.assert_called_once()

    def test_dispatch_workflow_remove_success(self, mock_workflow_command):
        """Test dispatching workflow remove command (success)."""
        args = argparse.Namespace(
            command='workflow',
            workflow_name_or_command='remove',
            force=False
        )

        mock_workflow_command.remove.return_value = True

        with patch('synapse_cli.cli.get_workflow_command', return_value=mock_workflow_command):
            exit_code = dispatch_command(args)

        assert exit_code == 0
        mock_workflow_command.remove.assert_called_once()

    def test_dispatch_workflow_remove_failure(self, mock_workflow_command):
        """Test dispatching workflow remove command (failure)."""
        args = argparse.Namespace(
            command='workflow',
            workflow_name_or_command='remove',
            force=False
        )

        mock_workflow_command.remove.return_value = False

        with patch('synapse_cli.cli.get_workflow_command', return_value=mock_workflow_command):
            exit_code = dispatch_command(args)

        assert exit_code == 1

    def test_dispatch_workflow_apply_success(self, mock_workflow_command):
        """Test dispatching workflow apply command (success)."""
        args = argparse.Namespace(
            command='workflow',
            workflow_name_or_command='feature-planning',
            force=False
        )

        mock_workflow_command.apply.return_value = True

        with patch('synapse_cli.cli.get_workflow_command', return_value=mock_workflow_command):
            exit_code = dispatch_command(args)

        assert exit_code == 0
        mock_workflow_command.apply.assert_called_once_with('feature-planning', force=False)

    def test_dispatch_workflow_apply_with_force(self, mock_workflow_command):
        """Test dispatching workflow apply command with --force."""
        args = argparse.Namespace(
            command='workflow',
            workflow_name_or_command='feature-planning',
            force=True
        )

        mock_workflow_command.apply.return_value = True

        with patch('synapse_cli.cli.get_workflow_command', return_value=mock_workflow_command):
            exit_code = dispatch_command(args)

        assert exit_code == 0
        mock_workflow_command.apply.assert_called_once_with('feature-planning', force=True)

    def test_dispatch_workflow_apply_failure(self, mock_workflow_command):
        """Test dispatching workflow apply command (failure)."""
        args = argparse.Namespace(
            command='workflow',
            workflow_name_or_command='feature-planning',
            force=False
        )

        mock_workflow_command.apply.return_value = False

        with patch('synapse_cli.cli.get_workflow_command', return_value=mock_workflow_command):
            exit_code = dispatch_command(args)

        assert exit_code == 1

    def test_dispatch_no_command(self):
        """Test dispatching with no command."""
        args = argparse.Namespace(command=None)

        exit_code = dispatch_command(args)

        assert exit_code == 1


class TestMain:
    """Tests for main function."""

    def test_main_no_args(self, capsys):
        """Test main with no arguments."""
        exit_code = main([])

        assert exit_code == 1

        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower() or "usage:" in captured.err.lower()

    def test_main_init_command(self):
        """Test main with init command."""
        mock_init_cmd = Mock()
        mock_init_cmd.execute = Mock()

        with patch('synapse_cli.cli.get_init_command', return_value=mock_init_cmd):
            exit_code = main(['init'])

        assert exit_code == 0

    def test_main_workflow_list(self):
        """Test main with workflow list command."""
        mock_workflow_cmd = Mock()
        mock_workflow_cmd.list = Mock()

        with patch('synapse_cli.cli.get_workflow_command', return_value=mock_workflow_cmd):
            exit_code = main(['workflow', 'list'])

        assert exit_code == 0

    def test_main_system_exit_from_command(self):
        """Test main when command raises SystemExit."""
        mock_init_cmd = Mock()
        mock_init_cmd.execute = Mock(side_effect=SystemExit(42))

        with patch('synapse_cli.cli.get_init_command', return_value=mock_init_cmd):
            exit_code = main(['init'])

        assert exit_code == 42

    def test_main_system_exit_none_code(self):
        """Test main when command raises SystemExit with None code."""
        mock_init_cmd = Mock()
        mock_init_cmd.execute = Mock(side_effect=SystemExit(None))

        with patch('synapse_cli.cli.get_init_command', return_value=mock_init_cmd):
            exit_code = main(['init'])

        assert exit_code == 1

    def test_main_keyboard_interrupt(self, capsys):
        """Test main when KeyboardInterrupt is raised."""
        mock_init_cmd = Mock()
        mock_init_cmd.execute = Mock(side_effect=KeyboardInterrupt())

        with patch('synapse_cli.cli.get_init_command', return_value=mock_init_cmd):
            exit_code = main(['init'])

        assert exit_code == 130

        captured = capsys.readouterr()
        assert "cancelled" in captured.err.lower()

    def test_main_exception(self, capsys):
        """Test main when exception is raised."""
        mock_init_cmd = Mock()
        mock_init_cmd.execute = Mock(side_effect=RuntimeError("Test error"))

        with patch('synapse_cli.cli.get_init_command', return_value=mock_init_cmd):
            exit_code = main(['init'])

        assert exit_code == 1

        captured = capsys.readouterr()
        assert "Error:" in captured.err
        assert "Test error" in captured.err
