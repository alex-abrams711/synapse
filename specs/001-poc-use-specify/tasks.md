# Tasks: Synapse Agent Workflow System POC

**Input**: Design documents from `/specs/001-poc-use-specify/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Extract: Python 3.11+ + Click (CLI), JSON (persistence), pathlib (file operations)
   → Structure: Global CLI package with project template scaffolding
2. Load design documents:
   → data-model.md: 7 core entities (AgentTemplate, ProjectConfig, Task, etc.)
   → contracts/: 1 CLI command contract (synapse init only)
   → research.md: Click framework, template-based scaffolding decisions
3. Generate tasks by category:
   → Setup: Python package, dependencies, linting
   → Tests: CLI contract test, template validation tests
   → Core: models, services, CLI implementation, templates
   → Integration: scaffolding workflow, template installation
   → Polish: unit tests, distribution setup
4. Apply task rules:
   → Template files = [P] parallel (different files)
   → Model files = [P] parallel (different files)
   → CLI depends on services (sequential)
5. TDD order: Contract test → Models → Templates → Services → CLI → Integration
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## ⚠️ CRITICAL COMPLETION REQUIREMENTS
**EVERY TASK MUST MEET ALL OF THE FOLLOWING BEFORE BEING MARKED COMPLETE:**

1. **✅ ALL TESTS PASS** - Zero test failures allowed
2. **✅ LINTING PASSES** - `ruff check .` must return zero errors
3. **✅ TYPE CHECKING PASSES** - `mypy synapse/` must return zero errors
4. **✅ CODE QUALITY** - No TODO comments, proper documentation, clean implementation

**UNACCEPTABLE TO MARK TASK COMPLETE IF ANY OF THE ABOVE FAIL**

Commands to run after EVERY task:
```bash
# MUST pass before task completion
pytest                # ← ZERO failures allowed
ruff check .          # ← ZERO errors allowed
mypy synapse/         # ← ZERO type errors allowed
```

## 🚨 TASK COMPLETION VERIFICATION PROTOCOL
Before marking ANY task complete, run this verification sequence:

```bash
# 1. Clean install/setup verification
pip install -e .

# 2. Test verification (MUST be zero failures)
pytest -v
echo "Exit code: $?" # Must be 0

# 3. Linting verification (MUST be zero errors)
ruff check .
echo "Exit code: $?" # Must be 0

# 4. Type checking verification (MUST be zero errors)
mypy synapse/
echo "Exit code: $?" # Must be 0

