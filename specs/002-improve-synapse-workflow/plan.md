# Implementation Plan: Synapse Workflow UX Improvements

**Branch**: `002-improve-synapse-workflow` | **Date**: 2025-09-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/Users/alexabrams/Workspace/synapse/specs/002-improve-synapse-workflow/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → Loaded: Synapse workflow UX improvements with CLAUDE.md integration and slash commands
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detected: Existing Python project, CLI modification, template enhancement
   → Set Structure Decision: Single project modification (existing synapse/ codebase)
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → All principles aligned: Library-first, TDD, CLI interfaces, observability
   → Update Progress Tracking: Initial Constitution Check PASS
5. Execute Phase 0 → research.md
   → Research CLAUDE.md template integration patterns and slash command implementation
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
   → Generate CLI command contracts, template integration models, user scenarios
7. Re-evaluate Constitution Check section
   → Verify design maintains constitutional compliance
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 8. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Enhance Synapse Agent Workflow System to provide seamless integration with existing Claude Code setups through template-based CLAUDE.md integration and explicit agent invocation slash commands. Key improvements include conflict-free file placement using structured templates with user content slots, and intuitive workflow commands (/synapse:plan, /synapse:implement, /synapse:review) plus direct agent communication (/synapse:dev, /synapse:audit, /synapse:dispatch).

## Technical Context
**Language/Version**: Python 3.11+ (existing codebase)
**Primary Dependencies**: Click (CLI), PyYAML (config), Jinja2 (templating), pathlib (file operations)
**Storage**: File-based templates and JSON state (existing approach)
**Testing**: pytest with existing test structure
**Target Platform**: Cross-platform CLI tool (macOS, Linux, Windows)
**Project Type**: single - Modification of existing CLI package
**Performance Goals**: <500ms for template integration, <1s for command registration
**Constraints**: Must preserve existing functionality, no breaking changes to workflow state
**Scale/Scope**: Template system for CLAUDE.md integration, 6 new slash commands, enhanced CLI

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Core Principles Alignment
- [x] **I. Library-First Architecture**: Enhancing existing CLI library with new template capabilities
- [x] **II. Workflow Composability**: New slash commands integrate with existing workflow orchestration
- [x] **III. Agent Autonomy & Orchestration**: Maintains existing agent boundaries, adds explicit invocation
- [x] **IV. Test-First Development**: TDD approach with template integration tests and CLI command tests
- [x] **V. CLI & API Dual Interface**: Enhancing CLI with new commands, maintaining programmatic access
- [x] **VI. Observability & Debugging**: Template integration logging, command execution tracing
- [x] **VII. Semantic Versioning**: Minor version bump for new features, backward compatible

### Quality Gates
- [ ] Code coverage > 80% (pending implementation)
- [ ] All public APIs documented (pending implementation)
- [ ] Performance benchmarks established (pending implementation)
- [ ] Security scanning passes (pending implementation)

**PASS**: All constitutional principles aligned with UX enhancement approach

## Project Structure

### Documentation (this feature)
```
specs/002-improve-synapse-workflow/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
synapse/
├── __init__.py
├── cli/
│   ├── __init__.py
│   ├── main.py          # Enhanced Click CLI with new commands
│   ├── init.py          # Updated init command with template integration
│   └── commands.py      # New slash command registration system
├── templates/
│   ├── __init__.py
│   ├── claude/
│   │   ├── agents/      # Existing agent templates
│   │   ├── commands/    # Enhanced command templates with new slash commands
│   │   └── CLAUDE.md.j2 # New Jinja2 template for CLAUDE.md integration
│   └── synapse/         # Existing workflow templates
├── models/
│   ├── __init__.py
│   ├── project.py       # Enhanced with template integration config
│   ├── task.py          # Existing workflow models
│   └── template.py      # New template integration models
├── services/
│   ├── __init__.py
│   ├── scaffolder.py    # Enhanced with template integration
│   ├── validator.py     # Enhanced template validation
│   └── integrator.py    # New CLAUDE.md integration service
└── utils/
    ├── __init__.py
    └── conflicts.py     # New command conflict detection

tests/
├── cli/
│   ├── test_init_command.py       # Updated for template integration
│   └── test_commands.py           # New slash command tests
├── integration/
│   ├── test_template_integration.py # New integration tests
│   └── test_claude_integration.py   # Enhanced existing tests
├── unit/
│   ├── test_models/
│   │   └── test_template.py       # New template model tests
│   ├── test_services/
│   │   └── test_integrator.py     # New integration service tests
│   └── test_utils/
│       └── test_conflicts.py      # New conflict detection tests
```

**Structure Decision**: Enhance existing single project structure with new template integration capabilities, slash command system, and CLAUDE.md integration service while preserving existing workflow functionality.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - Template integration patterns for preserving user content
   - Jinja2 templating best practices for markdown files
   - Claude Code slash command registration mechanisms
   - Command conflict detection strategies

2. **Generate and dispatch research agents**:
   ```
   Task: "Research Jinja2 templating patterns for markdown file integration"
   Task: "Research Claude Code slash command implementation approaches"
   Task: "Research file content preservation strategies during template integration"
   Task: "Research command conflict detection and resolution patterns"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all template integration and command system decisions resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - TemplateConfig: User content preservation configuration
   - CommandRegistry: Slash command conflict tracking
   - IntegrationStrategy: CLAUDE.md integration approach
   - SlashCommand: New command definition model
   - ContentSlot: User content placeholder in templates

2. **Generate API contracts** from functional requirements:
   - CLI command contracts for new slash command registration
   - Template integration API contracts
   - Conflict detection service contracts
   - Output contracts to `/contracts/`

3. **Generate contract tests** from contracts:
   - Template integration CLI tests (must fail initially)
   - Slash command registration tests (must fail initially)
   - Conflict detection tests (must fail initially)

4. **Extract test scenarios** from user stories:
   - Existing CLAUDE.md preservation scenario
   - New slash command usage scenarios
   - Command conflict resolution scenarios

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh claude`
   - Add template integration capabilities
   - Add new slash command information
   - Update recent UX enhancement changes

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, CLAUDE.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each CLI command contract → contract test task [P]
- Each template integration model → model creation task [P]
- Each user story → integration test task
- Implementation tasks to make tests pass

**Specific Tasks to Generate**:
1. **Contract Tests (3 tasks)**: Template integration CLI, slash command registration, conflict detection
2. **Data Models (5 tasks)**: TemplateConfig, CommandRegistry, IntegrationStrategy, SlashCommand, ContentSlot
3. **Template Files (7 tasks)**: CLAUDE.md.j2 template, 6 new slash command templates
4. **Services (2 tasks)**: Enhanced integrator service, conflict detection service
5. **CLI Implementation (3 tasks)**: Enhanced init command, new command registration, conflict handling
6. **Integration Tests (4 tasks)**: End-to-end template integration, slash command workflows

**Ordering Strategy**:
- TDD order: Contract tests → Models → Templates → Services → CLI → Integration
- Template files can run in parallel with model tasks [P]
- CLI depends on services and models (sequential)
- Integration tests validate complete workflow

**Estimated Output**: 24-28 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*No constitutional violations requiring justification*

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none required)

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*