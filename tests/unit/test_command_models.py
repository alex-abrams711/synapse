"""Unit tests for command models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from synapse.models.command import (
    AgentType,
    CommandInfo,
    CommandRegistry,
    ConflictInfo,
    ConflictResolution,
    ConflictType,
    SlashCommand,
)


class TestSlashCommand:
    """Test SlashCommand model."""

    def test_slash_command_creation(self) -> None:
        """Test basic SlashCommand creation."""
        command = SlashCommand(
            name="/synapse:plan",
            description="Planning command",
            agent_target=AgentType.DISPATCHER,
            command_template="# Planning Command\n\nInvoke DISPATCHER agent."
        )
        assert command.name == "/synapse:plan"
        assert command.description == "Planning command"
        assert command.agent_target == AgentType.DISPATCHER
        assert "Planning Command" in command.command_template
        assert command.is_synapse_managed is True

    def test_slash_command_defaults(self) -> None:
        """Test SlashCommand with default values."""
        command = SlashCommand(
            name="/test",
            description="Test command",
            agent_target=AgentType.DEV,
            command_template="Test template"
        )
        assert command.is_synapse_managed is True
        assert command.installation_date is None
        assert command.command_file_path is None

    def test_command_name_validation(self) -> None:
        """Test command name validation."""
        # Valid command names
        valid_names = [
            "/plan",
            "/synapse:implement",
            "/custom-command",
            "/test_command"
        ]
        for name in valid_names:
            command = SlashCommand(
                name=name,
                description="Test",
                agent_target=AgentType.DEV,
                command_template="Template"
            )
            assert command.name == name

        # Invalid command names
        invalid_names = [
            "plan",  # Missing slash
            "/invalid command",  # Space not allowed
            "/custom:command",  # Non-synapse prefix
        ]
        for name in invalid_names:
            with pytest.raises(ValidationError):
                SlashCommand(
                    name=name,
                    description="Test",
                    agent_target=AgentType.DEV,
                    command_template="Template"
                )

    def test_agent_target_validation(self) -> None:
        """Test agent target validation."""
        # Valid agent targets
        for agent_type in AgentType:
            command = SlashCommand(
                name="/test",
                description="Test",
                agent_target=agent_type,
                command_template="Template"
            )
            assert command.agent_target == agent_type

        # Test specific agent types
        command = SlashCommand(
            name="/dev-command",
            description="Dev command",
            agent_target=AgentType.DEV,
            command_template="Template"
        )
        assert command.agent_target == AgentType.DEV

    def test_command_template_validation(self) -> None:
        """Test command template validation."""
        # Valid template
        template = "# Test Command\n\nThis is a test command."
        command = SlashCommand(
            name="/test",
            description="Test",
            agent_target=AgentType.DEV,
            command_template=template
        )
        assert command.command_template == template

        # Empty template should be rejected
        with pytest.raises(ValidationError):
            SlashCommand(
                name="/test",
                description="Test",
                agent_target=AgentType.DEV,
                command_template=""
            )

        # Template without markdown heading should be rejected
        with pytest.raises(ValidationError):
            SlashCommand(
                name="/test",
                description="Test",
                agent_target=AgentType.DEV,
                command_template="No heading content"
            )


class TestCommandInfo:
    """Test CommandInfo model."""

    def test_command_info_creation(self) -> None:
        """Test basic CommandInfo creation."""
        info = CommandInfo(
            name="/test",
            file_path="/path/to/test.md",
            agent_target=AgentType.DEV,
            installation_date=datetime.now(),
            is_synapse_managed=True,
            last_modified=datetime.now()
        )
        assert info.name == "/test"
        assert info.file_path == "/path/to/test.md"
        assert info.agent_target == AgentType.DEV
        assert info.is_synapse_managed is True

    def test_command_info_defaults(self) -> None:
        """Test CommandInfo with default values."""
        info = CommandInfo(
            name="/test",
            file_path="/path/to/test.md",
            agent_target=AgentType.DEV
        )
        assert info.installation_date is None
        assert info.is_synapse_managed is False
        assert info.last_modified is None

    def test_command_name_validation(self) -> None:
        """Test command name validation in CommandInfo."""
        # Valid command name
        info = CommandInfo(
            name="/valid-command",
            file_path="/path/to/valid.md",
            agent_target=AgentType.DEV
        )
        assert info.name == "/valid-command"

        # Invalid command name
        with pytest.raises(ValidationError):
            CommandInfo(
                name="invalid",  # Missing slash
                file_path="/path/to/invalid.md",
                agent_target=AgentType.DEV
            )

    def test_file_path_validation(self) -> None:
        """Test file path validation."""
        # Valid file path
        info = CommandInfo(
            name="/test",
            file_path="/valid/path/to/command.md",
            agent_target=AgentType.DEV
        )
        assert info.file_path == "/valid/path/to/command.md"

        # Empty file path should be rejected
        with pytest.raises(ValidationError):
            CommandInfo(
                name="/test",
                file_path="",
                agent_target=AgentType.DEV
            )


class TestCommandRegistry:
    """Test CommandRegistry model."""

    def test_command_registry_creation(self) -> None:
        """Test basic CommandRegistry creation."""
        registry = CommandRegistry()
        assert len(registry.installed_commands) == 0
        assert len(registry.conflicts) == 0
        assert registry.last_scan_date is None
        assert len(registry.synapse_commands) == 0

    def test_add_command(self) -> None:
        """Test adding commands to registry."""
        registry = CommandRegistry()

        command_info = CommandInfo(
            name="/test",
            file_path="/path/to/test.md",
            agent_target=AgentType.DEV
        )

        registry.add_command(command_info)
        assert len(registry.installed_commands) == 1
        assert "/test" in registry.installed_commands
        assert registry.installed_commands["/test"] == command_info

    def test_get_command(self) -> None:
        """Test getting command from registry."""
        registry = CommandRegistry()

        command_info = CommandInfo(
            name="/test",
            file_path="/path/to/test.md",
            agent_target=AgentType.DEV
        )

        registry.add_command(command_info)

        # Test existing command
        retrieved = registry.get_command("/test")
        assert retrieved == command_info

        # Test non-existing command
        not_found = registry.get_command("/nonexistent")
        assert not_found is None

    def test_has_command(self) -> None:
        """Test checking if registry has command."""
        registry = CommandRegistry()

        command_info = CommandInfo(
            name="/test",
            file_path="/path/to/test.md",
            agent_target=AgentType.DEV
        )

        registry.add_command(command_info)

        assert registry.has_command("/test") is True
        assert registry.has_command("/nonexistent") is False

    def test_remove_command(self) -> None:
        """Test removing command from registry."""
        registry = CommandRegistry()

        command_info = CommandInfo(
            name="/test",
            file_path="/path/to/test.md",
            agent_target=AgentType.DEV
        )

        registry.add_command(command_info)
        assert registry.has_command("/test") is True

        # Remove existing command
        result = registry.remove_command("/test")
        assert result is True
        assert registry.has_command("/test") is False

        # Remove non-existing command
        result = registry.remove_command("/nonexistent")
        assert result is False

    def test_command_validation(self) -> None:
        """Test command validation in registry."""
        registry = CommandRegistry()

        # Valid commands should be accepted
        valid_commands = {
            "/synapse:plan": CommandInfo(
                name="/synapse:plan",
                file_path="/path/to/plan.md",
                agent_target=AgentType.DISPATCHER
            ),
            "/synapse:implement": CommandInfo(
                name="/synapse:implement",
                file_path="/path/to/implement.md",
                agent_target=AgentType.DEV
            )
        }

        registry.installed_commands = valid_commands

        # Should pass validation
        assert len(registry.installed_commands) == 2

        # Duplicate command names should be rejected
        with pytest.raises(ValidationError):
            CommandRegistry(
                installed_commands={
                    "/duplicate": CommandInfo(
                        name="/different",  # Name mismatch
                        file_path="/path1.md",
                        agent_target=AgentType.DEV
                    )
                }
            )


class TestConflictInfo:
    """Test ConflictInfo model."""

    def test_conflict_info_creation(self) -> None:
        """Test basic ConflictInfo creation."""
        synapse_command = SlashCommand(
            name="/synapse:plan",
            description="Planning command",
            agent_target=AgentType.DISPATCHER,
            command_template="# Planning"
        )

        conflict = ConflictInfo(
            command_name="/plan",
            existing_source="/path/to/existing.md",
            synapse_command=synapse_command,
            conflict_type=ConflictType.NAME_COLLISION,
            resolution=ConflictResolution.USE_PREFIX,
            detected_date=datetime.now()
        )

        assert conflict.command_name == "/plan"
        assert conflict.existing_source == "/path/to/existing.md"
        assert conflict.synapse_command == synapse_command
        assert conflict.conflict_type == ConflictType.NAME_COLLISION
        assert conflict.resolution == ConflictResolution.USE_PREFIX

    def test_conflict_types(self) -> None:
        """Test all conflict types are valid."""
        synapse_command = SlashCommand(
            name="/synapse:test",
            description="Test",
            agent_target=AgentType.DEV,
            command_template="# Test"
        )

        for conflict_type in ConflictType:
            conflict = ConflictInfo(
                command_name="/test",
                existing_source="/path/to/test.md",
                synapse_command=synapse_command,
                conflict_type=conflict_type,
                resolution=ConflictResolution.USE_PREFIX,
                detected_date=datetime.now()
            )
            assert conflict.conflict_type == conflict_type

    def test_conflict_resolutions(self) -> None:
        """Test all conflict resolutions are valid."""
        synapse_command = SlashCommand(
            name="/synapse:test",
            description="Test",
            agent_target=AgentType.DEV,
            command_template="# Test"
        )

        for resolution in ConflictResolution:
            conflict = ConflictInfo(
                command_name="/test",
                existing_source="/path/to/test.md",
                synapse_command=synapse_command,
                conflict_type=ConflictType.NAME_COLLISION,
                resolution=resolution,
                detected_date=datetime.now()
            )
            assert conflict.resolution == resolution

    def test_command_name_validation(self) -> None:
        """Test command name validation in ConflictInfo."""
        synapse_command = SlashCommand(
            name="/synapse:test",
            description="Test",
            agent_target=AgentType.DEV,
            command_template="# Test"
        )

        # Valid command name
        conflict = ConflictInfo(
            command_name="/valid",
            existing_source="/path/to/valid.md",
            synapse_command=synapse_command,
            conflict_type=ConflictType.NAME_COLLISION,
            resolution=ConflictResolution.USE_PREFIX,
            detected_date=datetime.now()
        )
        assert conflict.command_name == "/valid"

        # Invalid command name
        with pytest.raises(ValidationError):
            ConflictInfo(
                command_name="invalid",  # Missing slash
                existing_source="/path/to/invalid.md",
                synapse_command=synapse_command,
                conflict_type=ConflictType.NAME_COLLISION,
                resolution=ConflictResolution.USE_PREFIX,
                detected_date=datetime.now()
            )

    def test_existing_source_validation(self) -> None:
        """Test existing source validation."""
        synapse_command = SlashCommand(
            name="/synapse:test",
            description="Test",
            agent_target=AgentType.DEV,
            command_template="# Test"
        )

        # Valid source path
        conflict = ConflictInfo(
            command_name="/test",
            existing_source="/valid/path/to/source.md",
            synapse_command=synapse_command,
            conflict_type=ConflictType.NAME_COLLISION,
            resolution=ConflictResolution.USE_PREFIX,
            detected_date=datetime.now()
        )
        assert conflict.existing_source == "/valid/path/to/source.md"

        # Empty source should be rejected
        with pytest.raises(ValidationError):
            ConflictInfo(
                command_name="/test",
                existing_source="",
                synapse_command=synapse_command,
                conflict_type=ConflictType.NAME_COLLISION,
                resolution=ConflictResolution.USE_PREFIX,
                detected_date=datetime.now()
            )


class TestModelIntegration:
    """Test integration between command models."""

    def test_registry_with_conflicts(self) -> None:
        """Test CommandRegistry with ConflictInfo integration."""
        registry = CommandRegistry()

        synapse_command = SlashCommand(
            name="/synapse:plan",
            description="Planning command",
            agent_target=AgentType.DISPATCHER,
            command_template="# Planning"
        )

        conflict = ConflictInfo(
            command_name="/plan",
            existing_source="/path/to/existing.md",
            synapse_command=synapse_command,
            conflict_type=ConflictType.NAME_COLLISION,
            resolution=ConflictResolution.USE_PREFIX,
            detected_date=datetime.now()
        )

        registry.conflicts.append(conflict)

        assert len(registry.conflicts) == 1
        assert registry.conflicts[0].command_name == "/plan"
        assert registry.conflicts[0].conflict_type == ConflictType.NAME_COLLISION

    def test_command_registry_synapse_commands(self) -> None:
        """Test CommandRegistry synapse command tracking."""
        registry = CommandRegistry()

        # Add synapse-managed commands
        synapse_commands = ["/synapse:plan", "/synapse:implement", "/synapse:review"]
        registry.synapse_commands.extend(synapse_commands)

        assert len(registry.synapse_commands) == 3
        assert "/synapse:plan" in registry.synapse_commands
        assert "/synapse:implement" in registry.synapse_commands
        assert "/synapse:review" in registry.synapse_commands