# 5. Final integration check
python -m synapse --help  # Should work after CLI tasks
```

**If ANY command above fails, the task is NOT complete.**

## Path Conventions
- **Single project**: `synapse/`, `tests/` at repository root
- Global CLI package structure per plan.md

## Phase 3.1: Setup
- [ ] T001 Create Python package structure (synapse/__init__.py, pyproject.toml, setup.py) **→ MUST: ruff check . passes**
- [ ] T002 Initialize Python project with Click dependencies in pyproject.toml **→ MUST: pytest runs, mypy configured**
- [ ] T003 [P] Configure pytest, ruff linting, mypy type checking tools in pyproject.toml **→ MUST: All linting/typing tools functional**

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [ ] T004 CLI contract test for "synapse init" command in tests/cli/test_init_command.py **→ MUST: Test fails (ImportError/NotImplemented), ruff+mypy pass**
- [ ] T005 [P] Template validation test in tests/unit/test_templates/test_agent_templates.py **→ MUST: Test fails, ruff+mypy pass**
- [ ] T006 [P] Project scaffolding integration test in tests/integration/test_project_scaffolding.py **→ MUST: Test fails, ruff+mypy pass**
- [ ] T007 [P] Claude Code integration test in tests/integration/test_claude_integration.py **→ MUST: Test fails, ruff+mypy pass**

## Phase 3.3: Core Models (ONLY after tests are failing)
- [ ] T008 [P] AgentTemplate model in synapse/models/task.py **→ MUST: pytest passes, ruff+mypy pass, proper type annotations**
- [ ] T009 [P] ProjectConfig model in synapse/models/project.py **→ MUST: pytest passes, ruff+mypy pass, proper type annotations**
- [ ] T010 [P] Task and Subtask models in synapse/models/task.py **→ MUST: pytest passes, ruff+mypy pass, proper type annotations**
- [ ] T011 [P] WorkflowState model in synapse/models/task.py **→ MUST: pytest passes, ruff+mypy pass, proper type annotations**
- [ ] T012 [P] TaskLogEntry model in synapse/models/task.py **→ MUST: pytest passes, ruff+mypy pass, proper type annotations**
- [ ] T013 [P] VerificationReport and Finding models in synapse/models/task.py **→ MUST: pytest passes, ruff+mypy pass, proper type annotations**

## Phase 3.4: Template Files (parallel with models)
- [ ] T014 [P] DEV Claude agent template in synapse/templates/claude/agents/dev.md **→ MUST: pytest passes, ruff+mypy pass, template validation**
- [ ] T015 [P] AUDITOR Claude agent template in synapse/templates/claude/agents/auditor.md **→ MUST: pytest passes, ruff+mypy pass, template validation**
- [ ] T016 [P] DISPATCHER Claude agent template in synapse/templates/claude/agents/dispatcher.md **→ MUST: pytest passes, ruff+mypy pass, template validation**
- [ ] T017 [P] /status slash command template in synapse/templates/claude/commands/status.md **→ MUST: pytest passes, ruff+mypy pass, template validation**
- [ ] T018 [P] /workflow slash command template in synapse/templates/claude/commands/workflow.md **→ MUST: pytest passes, ruff+mypy pass, template validation**
- [ ] T019 [P] /validate slash command template in synapse/templates/claude/commands/validate.md **→ MUST: pytest passes, ruff+mypy pass, template validation**
- [ ] T020 [P] /agent slash command template in synapse/templates/claude/commands/agent.md **→ MUST: pytest passes, ruff+mypy pass, template validation**
- [ ] T021 [P] Main CLAUDE.md context template in synapse/templates/claude/CLAUDE.md **→ MUST: pytest passes, ruff+mypy pass, template validation**

## Phase 3.5: Services
- [ ] T022 Project scaffolder service in synapse/services/scaffolder.py **→ MUST: pytest passes, ruff+mypy pass, proper type annotations**
- [ ] T023 Template validation service in synapse/services/validator.py **→ MUST: pytest passes, ruff+mypy pass, proper type annotations**

## Phase 3.6: CLI Implementation
- [ ] T024 Click CLI entry point in synapse/cli/main.py **→ MUST: pytest passes, ruff+mypy pass, CLI contract tests pass**
- [ ] T025 "synapse init" command implementation in synapse/cli/init.py **→ MUST: pytest passes, ruff+mypy pass, CLI contract tests pass**

## Phase 3.7: Configuration Templates
- [ ] T026 [P] Synapse workflow config template in synapse/templates/synapse/config.yaml **→ MUST: pytest passes, ruff+mypy pass, template validation**
- [ ] T027 [P] Task log JSON template in synapse/templates/synapse/task_log.json **→ MUST: pytest passes, ruff+mypy pass, template validation**

## Phase 3.8: Integration & Package Setup
- [ ] T028 Connect CLI to scaffolder service and make contract tests pass **→ MUST: ALL tests pass, ruff+mypy pass, integration working**
- [ ] T029 Entry point configuration for global "synapse" command **→ MUST: ALL tests pass, ruff+mypy pass, CLI globally available**
- [ ] T030 Package distribution setup (pyproject.toml [project.scripts]) **→ MUST: ALL tests pass, ruff+mypy pass, package installable**

## Phase 3.9: Polish
- [ ] T031 [P] Unit tests for models in tests/unit/test_models/ **→ MUST: 100% test coverage, ALL tests pass, ruff+mypy pass**
- [ ] T032 [P] Unit tests for services in tests/unit/test_services/ **→ MUST: 100% test coverage, ALL tests pass, ruff+mypy pass**
- [ ] T033 [P] Template content validation tests in tests/unit/test_templates/ **→ MUST: 100% test coverage, ALL tests pass, ruff+mypy pass**
- [ ] T034 Performance validation (<1s init, <500ms agent communication) **→ MUST: ALL tests pass, ruff+mypy pass, performance benchmarks met**
- [ ] T035 End-to-end quickstart scenario validation **→ MUST: ALL tests pass, ruff+mypy pass, complete workflow functional**

## Dependencies
- Setup (T001-T003) before everything
- Tests (T004-T007) before implementation (T008+)
- Models (T008-T013) before services (T022-T023)
- Templates (T014-T027) can run parallel with models
- Services (T022-T023) before CLI (T024-T025)
- CLI (T024-T025) before integration (T028-T030)
- Core implementation before polish (T031-T035)

## Parallel Execution Examples

### Setup Phase (after T001-T003)
```
# Launch all test tasks together:
Task: "CLI contract test for synapse init in tests/cli/test_init_command.py"
Task: "Template validation test in tests/unit/test_templates/test_agent_templates.py"
Task: "Project scaffolding integration test in tests/integration/test_project_scaffolding.py"
Task: "Claude Code integration test in tests/integration/test_claude_integration.py"
```

### Model + Template Phase (after tests fail)
```
# Launch model tasks:
Task: "AgentTemplate model in synapse/models/task.py"
Task: "ProjectConfig model in synapse/models/project.py"
Task: "Task and Subtask models in synapse/models/task.py"

