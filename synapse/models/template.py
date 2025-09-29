"""Template integration models for Synapse workflow system."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SlotType(str, Enum):
    """Types of content slots in templates."""

    CONTEXT = "context"
    INSTRUCTIONS = "instructions"
    CUSTOM = "custom"
    METADATA = "metadata"


class IntegrationType(str, Enum):
    """Types of template integration strategies."""

    TEMPLATE_REPLACEMENT = "template_replacement"
    SLOT_BASED = "slot_based"
    HYBRID = "hybrid"


class PreservationRule(BaseModel):
    """Rule for preserving content during template integration."""

    pattern: str = Field(..., description="Pattern to match content for preservation")
    action: str = Field(..., description="Action to take (preserve, transform, discard)")
    target_slot: str | None = Field(default=None, description="Target slot for preserved content")
    priority: int = Field(default=0, description="Priority for rule application")

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        """Validate preservation action."""
        valid_actions = {"preserve", "transform", "discard"}
        if v not in valid_actions:
            raise ValueError(f"Action must be one of: {valid_actions}")
        return v


class ContentSlot(BaseModel):
    """Represents a user content area within a template."""

    model_config = ConfigDict(use_enum_values=True)

    slot_name: str = Field(..., description="Unique identifier for the content slot")
    content: str = Field(..., description="User-provided content for this slot")
    is_preserved: bool = Field(default=False, description="Whether content was preserved")
    original_location: str | None = Field(default=None, description="Original location in file")
    slot_type: SlotType = Field(..., description="Type of content slot")

    @field_validator("slot_name")
    @classmethod
    def validate_slot_name(cls, v: str) -> str:
        """Validate slot name format."""
        import re

        # Must be alphanumeric with underscores, not start with number, no spaces/dashes
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", v):
            raise ValueError("Slot name must be alphanumeric with underscores, start with letter")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate content doesn't contain template injection."""
        dangerous_patterns = ["{%", "{{", "%}", "}}"]
        for pattern in dangerous_patterns:
            if pattern in v:
                raise ValueError(f"Content cannot contain template syntax: {pattern}")
        return v


class IntegrationStrategy(BaseModel):
    """Defines how existing content is integrated with templates."""

    model_config = ConfigDict(use_enum_values=True)

    strategy_type: IntegrationType = Field(..., description="Type of integration")
    content_mapping: dict[str, str] = Field(
        default_factory=dict, description="Mapping of original content to template slots"
    )
    preservation_rules: list[PreservationRule] = Field(
        default_factory=list, description="Rules for content preservation"
    )
    migration_required: bool = Field(
        default=False, description="Whether migration from previous version needed"
    )

    @field_validator("content_mapping")
    @classmethod
    def validate_content_mapping(cls, v: dict[str, str]) -> dict[str, str]:
        """Validate content mapping keys."""
        for key in v.keys():
            if not key.replace("_", "").isalnum():
                raise ValueError(f"Mapping key must be alphanumeric: {key}")
        return v


class TemplateConfig(BaseModel):
    """Configuration for CLAUDE.md template integration."""

    model_config = ConfigDict(
        use_enum_values=True, json_encoders={datetime: lambda v: v.isoformat()}
    )

    template_version: str = Field(..., description="Version of template structure")
    user_content_slots: dict[str, str] = Field(
        default_factory=dict, description="Mapping of slot names to user content"
    )
    backup_created: bool = Field(
        default=False, description="Whether backup was created before integration"
    )
    integration_date: datetime | None = Field(
        default=None, description="When template integration was performed"
    )
    original_file_hash: str | None = Field(
        default=None, description="Hash of original file for change detection"
    )
    integration_strategy: IntegrationStrategy | None = Field(
        default=None, description="Strategy used for integration"
    )

    @field_validator("template_version")
    @classmethod
    def validate_template_version(cls, v: str) -> str:
        """Validate semantic versioning format."""
        import re

        pattern = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9-]+)?$"
        if not re.match(pattern, v):
            raise ValueError("Template version must follow semantic versioning")
        return v

    @field_validator("user_content_slots")
    @classmethod
    def validate_user_content_slots(cls, v: dict[str, str]) -> dict[str, str]:
        """Validate user content slot keys."""
        for key in v.keys():
            if not key.replace("_", "").isalnum():
                raise ValueError(f"Slot key must be alphanumeric: {key}")
        return v

    def add_content_slot(self, slot_name: str, content: str) -> None:
        """Add content to a template slot."""
        self.user_content_slots[slot_name] = content

    def get_content_slot(self, slot_name: str, default: str = "") -> str:
        """Get content from a template slot."""
        return self.user_content_slots.get(slot_name, default)

    def has_content_slot(self, slot_name: str) -> bool:
        """Check if a content slot exists."""
        return slot_name in self.user_content_slots

    def create_backup_info(self, file_hash: str) -> None:
        """Mark that backup was created with file hash."""
        self.backup_created = True
        self.original_file_hash = file_hash
        if not self.integration_date:
            self.integration_date = datetime.now()
