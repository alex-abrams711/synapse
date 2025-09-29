# Data Model: Synapse Workflow UX Improvements

**Feature**: Template Integration and Slash Command System
**Date**: 2025-09-28
**Phase**: Phase 1 - Data Model Design

## Core Entities

### TemplateConfig
Configuration for CLAUDE.md template integration and user content preservation.

**Fields**:
- `template_version: str` - Version of template structure being used
- `user_content_slots: Dict[str, str]` - Mapping of slot names to user content
- `backup_created: bool` - Whether backup was created before integration
- `integration_date: datetime` - When template integration was performed
- `original_file_hash: str` - Hash of original CLAUDE.md for change detection

**Relationships**:
- One-to-one with ProjectConfig
- Contains multiple ContentSlot entries

**Validation Rules**:
- template_version must follow semantic versioning
- user_content_slots keys must match template slot definitions
- backup_created must be true before any integration

**State Transitions**:
- DETECTED → ANALYZED → INTEGRATED → VALIDATED

### ContentSlot
Represents a user content area within the CLAUDE.md template.

**Fields**:
- `slot_name: str` - Unique identifier for the content slot
- `content: str` - User-provided content for this slot
- `is_preserved: bool` - Whether content was successfully preserved during integration
- `original_location: str` - Original location in file (line numbers or section)
- `slot_type: SlotType` - Type of content (CONTEXT, INSTRUCTIONS, CUSTOM)

**Relationships**:
- Many-to-one with TemplateConfig
- Referenced by IntegrationStrategy

**Validation Rules**:
- slot_name must be alphanumeric with underscores
- content cannot contain template syntax that could cause injection
- original_location must be valid file location reference

### CommandRegistry
Tracks installed slash commands and manages conflict detection.

**Fields**:
- `installed_commands: Dict[str, SlashCommand]` - Mapping of command names to definitions
- `conflicts: List[ConflictInfo]` - Detected conflicts with existing commands
- `last_scan_date: datetime` - When conflict detection was last performed
- `synapse_commands: List[str]` - List of Synapse-managed command names

**Relationships**:
- One-to-one with ProjectConfig
- Contains multiple SlashCommand entries
- References ConflictInfo entries

**Validation Rules**:
- Command names must be unique within registry
- Synapse commands must use '/synapse:' prefix
- Conflicts must be resolved or documented before installation

### SlashCommand
Definition of a Claude Code slash command.

**Fields**:
- `name: str` - Command name (e.g., '/synapse:plan')
- `description: str` - Human-readable description of command functionality
- `agent_target: AgentType` - Which agent this command invokes
- `command_file_path: str` - Path to command definition file
- `is_synapse_managed: bool` - Whether this command is managed by Synapse
- `installation_date: datetime` - When command was installed

**Relationships**:
- Many-to-one with CommandRegistry
- References agent definitions

**Validation Rules**:
- name must start with '/' and contain no spaces
- agent_target must be valid agent type (DEV, AUDITOR, DISPATCHER)
- command_file_path must exist and be readable

**State Transitions**:
- DEFINED → VALIDATED → INSTALLED → ACTIVE

### IntegrationStrategy
Defines how existing CLAUDE.md content is integrated with Synapse templates.

**Fields**:
- `strategy_type: IntegrationType` - Type of integration (TEMPLATE_REPLACEMENT, SLOT_BASED)
- `content_mapping: Dict[str, str]` - Mapping of original content to template slots
- `preservation_rules: List[PreservationRule]` - Rules for content preservation
- `migration_required: bool` - Whether migration from previous version needed

**Relationships**:
- One-to-one with TemplateConfig
- References ContentSlot mappings

**Validation Rules**:
- strategy_type must be supported integration type
- content_mapping keys must match available template slots
- preservation_rules must be valid and executable

### ConflictInfo
Information about detected command conflicts.

**Fields**:
- `command_name: str` - Name of conflicting command
- `existing_source: str` - Source of existing command (file path)
- `synapse_command: SlashCommand` - Synapse command that conflicts
- `conflict_type: ConflictType` - Type of conflict (NAME_COLLISION, FUNCTIONALITY_OVERLAP)
- `resolution: ConflictResolution` - How conflict was/will be resolved
- `detected_date: datetime` - When conflict was detected

**Relationships**:
- Many-to-one with CommandRegistry
- References SlashCommand

**Validation Rules**:
- command_name must match actual conflicting command
- existing_source must be valid file path
- resolution must be valid resolution type

## Enumerations

### SlotType
- `CONTEXT`: User project context and background
- `INSTRUCTIONS`: User-specific instructions and preferences
- `CUSTOM`: Custom user content sections
- `METADATA`: Project metadata and configuration

### AgentType
- `DEV`: Development and implementation agent
- `AUDITOR`: Quality assurance and verification agent
- `DISPATCHER`: Coordination and orchestration agent

### IntegrationType
- `TEMPLATE_REPLACEMENT`: Replace entire file with template structure
- `SLOT_BASED`: Insert user content into predefined template slots
- `HYBRID`: Combination of replacement and slot-based approaches

### ConflictType
- `NAME_COLLISION`: Command names are identical
- `FUNCTIONALITY_OVERLAP`: Commands have similar functionality
- `PREFIX_CONFLICT`: Command prefixes create ambiguity

### ConflictResolution
- `USE_PREFIX`: Add '/synapse:' prefix to Synapse commands
- `WARN_USER`: Display warning but proceed with installation
- `SKIP_COMMAND`: Skip conflicting Synapse command
- `USER_CHOICE`: Prompt user for resolution decision

## Entity Relationships

```
ProjectConfig
├── TemplateConfig (1:1)
│   ├── ContentSlot (1:many)
│   └── IntegrationStrategy (1:1)
└── CommandRegistry (1:1)
    ├── SlashCommand (1:many)
    └── ConflictInfo (1:many)
```

## Data Persistence

### Storage Format
- **TemplateConfig**: JSON in `.synapse/template_config.json`
- **CommandRegistry**: JSON in `.synapse/command_registry.json`
- **ContentSlots**: Embedded within TemplateConfig
- **ConflictInfo**: Embedded within CommandRegistry

### Migration Strategy
- Version-based migration scripts for data model changes
- Backward compatibility for at least one major version
- Automatic migration during `synapse init` if needed

## Validation Rules Summary

### Cross-Entity Validation
- TemplateConfig.user_content_slots must reference valid ContentSlot definitions
- CommandRegistry.installed_commands must not have unresolved conflicts
- IntegrationStrategy.content_mapping must align with TemplateConfig slots
- SlashCommand.agent_target must reference valid agent configurations

### Business Logic Constraints
- Cannot integrate template without successful backup creation
- Cannot install commands with unresolved NAME_COLLISION conflicts
- Cannot modify Synapse-managed commands outside of system updates
- Must preserve user content during template migrations

### Performance Constraints
- ContentSlot.content limited to 100KB per slot to prevent memory issues
- CommandRegistry conflict detection must complete within 5 seconds
- Template integration must complete within 10 seconds for typical configurations

This data model provides the foundation for implementing template-based CLAUDE.md integration and conflict-aware slash command management while maintaining data integrity and user control.