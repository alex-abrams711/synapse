# Change Proposal: Implement Synapse CLI System

**Change ID**: `implement-synapse-cli-system`
**Type**: New Feature
**Status**: Proposed
**Created**: 2025-10-20
**Owner**: Development Team

---

## Overview

Implement the complete Synapse CLI tool from scratch - a Python-based command-line application that enables developers to apply AI workflow patterns to their Claude Code setup through file copying and settings management.

## Problem Statement

Developers currently face several challenges when working with Claude Code:
1. **Manual Setup**: Must manually create `.claude/` directory structures and configuration files
2. **Inconsistent Workflows**: No standardized way to apply structured task management patterns
3. **Configuration Drift**: Difficult to track, version, and rollback Claude Code configuration changes
4. **Quality Enforcement**: No automated quality gates for AI-assisted development

## Proposed Solution

Build a CLI tool that provides:
- **Project Initialization**: Sets up `.synapse/` configuration directory
- **Workflow Application**: Copies pre-defined workflow files to `.claude/` directory
- **Two Workflow Patterns**:
  - **Feature Planning**: Structured task creation with quality standards
  - **Feature Implementation**: Quality-gated development with automated verification
- **Settings Management**: Safely merges workflow settings with existing Claude Code settings
- **State Tracking**: Maintains workflow state with complete rollback capability
- **Backup System**: Atomic operations with timestamped backups

## Scope

### In Scope
- Complete Python CLI implementation with argparse
- Two workflow patterns (feature-planning, feature-implementation)
- File operations (copy agents, hooks, commands)
- Settings merge with JSON validation
- Backup/restore system
- State tracking and manifest management
- Project initialization command
- Workflow management commands (list, status, remove, apply)

### Out of Scope
- Multi-project support
- Cloud hosting or sharing
- Plugin architecture
- Integration with other AI assistants beyond Claude Code
- Advanced analytics or telemetry
- Enterprise features
- Multi-language support

## Benefits

1. **Simplified Setup**: One command to apply comprehensive workflow patterns
2. **Safety**: Backup/restore prevents data loss during configuration changes
3. **Consistency**: Standardized workflow patterns across projects
4. **Quality Enforcement**: Automated quality gates in implementation workflow
5. **Rollback Capability**: Complete state tracking enables clean workflow removal

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| JSON corruption during settings merge | High | Validate before writing, maintain backups |
| File permission issues | Medium | Check/set executable permissions on shell scripts |
| Workflow conflicts | Medium | Track files per workflow, prevent overwrites without --force |
| Python version compatibility | Low | Test on Python 3.9+ |
| Resource discovery in packaged CLI | Medium | Use setuptools resource APIs correctly |

## Dependencies

### Technical Dependencies
- Python 3.9+
- setuptools (packaging)
- uv (runtime dependency for Python hooks)
- Playwright (optional, for verifier agent testing)

### External Dependencies
- Claude Code (required - this tool configures Claude Code)

## Success Criteria

- [ ] All CLI commands (`init`, `workflow list/status/remove/<name>`) work correctly
- [ ] Both workflows can be applied and removed without data loss
- [ ] Settings merge doesn't corrupt existing `.claude/settings.json`
- [ ] Backup/restore system prevents data loss
- [ ] Python hooks execute correctly with `uv run`
- [ ] File permissions are set correctly on shell scripts
- [ ] Comprehensive integration tests pass
- [ ] Tool can be installed via pip/pipx

## Related Changes

None (this is the initial implementation)

## Capabilities Introduced

1. **CLI Core** - Command-line interface with project initialization
2. **File Operations** - Workflow file copying with permission management
3. **Settings Management** - JSON merge with validation
4. **Backup System** - Timestamped backups with restore capability
5. **State Tracking** - Workflow manifest and configuration management
6. **Feature Planning Workflow** - Task-writer agent with reminder hooks
7. **Feature Implementation Workflow** - Quality-gated development with agents and hooks
8. **Sense Command** - Project analysis and quality configuration

## Implementation Phases

### Phase 1: Core CLI & File Operations
- Project initialization
- Basic file copying
- Command structure

### Phase 2: Settings & State Management
- JSON merge logic
- Backup/restore system
- State tracking

### Phase 3: Feature Planning Workflow
- Task-writer agent
- Reminder hooks
- Sense command

### Phase 4: Feature Implementation Workflow
- Implementer & verifier agents
- Quality gate hooks (Python)
- Comprehensive QA integration

## Timeline Estimate

- **Phase 1**: 2-3 days
- **Phase 2**: 2-3 days
- **Phase 3**: 1-2 days
- **Phase 4**: 3-4 days
- **Testing & Refinement**: 2-3 days

**Total**: ~10-15 days for complete implementation

## Design Decisions

### 1. Workflow Switching Strategy
**Decision**: When switching workflows with `--force` flag, completely remove the active workflow before applying the new one.

**Rationale**:
- Prevents hanging artifacts in `.claude/` or `.synapse/`
- Ensures clean state with only one workflow active at a time
- Simpler state management and easier to reason about
- No conflicts between workflow files or settings

**Implementation**:
```bash
# User runs this while feature-planning is active
synapse workflow feature-implementation --force

# System does:
1. Remove feature-planning workflow (restore from backup)
2. Apply feature-implementation workflow
3. Result: Clean state with only implementation workflow
```

### 2. Partial Application Failure Handling
**Decision**: Full atomic rollback - if any step fails during workflow application, restore from backup and leave no partial changes.

**Rationale**:
- Users never end up in broken/partial state
- All-or-nothing approach is easier to understand and debug
- Backup system provides clean rollback mechanism
- Prevents corrupted `.claude/` configurations

**Implementation**:
- Create backup before any modifications
- If any step fails (file copy, settings merge, etc.), restore entire `.claude/` from backup
- Report clear error about what failed
- User can fix issue and retry

### 3. Sense Command Scope
**Decision**: Each workflow includes its own workflow-specific `sense.md` with different focus areas.

**Rationale**:
- Planning workflow needs different project insights than implementation workflow
- Tailored commands provide more relevant information
- Each workflow remains self-contained

**Implementation**:
- **Planning workflow's sense.md** focuses on:
  - Project structure and architecture
  - Documentation locations
  - Existing task management patterns
  - High-level project understanding

- **Implementation workflow's sense.md** focuses on:
  - Quality tool detection (linters, type checkers, test runners)
  - CI/CD configuration
  - Coverage thresholds and quality gates
  - Build systems and test frameworks

### 4. Workflow Upgrade Path
**Decision**: Manual re-application required - users must run `synapse workflow <name> --force` after upgrading CLI to get updated workflow definitions.

**Rationale**:
- Explicit user control over when workflows update
- No automatic changes that might break existing setup
- Simple to implement (no complex version tracking)
- Workflows versioned implicitly by CLI version

**Implementation**:
```bash
# User upgrades Synapse CLI
pip install --upgrade synapse-cli

# To get updated workflow definitions
synapse workflow feature-planning --force
```

**Note**: Starting version is v0.3.0 (complete rewrite of Synapse, previous versions obsoleted)
