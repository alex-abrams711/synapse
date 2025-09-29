"""Unit tests for template models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from synapse.models.template import (
    ContentSlot,
    IntegrationStrategy,
    IntegrationType,
    PreservationRule,
    SlotType,
    TemplateConfig,
)


class TestTemplateConfig:
    """Test TemplateConfig model."""

    def test_template_config_creation(self) -> None:
        """Test basic TemplateConfig creation."""
        config = TemplateConfig(
            template_version="1.0.0",
            user_content_slots={"context": "My project context"},
            backup_created=True,
            integration_date=datetime.now(),
            original_file_hash="abc123"
        )
        assert config.template_version == "1.0.0"
        assert config.user_content_slots["context"] == "My project context"
        assert config.backup_created is True
        assert config.original_file_hash == "abc123"

    def test_template_config_defaults(self) -> None:
        """Test TemplateConfig with default values."""
        config = TemplateConfig(
            template_version="1.0.0",
            user_content_slots={}
        )
        assert config.backup_created is False
        assert config.integration_date is None
        assert config.original_file_hash is None

    def test_template_version_validation(self) -> None:
        """Test template version validation."""
        # Valid semantic version
        config = TemplateConfig(
            template_version="1.2.3",
            user_content_slots={}
        )
        assert config.template_version == "1.2.3"

        # Invalid version should raise ValidationError
        with pytest.raises(ValidationError):
            TemplateConfig(
                template_version="invalid-version",
                user_content_slots={}
            )

    def test_user_content_slots_validation(self) -> None:
        """Test user content slots validation."""
        # Valid slot names
        config = TemplateConfig(
            template_version="1.0.0",
            user_content_slots={
                "valid_slot": "content",
                "another_valid_slot": "more content"
            }
        )
        assert len(config.user_content_slots) == 2

        # Invalid slot names should be validated by the validator
        with pytest.raises(ValidationError):
            TemplateConfig(
                template_version="1.0.0",
                user_content_slots={
                    "invalid slot": "content",  # Space not allowed
                }
            )


class TestContentSlot:
    """Test ContentSlot model."""

    def test_content_slot_creation(self) -> None:
        """Test basic ContentSlot creation."""
        slot = ContentSlot(
            slot_name="user_context",
            content="My project context",
            slot_type=SlotType.CONTEXT,
            is_preserved=True,
            original_location="lines 1-10"
        )
        assert slot.slot_name == "user_context"
        assert slot.content == "My project context"
        assert slot.slot_type == SlotType.CONTEXT
        assert slot.is_preserved is True
        assert slot.original_location == "lines 1-10"

    def test_content_slot_defaults(self) -> None:
        """Test ContentSlot with default values."""
        slot = ContentSlot(
            slot_name="test_slot",
            content="Test content",
            slot_type=SlotType.CUSTOM
        )
        assert slot.is_preserved is False
        assert slot.original_location is None

    def test_slot_name_validation(self) -> None:
        """Test slot name validation."""
        # Valid slot names
        valid_names = ["user_context", "custom_instructions", "project_metadata"]
        for name in valid_names:
            slot = ContentSlot(
                slot_name=name,
                content="test",
                slot_type=SlotType.CUSTOM
            )
            assert slot.slot_name == name

        # Invalid slot names
        invalid_names = ["invalid slot", "slot-with-dash", "123slot"]
        for name in invalid_names:
            with pytest.raises(ValidationError):
                ContentSlot(
                    slot_name=name,
                    content="test",
                    slot_type=SlotType.CUSTOM
                )

    def test_content_validation(self) -> None:
        """Test content validation for template injection."""
        # Valid content
        slot = ContentSlot(
            slot_name="test_slot",
            content="This is normal content",
            slot_type=SlotType.CUSTOM
        )
        assert slot.content == "This is normal content"

        # Content with dangerous template patterns should be rejected
        dangerous_patterns = ["{{injection}}", "{%command%}", "{{exec}}"]
        for pattern in dangerous_patterns:
            with pytest.raises(ValidationError):
                ContentSlot(
                    slot_name="test_slot",
                    content=f"Content with {pattern}",
                    slot_type=SlotType.CUSTOM
                )

    def test_slot_types(self) -> None:
        """Test all slot types are valid."""
        for slot_type in SlotType:
            slot = ContentSlot(
                slot_name="test_slot",
                content="test content",
                slot_type=slot_type
            )
            assert slot.slot_type == slot_type


class TestIntegrationStrategy:
    """Test IntegrationStrategy model."""

    def test_integration_strategy_creation(self) -> None:
        """Test basic IntegrationStrategy creation."""
        strategy = IntegrationStrategy(
            strategy_type=IntegrationType.SLOT_BASED,
            content_mapping={"context": "user_context_slot"},
            preservation_rules=[
                PreservationRule(
                    action="preserve",
                    pattern="# Custom.*",
                    target_slot="custom_content"
                )
            ],
            migration_required=False
        )
        assert strategy.strategy_type == IntegrationType.SLOT_BASED
        assert strategy.content_mapping["context"] == "user_context_slot"
        assert len(strategy.preservation_rules) == 1
        assert strategy.migration_required is False

    def test_integration_strategy_defaults(self) -> None:
        """Test IntegrationStrategy with default values."""
        strategy = IntegrationStrategy(
            strategy_type=IntegrationType.TEMPLATE_REPLACEMENT,
            content_mapping={}
        )
        assert strategy.preservation_rules == []
        assert strategy.migration_required is False

    def test_content_mapping_validation(self) -> None:
        """Test content mapping validation."""
        # Valid mapping
        strategy = IntegrationStrategy(
            strategy_type=IntegrationType.SLOT_BASED,
            content_mapping={
                "valid_key": "valid_slot",
                "another_key": "another_slot"
            }
        )
        assert len(strategy.content_mapping) == 2

        # Invalid mapping keys should be rejected
        with pytest.raises(ValidationError):
            IntegrationStrategy(
                strategy_type=IntegrationType.SLOT_BASED,
                content_mapping={
                    "invalid key": "valid_slot",  # Space not allowed
                }
            )

    def test_integration_types(self) -> None:
        """Test all integration types are valid."""
        for integration_type in IntegrationType:
            strategy = IntegrationStrategy(
                strategy_type=integration_type,
                content_mapping={}
            )
            assert strategy.strategy_type == integration_type


class TestPreservationRule:
    """Test PreservationRule model."""

    def test_preservation_rule_creation(self) -> None:
        """Test basic PreservationRule creation."""
        rule = PreservationRule(
            action="preserve",
            pattern="# Custom.*",
            target_slot="custom_content"
        )
        assert rule.action == "preserve"
        assert rule.pattern == "# Custom.*"
        assert rule.target_slot == "custom_content"

    def test_preservation_rule_defaults(self) -> None:
        """Test PreservationRule with default values."""
        rule = PreservationRule(
            action="preserve",
            pattern=".*"
        )
        assert rule.target_slot is None

    def test_action_validation(self) -> None:
        """Test preservation action validation."""
        # Valid actions
        valid_actions = ["preserve", "transform", "discard"]
        for action in valid_actions:
            rule = PreservationRule(
                action=action,
                pattern=".*"
            )
            assert rule.action == action

        # Invalid action should be rejected
        with pytest.raises(ValidationError):
            PreservationRule(
                action="invalid_action",
                pattern=".*"
            )


class TestModelIntegration:
    """Test integration between template models."""

    def test_template_config_with_content_slots(self) -> None:
        """Test TemplateConfig with ContentSlot integration."""
        # Create content slots
        context_slot = ContentSlot(
            slot_name="user_context",
            content="Project context",
            slot_type=SlotType.CONTEXT
        )

        instructions_slot = ContentSlot(
            slot_name="user_instructions",
            content="Custom instructions",
            slot_type=SlotType.INSTRUCTIONS
        )

        # Create template config with slot content
        config = TemplateConfig(
            template_version="1.0.0",
            user_content_slots={
                context_slot.slot_name: context_slot.content,
                instructions_slot.slot_name: instructions_slot.content
            }
        )

        assert len(config.user_content_slots) == 2
        assert config.user_content_slots["user_context"] == "Project context"
        assert config.user_content_slots["user_instructions"] == "Custom instructions"

    def test_integration_strategy_with_preservation_rules(self) -> None:
        """Test IntegrationStrategy with preservation rules."""
        rules = [
            PreservationRule(
                action="preserve",
                pattern="# Custom Section.*",
                target_slot="custom_content"
            ),
            PreservationRule(
                action="transform",
                pattern="## Instructions.*",
                target_slot="user_instructions"
            )
        ]

        strategy = IntegrationStrategy(
            strategy_type=IntegrationType.HYBRID,
            content_mapping={
                "custom": "custom_content",
                "instructions": "user_instructions"
            },
            preservation_rules=rules
        )

        assert len(strategy.preservation_rules) == 2
        assert strategy.preservation_rules[0].action == "preserve"
        assert strategy.preservation_rules[1].action == "transform"
        assert strategy.content_mapping["custom"] == "custom_content"
