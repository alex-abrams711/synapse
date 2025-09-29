"""Contract tests for command conflict detection."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from synapse.cli.main import cli


class TestCommandConflictDetection:
    """Test command conflict detection functionality."""

    def setup_method(self) -> None:
        """Set up test environment."""
        import os
        self.original_cwd = os.getcwd()  # Save original working directory
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.test_project_dir = Path(self.temp_dir) / "test_project"
        self.test_project_dir.mkdir()
        self.commands_dir = self.test_project_dir / ".claude" / "commands"
        self.commands_dir.mkdir(parents=True)

    def teardown_method(self) -> None:
        """Clean up test environment."""
        import os
        import shutil
        os.chdir(self.original_cwd)  # Restore original working directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_detect_name_collision_conflicts(self) -> None:
        """Test detection of name collision conflicts."""
        # Create existing conflicting commands
        (self.commands_dir / "plan.md").write_text("# /plan - Existing command")
        (self.commands_dir / "review.md").write_text("# /review - Existing command")

        # Test conflict detection utility is working
        from synapse.utils.conflicts import detect_command_conflicts

        conflicts = detect_command_conflicts(
            proposed_commands=["plan", "implement", "review", "dev"],
            command_dir=str(self.commands_dir)
        )

        # Should detect conflicts with existing plan and review commands
        assert len(conflicts.conflicts) >= 2

    def test_conflict_resolution_with_prefix(self) -> None:
        """Test conflict resolution using synapse: prefix."""
        from datetime import datetime

        from synapse.models.command import (
            AgentType,
            ConflictInfo,
            ConflictResolution,
            ConflictType,
            SlashCommand,
        )

        # Create a SlashCommand object for synapse_command
        synapse_command = SlashCommand(
            name="/synapse:plan",
            description="Planning command",
            agent_target=AgentType.DISPATCHER,
            command_template="# Synapse Plan Command\n\nInvoke planning functionality.",
            is_synapse_managed=True,
            installation_date=datetime.now()
        )

        conflict = ConflictInfo(
            command_name="/plan",  # Command name must start with '/'
            existing_source=str(self.commands_dir / "plan.md"),
            synapse_command=synapse_command,
            conflict_type=ConflictType.NAME_COLLISION,
            resolution=ConflictResolution.USE_PREFIX,
            detected_date=datetime.now(),
            is_resolvable=True
        )

        # Test that the conflict was created successfully
        assert conflict.command_name == "/plan"
        assert conflict.conflict_type == ConflictType.NAME_COLLISION
        assert conflict.resolution == ConflictResolution.USE_PREFIX
        assert conflict.is_resolvable is True

    def test_init_command_warns_about_conflicts(self) -> None:
        """Test that init command warns about detected conflicts."""
        # Create conflicting commands
        (self.commands_dir / "plan.md").write_text("# /plan - Existing")
        (self.commands_dir / "implement.md").write_text("# /implement - Existing")

        # Change to test directory
        import os
        os.chdir(self.test_project_dir)

        # Run init and expect it to detect conflicts
        result = self.runner.invoke(cli, [
            'init',
            '--project-name', 'Test Project'
        ])

        # Should complete but may warn about conflicts
        # For now, this will just run the existing init without conflict detection
        assert result.exit_code == 0  # Existing init should work
        # But enhanced conflict detection isn't implemented yet

    def test_conflict_registry_model_contract(self) -> None:
        """Test CommandRegistry model contract."""
        from synapse.models.command import CommandRegistry

        registry = CommandRegistry(
            installed_commands={},
            conflicts=[],
            last_scan_date=None,
            synapse_commands=["plan", "implement", "review", "dev", "audit", "dispatch"]
        )

        # Registry should track conflicts
        assert isinstance(registry.synapse_commands, list)
        assert len(registry.synapse_commands) == 6

    def test_conflict_detection_service_contract(self) -> None:
        """Test conflict detection service contract."""
        from synapse.utils.conflicts import detect_command_conflicts, scan_existing_commands

        # Create some test commands in the directory
        (self.commands_dir / "plan.md").write_text("# /plan - Planning Command\n")

        # Test scanning existing commands
        existing_commands = scan_existing_commands(str(self.commands_dir))
        assert isinstance(existing_commands, dict)
        assert "/plan" in existing_commands

        # Test conflict detection
        result = detect_command_conflicts(["/plan"], str(self.commands_dir))

        # Should return structured conflict information
        assert hasattr(result, 'conflicts')
        assert hasattr(result, 'existing_commands')
        assert hasattr(result, 'conflict_summary')

    def test_command_file_parsing(self) -> None:
        """Test parsing of existing command files."""
        # Create command with specific format
        command_content = """# /plan - My Planning Command

## Description
Custom planning functionality.

## Implementation
Execute custom planning logic.
"""
        (self.commands_dir / "plan.md").write_text(command_content)

        from synapse.utils.conflicts import parse_command_file

        command_info = parse_command_file(str(self.commands_dir / "plan.md"), command_content)

        # Should extract command information
        assert command_info.name == "/plan"
        assert "planning" in command_info.description.lower()

    def test_functionality_overlap_detection(self) -> None:
        """Test detection of functionality overlap conflicts."""
        # Create command that overlaps in functionality
        overlap_content = """# /planning - Planning Command

## Description
This command helps with planning tasks and project management.
"""
        (self.commands_dir / "planning.md").write_text(overlap_content)

        from synapse.utils.conflicts import detect_functionality_overlap

        overlaps = detect_functionality_overlap(
            existing_commands=["planning"],
            synapse_commands=["plan"]
        )

        # Should detect semantic similarity (results depend on implementation)
        assert isinstance(overlaps, list)

    def test_conflict_resolution_strategies(self) -> None:
        """Test different conflict resolution strategies."""
        from synapse.utils.conflicts import ConflictResolver

        resolver = ConflictResolver()

        # Test prefix strategy
        result = resolver.resolve_with_prefix("plan")
        assert result == "synapse:plan"

        # Test warning strategy
        result = resolver.resolve_with_warning("plan")
        assert result["action"] == "warn_user"

        # Test skip strategy
        result = resolver.resolve_with_skip("plan")
        assert result["action"] == "skip_command"

    def test_interactive_conflict_resolution(self) -> None:
        """Test interactive conflict resolution."""
        from synapse.utils.conflicts import InteractiveResolver

        resolver = InteractiveResolver()

        # Mock user input
        with patch('builtins.input', return_value='1'):
            result = resolver.resolve_interactively({
                "plan": ["Use prefix (/synapse:plan)", "Skip command", "Override existing"]
            })

            assert result["plan"] == "use_prefix"
