"""Contract tests for template integration service API."""

import tempfile
from datetime import datetime
from pathlib import Path


class TestTemplateIntegrationService:
    """Test template integration service API contracts."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = Path(self.temp_dir) / "test_claude.md"

    def teardown_method(self) -> None:
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_analyze_existing_claude_md(self) -> None:
        """Test /template/analyze endpoint contract."""
        # Create sample CLAUDE.md file
        sample_content = """# My Project

This is my project context.

## Custom Instructions

My custom instructions here.

## Project Guidelines

Project-specific guidelines.
"""
        self.test_file_path.write_text(sample_content)

        # Template integration service now exists, test actual functionality
        from synapse.services.integrator import TemplateIntegrator
        service = TemplateIntegrator()

        result = service.analyze_claude_md(str(self.test_file_path), "1.0.0")

        # Expected contract response
        assert result.file_exists is True
        assert len(result.content_sections) > 0
        # Check for the actual slot names returned by the implementation
        assert len(result.user_content_slots) > 0  # Should find user content slots
        assert result.integration_strategy in ["template_replacement", "slot_based", "hybrid"]
        assert result.backup_required is True

    def test_integrate_template_contract(self) -> None:
        """Test /template/integrate endpoint contract."""
        # Template integration service now exists, test actual functionality
        from synapse.models.template import TemplateConfig
        from synapse.services.integrator import TemplateIntegrator

        # Create test file first
        test_content = """# Test Project

## Context
My project context here.

## Instructions
My custom instructions.
"""
        self.test_file_path.write_text(test_content)

        template_config = TemplateConfig(
            template_version="1.0.0",
            user_content_slots={"user_context": "My context"},
            integration_date=datetime.now()
        )

        service = TemplateIntegrator()
        result = service.integrate_template(
            str(self.test_file_path),
            template_config,
            integration_strategy="slot_based",
            create_backup=True
        )

        # Expected contract response
        assert result.success is True
        assert result.output_file is not None
        assert result.backup_file is not None
        assert isinstance(result.preserved_content, dict)
        assert isinstance(result.warnings, list)

    def test_validate_template_integration(self) -> None:
        """Test /template/validate endpoint contract."""
        # Template integration service now exists, test actual functionality
        from synapse.services.integrator import TemplateIntegrator

        # Create test content that includes the user context
        test_content = """# Test Project

My context content here

## Other sections
Some other content
"""
        self.test_file_path.write_text(test_content)

        service = TemplateIntegrator()
        result = service.validate_integration(
            integrated_file=str(self.test_file_path),
            original_content={"user_context_slot": "My context content here"},
            template_version="1.0.0"
        )

        # Expected contract response
        assert isinstance(result.is_valid, bool)
        assert isinstance(result.validation_errors, list)
        assert hasattr(result, 'content_integrity')
        assert "slots_preserved" in result.content_integrity
        assert "slots_lost" in result.content_integrity

    def test_register_slash_commands_contract(self) -> None:
        """Test /commands/register endpoint contract."""
        # Command models and registry now exist, test actual functionality
        from synapse.models.command import AgentType, SlashCommand
        from synapse.services.command_registry import CommandRegistry

        # Create commands directory
        commands_dir = Path(self.temp_dir) / ".claude" / "commands"
        commands_dir.mkdir(parents=True)

        commands = [
            SlashCommand(
                name="/synapse:plan",
                description="Planning command",
                agent_target=AgentType.DISPATCHER,
                command_template="# /synapse:plan\n\nPlanning command template",
                command_file_path="synapse-plan.md",
                is_synapse_managed=True
            )
        ]

        registry = CommandRegistry()
        result = registry.register_commands(
            commands=commands,
            command_dir=str(commands_dir)
        )

        # Expected contract response
        assert hasattr(result, 'registered_commands')
        assert hasattr(result, 'conflicts_detected')

    def test_detect_command_conflicts_contract(self) -> None:
        """Test /commands/detect-conflicts endpoint contract."""
        # Create mock commands directory
        commands_dir = Path(self.temp_dir) / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "plan.md").write_text("# /plan - Existing command")

        from synapse.utils.conflicts import detect_command_conflicts

        result = detect_command_conflicts(
            proposed_commands=["plan", "implement", "review"],
            command_dir=str(commands_dir)
        )

        # Expected contract response
        assert isinstance(result.conflicts, list)
        assert hasattr(result, 'conflict_summary')
        assert hasattr(result.conflict_summary, 'total_conflicts')
        assert hasattr(result.conflict_summary, 'name_collisions')

    def test_template_config_model_contract(self) -> None:
        """Test TemplateConfig model contract."""
        from synapse.models.template import TemplateConfig

        config = TemplateConfig(
            template_version="1.0.0",
            user_content_slots={"user_context": "content"},
            backup_created=True,
            integration_date=datetime.now(),
            original_file_hash="abc123"
        )

        # Model should have proper validation
        assert config.template_version == "1.0.0"
        assert isinstance(config.user_content_slots, dict)
        assert config.backup_created is True

    def test_slash_command_model_contract(self) -> None:
        """Test SlashCommand model contract."""
        from synapse.models.command import AgentType, SlashCommand

        command = SlashCommand(
            name="/synapse:plan",
            description="Planning command",
            agent_target=AgentType.DISPATCHER,
            command_template="# Synapse Plan Command\n\nTemplate content",
            is_synapse_managed=True
        )

        # Model should validate synapse prefix
        assert command.name.startswith("/synapse:")
        assert command.agent_target == AgentType.DISPATCHER
        assert command.is_synapse_managed is True

    def test_conflict_info_model_contract(self) -> None:
        """Test ConflictInfo model contract."""
        from synapse.models.command import (
            AgentType,
            ConflictInfo,
            ConflictResolution,
            ConflictType,
            SlashCommand,
        )

        # Create a proper SlashCommand for synapse_command
        synapse_cmd = SlashCommand(
            name="/synapse:plan",
            description="Planning command",
            agent_target=AgentType.DISPATCHER,
            command_template="# Synapse Plan Command\n\nTemplate content",
            is_synapse_managed=True
        )

        conflict = ConflictInfo(
            command_name="/plan",
            existing_source="/path/to/plan.md",
            synapse_command=synapse_cmd,
            conflict_type=ConflictType.NAME_COLLISION,
            resolution=ConflictResolution.USE_PREFIX,
            detected_date=datetime.now(),
            is_resolvable=True
        )

        # Model should have proper validation
        assert conflict.conflict_type == ConflictType.NAME_COLLISION
        assert conflict.resolution == ConflictResolution.USE_PREFIX
        assert isinstance(conflict.is_resolvable, bool)

    def test_integration_strategy_contract(self) -> None:
        """Test integration strategy model contract."""
        from synapse.models.template import IntegrationStrategy

        strategy = IntegrationStrategy(
            strategy_type="slot_based",
            content_mapping={"user_context": "context_content"},
            preservation_rules=[],
            migration_required=False
        )

        # Model should validate strategy types
        assert strategy.strategy_type in ["template_replacement", "slot_based", "hybrid"]
        assert isinstance(strategy.content_mapping, dict)
        assert isinstance(strategy.migration_required, bool)
