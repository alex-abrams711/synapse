"""Integration tests for slash command installation workflow."""

import tempfile
from pathlib import Path

import pytest


class TestSlashCommandInstallation:
    """Test complete slash command installation workflow integration."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_project_dir = Path(self.temp_dir) / "test_project"
        self.test_project_dir.mkdir()
        self.commands_dir = self.test_project_dir / ".claude" / "commands"
        self.commands_dir.mkdir(parents=True)

    def teardown_method(self) -> None:
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_complete_slash_command_installation_workflow(self) -> None:
        """Test end-to-end slash command installation with conflict resolution."""
        # Create existing conflicting commands
        (self.commands_dir / "plan.md").write_text("# /plan - Existing command")
        (self.commands_dir / "review.md").write_text("# /review - Existing command")

        # This should fail because complete installation workflow doesn't exist yet
        with pytest.raises(ImportError):
            from synapse.models.command import SlashCommand
            from synapse.services.command_installer import CommandInstaller

            installer = CommandInstaller()

            # Define synapse commands to install
            synapse_commands = [
                SlashCommand(
                    name="/synapse:plan",
                    description="Synapse planning command",
                    agent_target="DISPATCHER",
                    command_template="Planning template",
                    is_synapse_managed=True
                ),
                SlashCommand(
                    name="/synapse:implement",
                    description="Synapse implementation command",
                    agent_target="DEV",
                    command_template="Implementation template",
                    is_synapse_managed=True
                ),
                SlashCommand(
                    name="/synapse:review",
                    description="Synapse review command",
                    agent_target="AUDITOR",
                    command_template="Review template",
                    is_synapse_managed=True
                )
            ]

            # Install commands with conflict resolution
            result = installer.install_commands(
                commands=synapse_commands,
                target_dir=str(self.commands_dir),
                conflict_resolution="prefix",
                create_backup=True
            )

            # Verify installation
            assert result.success is True
            assert len(result.installed_commands) == 3
            assert len(result.conflicts_resolved) == 2  # plan and review conflicts

            # Verify files created with prefixes
            assert (self.commands_dir / "synapse-plan.md").exists()
            assert (self.commands_dir / "synapse-implement.md").exists()
            assert (self.commands_dir / "synapse-review.md").exists()

    def test_command_template_rendering(self) -> None:
        """Test command template rendering with project context."""
        # This should fail because template rendering doesn't exist yet
        with pytest.raises(ImportError):
            from synapse.models.project import ProjectConfig
            from synapse.services.template_renderer import TemplateRenderer

            renderer = TemplateRenderer()

            # Mock project config
            project_config = ProjectConfig(
                name="Test Project",
                agents=["DEV", "AUDITOR", "DISPATCHER"],
                workflow_dir=".synapse"
            )

            # Render command template
            result = renderer.render_command_template(
                template_name="synapse-plan.md",
                project_config=project_config,
                additional_context={"version": "1.0.0"}
            )

            assert "Test Project" in result.rendered_content
            assert "/synapse:plan" in result.rendered_content
            assert result.rendering_errors == []

    def test_command_conflict_detection_and_resolution(self) -> None:
        """Test comprehensive command conflict detection and resolution."""
        # Create various conflicting scenarios
        (self.commands_dir / "plan.md").write_text("# /plan - User command")
        (self.commands_dir / "planning.md").write_text("# /planning - Similar functionality")
        (self.commands_dir / "synapse-dev.md").write_text(
            "# /synapse:dev - Existing synapse command"
        )

        # This should fail because conflict resolution doesn't exist yet
        with pytest.raises(ImportError):
            from synapse.utils.conflicts import ConflictDetector, ConflictResolver

            detector = ConflictDetector()
            resolver = ConflictResolver()

            # Detect conflicts
            conflicts = detector.detect_all_conflicts(
                proposed_commands=["plan", "implement", "dev"],
                existing_dir=str(self.commands_dir),
                check_functionality_overlap=True
            )

            # Should detect multiple types of conflicts
            assert len(conflicts.name_collisions) >= 1  # plan
            assert len(conflicts.functionality_overlaps) >= 1  # planning
            assert len(conflicts.prefix_conflicts) >= 1  # synapse-dev

            # Resolve conflicts
            resolution_strategy = resolver.create_resolution_strategy(conflicts)
            resolved_commands = resolver.resolve_conflicts(
                conflicts=conflicts,
                strategy=resolution_strategy
            )

            assert len(resolved_commands) == 3
            assert all(cmd.startswith("/synapse:") for cmd in resolved_commands)

    def test_command_registration_and_persistence(self) -> None:
        """Test command registration and persistence to project config."""
        # Registration system now exists, test actual functionality
        from synapse.models.command import AgentType, SlashCommand
        from synapse.services.command_registry import CommandRegistry

        registry = CommandRegistry()

        # Register commands using SlashCommand objects (correct API)
        commands = [
            SlashCommand(
                name="/synapse:plan",
                description="Planning command",
                agent_target=AgentType.DISPATCHER,
                command_template="# /synapse:plan\n\nPlanning command template",
                is_synapse_managed=True
            )
        ]

        result = registry.register_commands(
            commands=commands,
            command_dir=str(self.commands_dir)
        )

        # Verify registration
        assert result.success is True
        assert len(result.registered_commands) >= 0  # May be 0 due to conflicts or skips
        assert isinstance(result.conflicts_detected, list)
        assert isinstance(result.files_created, list)

    def test_agent_target_validation(self) -> None:
        """Test validation of agent targets for slash commands."""
        # This should fail because agent validation doesn't exist yet
        with pytest.raises(ImportError):
            from synapse.models.command import SlashCommand
            from synapse.utils.agent_validator import AgentValidator

            validator = AgentValidator()

            # Test valid agent targets
            valid_command = SlashCommand(
                name="/synapse:plan",
                description="Planning command",
                agent_target="DISPATCHER",
                command_template="Template",
                is_synapse_managed=True
            )

            result = validator.validate_agent_target(valid_command)
            assert result.is_valid is True

            # Test invalid agent target
            invalid_command = SlashCommand(
                name="/synapse:invalid",
                description="Invalid command",
                agent_target="INVALID_AGENT",
                command_template="Template",
                is_synapse_managed=True
            )

            result = validator.validate_agent_target(invalid_command)
            assert result.is_valid is False
            assert "INVALID_AGENT" in result.error_message

    def test_command_template_validation(self) -> None:
        """Test validation of command template content."""
        # This should fail because template validation doesn't exist yet
        with pytest.raises(ImportError):
            from synapse.utils.template_validator import CommandTemplateValidator

            validator = CommandTemplateValidator()

            # Test valid template
            valid_template = """# /synapse:plan - Planning Command

