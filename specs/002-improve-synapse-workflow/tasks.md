# Tasks: Synapse Workflow UX Improvements

**Input**: Design documents from `/Users/alexabrams/Workspace/synapse/specs/002-improve-synapse-workflow/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Extract: Python 3.11+ + Click (CLI), PyYAML (config), Jinja2 (templating), pathlib (file operations)
   → Structure: Single project modification (existing synapse/ codebase)
2. Load design documents:
   → data-model.md: 6 core entities (TemplateConfig, ContentSlot, CommandRegistry, SlashCommand, IntegrationStrategy, ConflictInfo)
   → contracts/: 2 contract files (CLI template integration, service APIs)
   → research.md: Jinja2 templating, conflict detection, content preservation decisions
   → quickstart.md: 4 main scenarios (fresh setup, existing project, agent communication, migration)
3. Generate tasks by category:
   → Setup: Dependencies, configuration, enhanced CLI structure
   → Tests: Contract tests, template integration tests, command installation tests
   → Core: Template models, integration service, command registry, enhanced CLI
   → Integration: Template system, conflict detection, slash command installation
   → Polish: Unit tests, performance validation, documentation
4. Apply task rules:
   → Template files = [P] parallel (different files)
   → Model files = [P] parallel (different entities)
   → CLI commands = sequential (shared main.py modifications)
5. TDD order: Contract tests → Models → Services → CLI enhancements → Integration
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## ⚠️ CRITICAL COMPLETION REQUIREMENTS
**EVERY TASK MUST MEET ALL OF THE FOLLOWING BEFORE BEING MARKED COMPLETE:**

1. **✅ ALL TESTS PASS** - Zero test failures allowed: `pytest`
2. **✅ LINTING PASSES** - Zero linting errors allowed: `ruff check .`
3. **✅ TYPE CHECKING PASSES** - Zero type errors allowed: `mypy synapse/`
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

# 5. Enhanced CLI verification (after CLI tasks)
python -m synapse --help  # Should work
python -m synapse init --help  # Should show enhanced options
```

**If ANY command above fails, the task is NOT complete.**

## Path Conventions
- **Single project**: `synapse/`, `tests/` at repository root
- Enhanced existing CLI package structure per plan.md

## Phase 3.1: Setup
- [x] T001 Update Python dependencies with Jinja2 templating support in pyproject.toml **→ MUST: pytest runs, ruff check passes, mypy configured**
- [x] T002 [P] Configure enhanced linting rules for template integration in pyproject.toml **→ MUST: ruff check . passes with new rules**
- [x] T003 [P] Add development scripts for template testing in scripts/ directory **→ MUST: scripts executable, pytest passes**

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T004 [P] Contract test for enhanced "synapse init" with template integration in tests/cli/test_init_template_integration.py **→ MUST: Test fails (ImportError/NotImplemented), ruff+mypy pass**
- [x] T005 [P] Contract test for template integration service API in tests/integration/test_template_service.py **→ MUST: Test fails, ruff+mypy pass**
- [x] T006 [P] Contract test for command conflict detection in tests/cli/test_command_conflicts.py **→ MUST: Test fails, ruff+mypy pass**
- [x] T007 [P] Integration test for CLAUDE.md preservation scenario in tests/integration/test_claude_preservation.py **→ MUST: Test fails, ruff+mypy pass**
- [x] T008 [P] Integration test for slash command installation workflow in tests/integration/test_slash_commands.py **→ MUST: Test fails, ruff+mypy pass**

## Phase 3.3: Core Models (ONLY after tests are failing)
- [x] T009 [P] TemplateConfig model in synapse/models/template.py **→ MUST: pytest passes, ruff+mypy pass, proper type annotations**
- [x] T010 [P] ContentSlot model in synapse/models/template.py **→ MUST: pytest passes, ruff+mypy pass, proper type annotations**
- [x] T011 [P] CommandRegistry model in synapse/models/command.py **→ MUST: pytest passes, ruff+mypy pass, proper type annotations**
- [x] T012 [P] SlashCommand model in synapse/models/command.py **→ MUST: pytest passes, ruff+mypy pass, proper type annotations**
- [x] T013 [P] IntegrationStrategy model in synapse/models/template.py **→ MUST: pytest passes, ruff+mypy pass, proper type annotations**
- [x] T014 [P] ConflictInfo model in synapse/models/command.py **→ MUST: pytest passes, ruff+mypy pass, proper type annotations**

