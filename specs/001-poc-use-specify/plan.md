
# Implementation Plan: Synapse Agent Workflow System POC

**Branch**: `001-poc-use-specify` | **Date**: 2025-09-27 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-poc-use-specify/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Build a globally installable Python package that provides Claude Code agent workflow orchestration. After installation, users run "synapse init" to scaffold a project with smart agents and workflow directory structure. The system prevents Claude Code from going off-rails through specialized agents (DEV, AUDITOR, DISPATCHER) that interact via JSON task logs within Claude Code sessions.

## Technical Context
**Language/Version**: Python 3.11+
**Primary Dependencies**: Click (CLI), JSON (persistence), pathlib (file operations)
**Storage**: JSON files (task logs, agent configs, workflow state)
**Testing**: pytest with fixtures for agent behavior
**Target Platform**: Cross-platform CLI tool (macOS, Linux, Windows)
**Project Type**: single - Global CLI package with project template scaffolding
**Performance Goals**: <1s for init command, <500ms for agent communication
**Constraints**: Agent code immutable at runtime, immediate user escalation on failures
**Scale/Scope**: POC - 3 agents, single workflow, template-based project initialization
**Architecture Note**: Global installation ("pip install synapse-workflow") enables "synapse init" to scaffold projects with Claude Code agents in `.claude/agents/` directory and workflow logging in `.synapse/` directory, NOT imported Python libraries

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Core Principles Alignment
- [x] **I. Library-First Architecture**: Global CLI package that scaffolds templates (not imported libraries)
- [x] **II. Workflow Composability**: Agent workflow supports task orchestration with branching logic
- [x] **III. Agent Autonomy & Orchestration**: Three agents with bounded scopes, JSON-based contracts
- [x] **IV. Test-First Development**: TDD approach with pytest, agent behavior testing
- [x] **V. CLI & API Dual Interface**: Primary CLI tool for initialization and project scaffolding
- [x] **VI. Observability & Debugging**: JSON task logs provide audit trail and debugging capability
- [x] **VII. Semantic Versioning**: Will follow semver for package releases

### Quality Gates
- [ ] Code coverage > 80% (pending implementation)
- [ ] All public APIs documented (pending implementation)
- [ ] Performance benchmarks established (pending implementation)
- [ ] Security scanning passes (pending implementation)

**PASS**: All constitutional principles aligned with global installation approach

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
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
│   ├── main.py          # Click CLI entry point (only "synapse init")
│   └── init.py          # "synapse init" command implementation
├── templates/
│   ├── __init__.py
│   ├── claude/
│   │   ├── agents/
│   │   │   ├── dev.md        # DEV Claude agent template
│   │   │   ├── auditor.md    # AUDITOR Claude agent template
│   │   │   └── dispatcher.md # DISPATCHER Claude agent template
│   │   ├── commands/
│   │   │   ├── status.md     # /status slash command template
│   │   │   ├── workflow.md   # /workflow slash command template
│   │   │   ├── validate.md   # /validate slash command template
│   │   │   └── agent.md      # /agent slash command template
│   │   └── CLAUDE.md         # Main Claude Code context template
│   └── synapse/
│       ├── config.yaml       # Synapse workflow configuration
│       └── task_log.json     # Task log template
├── models/
│   ├── __init__.py
│   ├── task.py          # Task and workflow models
│   └── project.py       # Project configuration models
└── services/
    ├── __init__.py
    ├── scaffolder.py    # Project scaffolding service
    └── validator.py     # Template validation service

tests/
├── cli/
│   └── test_init_command.py        # Only test for "synapse init"
├── integration/
│   ├── test_project_scaffolding.py
│   └── test_claude_integration.py
└── unit/
    ├── test_models/
    ├── test_services/
    └── test_templates/
```

**Structure Decision**: Minimal global CLI package with only `synapse init` command. This scaffolds:
- `.claude/agents/` - Claude Code agent definitions
- `.claude/commands/` - Claude Code slash commands (status, workflow, validate, agent)
- `.synapse/` - Workflow state and logging
- `CLAUDE.md` - Main Claude Code context file

**No other CLI commands needed** - all functionality accessed via Claude Code slash commands.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh claude`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each CLI command contract → contract test task [P]
- Each data model entity → model class task [P]
- Each template type → template creation task [P]
- CLI implementation tasks to make contract tests pass
- Integration scenarios from quickstart guide

**Specific Tasks to Generate**:
1. **Contract Tests (1 task)**: Only "synapse init" CLI command contract
2. **Data Models (6 tasks)**: Core entity classes from data-model.md
3. **Template Files (8 tasks)**: Agent templates (3) + slash command templates (4) + CLAUDE.md
4. **CLI Implementation (2 tasks)**: Single init command with Click framework
5. **Services (2 tasks)**: Scaffolder service and template validation
6. **Integration Tests (3 tasks)**: End-to-end init workflow scenarios
7. **Package Setup (3 tasks)**: pyproject.toml, setup.py, distribution

**Ordering Strategy**:
- TDD order: Contract test → Models → Templates → Services → CLI → Integration
- Template tasks can run in parallel with model tasks [P]
- CLI depends only on scaffolder service (minimal implementation)
- Integration tests validate complete init workflow and template scaffolding

**Estimated Output**: 25-30 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


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
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