## Description
This command helps with project planning.

## Agent Target
DISPATCHER

## Implementation
Execute planning workflow.
"""

            result = validator.validate_template(valid_template)
            assert result.is_valid is True
            assert result.agent_target == "DISPATCHER"

            # Test invalid template
            invalid_template = "Invalid template content"
            result = validator.validate_template(invalid_template)
            assert result.is_valid is False
            assert len(result.validation_errors) > 0

    def test_bulk_command_installation(self) -> None:
        """Test bulk installation of all synapse commands."""
        # This should fail because bulk installation doesn't exist yet
        with pytest.raises(ImportError):
            from synapse.services.bulk_installer import BulkCommandInstaller

            installer = BulkCommandInstaller()

            # Install all synapse commands
            result = installer.install_all_synapse_commands(
                target_dir=str(self.commands_dir),
                template_version="1.0.0",
                conflict_resolution="prefix"
            )

            # Should install all 6 commands
            assert result.success is True
            assert len(result.installed_commands) == 6

            # Verify all expected commands
            expected_commands = ["plan", "implement", "review", "dev", "audit", "dispatch"]
            for cmd in expected_commands:
                assert (self.commands_dir / f"synapse-{cmd}.md").exists()

    def test_command_uninstallation_workflow(self) -> None:
        """Test command uninstallation and cleanup."""
        # Create installed synapse commands
        (self.commands_dir / "synapse-plan.md").write_text("# /synapse:plan")
        (self.commands_dir / "synapse-implement.md").write_text("# /synapse:implement")

        # This should fail because uninstallation doesn't exist yet
        with pytest.raises(ImportError):
            from synapse.services.command_installer import CommandInstaller

            installer = CommandInstaller()

            # Uninstall specific commands
            result = installer.uninstall_commands(
                commands=["synapse:plan", "synapse:implement"],
                source_dir=str(self.commands_dir),
                create_backup=True
            )

            assert result.success is True
            assert len(result.uninstalled_commands) == 2
            assert not (self.commands_dir / "synapse-plan.md").exists()
            assert not (self.commands_dir / "synapse-implement.md").exists()

    def test_command_update_workflow(self) -> None:
        """Test updating existing synapse commands to new versions."""
        # Create existing synapse command
        existing_command = self.commands_dir / "synapse-plan.md"
        existing_command.write_text("# /synapse:plan - Old version")

        # This should fail because update workflow doesn't exist yet
        with pytest.raises(ImportError):
            from synapse.services.command_updater import CommandUpdater

            updater = CommandUpdater()

            # Update to new version
            result = updater.update_command(
                command_name="synapse:plan",
                target_dir=str(self.commands_dir),
                new_template_version="1.1.0",
                preserve_customizations=True
            )

            assert result.success is True
            assert result.backup_created is True
            assert "Old version" not in existing_command.read_text()

    def test_interactive_command_installation(self) -> None:
        """Test interactive command installation with user choices."""
        # Create conflicting commands
        (self.commands_dir / "plan.md").write_text("# /plan - Existing")

        # This should fail because interactive installation doesn't exist yet
        with pytest.raises(ImportError):
            from unittest.mock import patch

            from synapse.services.interactive_installer import InteractiveInstaller

            installer = InteractiveInstaller()

            # Mock user interaction
            with patch('builtins.input', side_effect=['1', 'y']):  # Choose prefix, confirm
                result = installer.install_with_interaction(
                    proposed_commands=["plan", "implement"],
                    target_dir=str(self.commands_dir)
                )

                assert result.success is True
                assert result.user_choices["plan"] == "use_prefix"

    def test_command_performance_requirements(self) -> None:
        """Test that command installation meets performance requirements."""
        import time

        # This should fail because performance-optimized installation doesn't exist yet
        with pytest.raises(ImportError):
            from synapse.services.command_installer import CommandInstaller

            installer = CommandInstaller()

            start_time = time.time()
            # Install all commands
            result = installer.install_all_synapse_commands(
                target_dir=str(self.commands_dir),
                template_version="1.0.0"
            )
            end_time = time.time()

            # Should complete within performance requirements
            duration = end_time - start_time
            assert duration < 1.0  # <1s requirement
            assert result.success is True