## Phase 3.4: Template System
- [x] T015 [P] Jinja2 CLAUDE.md template file in synapse/templates/claude/CLAUDE.md.j2 **→ MUST: pytest passes, ruff+mypy pass, template validation**
- [x] T016 [P] Synapse plan command template in synapse/templates/claude/commands/synapse-plan.md **→ MUST: pytest passes, ruff+mypy pass, template validation**
- [x] T017 [P] Synapse implement command template in synapse/templates/claude/commands/synapse-implement.md **→ MUST: pytest passes, ruff+mypy pass, template validation**
- [x] T018 [P] Synapse review command template in synapse/templates/claude/commands/synapse-review.md **→ MUST: pytest passes, ruff+mypy pass, template validation**
- [x] T019 [P] Synapse dev command template in synapse/templates/claude/commands/synapse-dev.md **→ MUST: pytest passes, ruff+mypy pass, template validation**
- [x] T020 [P] Synapse audit command template in synapse/templates/claude/commands/synapse-audit.md **→ MUST: pytest passes, ruff+mypy pass, template validation**
- [x] T021 [P] Synapse dispatch command template in synapse/templates/claude/commands/synapse-dispatch.md **→ MUST: pytest passes, ruff+mypy pass, template validation**

## Phase 3.5: Services
- [x] T022 Template integration service in synapse/services/integrator.py **→ MUST: pytest passes, ruff+mypy pass, proper type annotations**
- [x] T023 Command conflict detection utility in synapse/utils/conflicts.py **→ MUST: pytest passes, ruff+mypy pass, proper type annotations**
- [x] T024 Enhanced template validation service in synapse/services/validator.py **→ MUST: pytest passes, ruff+mypy pass, proper type annotations**

## Phase 3.6: CLI Implementation
- [x] T025 Enhanced "synapse init" command with template integration in synapse/cli/init.py **→ MUST: pytest passes, ruff+mypy pass, CLI contract tests pass**
- [x] T026 New command registration system in synapse/cli/commands.py **→ MUST: pytest passes, ruff+mypy pass, CLI contract tests pass**
- [x] T027 Template management CLI commands in synapse/cli/template.py **→ MUST: pytest passes, ruff+mypy pass, CLI contract tests pass**

## Phase 3.7: Enhanced Project Configuration
- [x] T028 Enhanced project config with template settings in synapse/models/project.py **→ MUST: pytest passes, ruff+mypy pass, backward compatibility maintained**
- [x] T029 Enhanced scaffolder service with template integration in synapse/services/scaffolder.py **→ MUST: pytest passes, ruff+mypy pass, existing functionality preserved**

## Phase 3.8: Integration & Workflow
- [x] T030 Connect template integration to enhanced init command **→ MUST: ALL tests pass, ruff+mypy pass, template integration working**
- [x] T031 Connect command conflict detection to command installation **→ MUST: ALL tests pass, ruff+mypy pass, conflict detection working**
- [x] T032 Implement CLAUDE.md backup and restoration system **→ MUST: ALL tests pass, ruff+mypy pass, backup/restore functional**
- [x] T033 Performance optimization for template processing **→ MUST: <500ms template integration, ALL tests pass, ruff+mypy pass**

## Phase 3.9: Polish & Validation
- [x] T034 [P] Unit tests for template models in tests/unit/test_template_models.py **→ MUST: 100% test coverage, ALL tests pass, ruff+mypy pass**
- [x] T035 [P] Unit tests for command models in tests/unit/test_command_models.py **→ MUST: 100% test coverage, ALL tests pass, ruff+mypy pass**
- [x] T036 [P] Unit tests for integration service in tests/unit/test_integrator.py **→ MUST: 100% test coverage, ALL tests pass, ruff+mypy pass**
- [x] T037 [P] Unit tests for conflict detection in tests/unit/test_conflicts.py **→ MUST: 100% test coverage, ALL tests pass, ruff+mypy pass**
- [x] T038 Performance validation (<500ms init, <1s command registration) **→ MUST: Performance benchmarks met, ALL tests pass, ruff+mypy pass**
- [x] T039 End-to-end quickstart scenario validation **→ MUST: ALL quickstart scenarios pass, ALL tests pass, ruff+mypy pass**
- [x] T040 Enhanced documentation for new UX features **→ MUST: Documentation complete, ALL tests pass, ruff+mypy pass**