# Parallel with template tasks:
Task: "DEV Claude agent template in synapse/templates/claude/agents/dev.md"
Task: "AUDITOR Claude agent template in synapse/templates/claude/agents/auditor.md"
Task: "/status slash command template in synapse/templates/claude/commands/status.md"
```

### Polish Phase
```
# Launch all unit test tasks:
Task: "Unit tests for models in tests/unit/test_models/"
Task: "Unit tests for services in tests/unit/test_services/"
Task: "Template content validation tests in tests/unit/test_templates/"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify CLI contract test fails before implementing CLI
- Template files are independent and can be created in parallel
- Model classes can be in same file but different entities
- Each template serves different Claude Code functionality
- Global installation requires proper entry point configuration

## 🚨 CRITICAL QUALITY GATES - READ BEFORE STARTING
1. **ZERO TOLERANCE POLICY**: No task is complete until ALL quality checks pass
2. **TDD MANDATORY**: Tests must be written first and must fail before implementation
3. **TYPE SAFETY REQUIRED**: Every function, class, and variable must have proper type annotations
4. **DOCUMENTATION REQUIRED**: All public APIs must have docstrings following Google style
5. **PERFORMANCE REQUIREMENTS**: Must meet specified performance benchmarks
6. **NO SHORTCUTS**: Cutting corners on quality is UNACCEPTABLE and will require rework

**Remember: High-quality, thoroughly tested, well-typed code is the ONLY acceptable outcome.**

## Task Generation Rules Applied

1. **From Contracts**:
   - cli-commands.yaml → T004 CLI contract test for "synapse init"
   - Only one CLI command per design (other functionality via Claude slash commands)

2. **From Data Model**:
   - 7 entities → T008-T013 model creation tasks (can share files)
   - AgentTemplate, ProjectConfig, Task, Subtask, WorkflowState, TaskLogEntry, VerificationReport

3. **From Plan Architecture**:
   - 3 Claude agents → T014-T016 agent template tasks [P]
   - 4 slash commands → T017-T020 command template tasks [P]
   - 1 main context → T021 CLAUDE.md template [P]
   - 2 services → T022-T023 service implementation
   - 2 config templates → T026-T027 configuration files [P]

4. **From Research Decisions**:
   - Click framework → T002 dependency setup, T024-T025 CLI implementation
   - Template-based scaffolding → T022 scaffolder service, T014-T027 template files
   - PyPI distribution → T029-T030 package setup

## Validation Checklist
*GATE: All items verified before task execution*

- [x] CLI contract (synapse init) has corresponding test (T004)
- [x] All 7 entities have model tasks (T008-T013)
- [x] All tests come before implementation (T004-T007 before T008+)
- [x] Parallel tasks truly independent (different files marked [P])
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] TDD order maintained (tests → models → services → CLI → integration)
- [x] Template files can be created independently in parallel
- [x] Package structure supports global CLI installation