## Dependencies
- Setup (T001-T003) before everything
- Tests (T004-T008) before implementation (T009+)
- Models (T009-T014) before services (T022-T024)
- Templates (T015-T021) can run parallel with models
- Services (T022-T024) before CLI (T025-T027)
- CLI (T025-T027) before integration (T030-T033)
- Core implementation before polish (T034-T040)

## Parallel Execution Examples

### Setup Phase (after T001-T003)
```
# Launch all test tasks together:
Task: "Contract test for enhanced synapse init with template integration in tests/cli/test_init_template_integration.py"
Task: "Contract test for template integration service API in tests/integration/test_template_service.py"
Task: "Contract test for command conflict detection in tests/cli/test_command_conflicts.py"
Task: "Integration test for CLAUDE.md preservation in tests/integration/test_claude_preservation.py"
Task: "Integration test for slash command installation in tests/integration/test_slash_commands.py"
```

### Model + Template Phase (after tests fail)
```
# Launch model tasks:
Task: "TemplateConfig model in synapse/models/template.py"
Task: "CommandRegistry model in synapse/models/command.py"
Task: "SlashCommand model in synapse/models/command.py"

# Parallel with template tasks:
Task: "Jinja2 CLAUDE.md template file in synapse/templates/claude/CLAUDE.md.j2"
Task: "Synapse plan command template in synapse/templates/claude/commands/synapse-plan.md"
Task: "Synapse implement command template in synapse/templates/claude/commands/synapse-implement.md"
```

### Polish Phase
```
# Launch all unit test tasks:
Task: "Unit tests for template models in tests/unit/test_template_models.py"
Task: "Unit tests for command models in tests/unit/test_command_models.py"
Task: "Unit tests for integration service in tests/unit/test_integrator.py"
Task: "Unit tests for conflict detection in tests/unit/test_conflicts.py"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify CLI contract tests fail before implementing CLI enhancements
- Template files are independent and can be created in parallel
- Model classes can be in same file but different entities
- Each template serves different slash command functionality
- Enhanced CLI preserves existing functionality while adding new capabilities

## 🚨 CRITICAL QUALITY GATES - READ BEFORE STARTING
1. **ZERO TOLERANCE POLICY**: No task is complete until ALL quality checks pass
2. **TDD MANDATORY**: Tests must be written first and must fail before implementation
3. **TYPE SAFETY REQUIRED**: Every function, class, and variable must have proper type annotations
4. **DOCUMENTATION REQUIRED**: All public APIs must have docstrings following Google style
5. **PERFORMANCE REQUIREMENTS**: Must meet specified performance benchmarks
6. **BACKWARD COMPATIBILITY**: Existing Synapse functionality must be preserved
7. **NO SHORTCUTS**: Cutting corners on quality is UNACCEPTABLE and will require rework

**Remember: High-quality, thoroughly tested, well-typed code with seamless UX integration is the ONLY acceptable outcome.**

## Task Generation Rules Applied

1. **From Contracts**:
   - cli-template-integration.yaml → T004, T006 CLI contract tests
   - template-integration-service.yaml → T005 service contract test

2. **From Data Model**:
   - 6 entities → T009-T014 model creation tasks (can share files by entity type)
   - TemplateConfig, ContentSlot, CommandRegistry, SlashCommand, IntegrationStrategy, ConflictInfo

3. **From Plan Architecture**:
   - 6 slash command templates → T016-T021 template tasks [P]
   - 1 main CLAUDE.md template → T015 template task [P]
   - 3 enhanced services → T022-T024 service implementation
   - 3 CLI enhancements → T025-T027 CLI implementation

4. **From Quickstart Scenarios**:
   - 4 scenarios → T007-T008 integration tests + T039 end-to-end validation
   - Performance requirements → T038 performance validation

## Validation Checklist
*GATE: All items verified before task execution*

- [x] All CLI contracts have corresponding tests (T004, T006)
- [x] All service contracts have corresponding tests (T005)
- [x] All 6 entities have model tasks (T009-T014)
- [x] All tests come before implementation (T004-T008 before T009+)
- [x] Parallel tasks truly independent (different files marked [P])
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] TDD order maintained (tests → models → services → CLI → integration)
- [x] Template files can be created independently in parallel
- [x] Enhanced CLI preserves existing functionality while adding new capabilities
- [x] Quality verification built into every task completion requirement