# Implementation Tasks

**Change ID**: `implement-synapse-cli-system`
**Last Updated**: 2025-10-20

This document breaks down the implementation into ordered, verifiable tasks that deliver user-visible progress.

---

## Phase 1: Project Foundation (Days 1-2)

### Task 1.1: Create Project Structure
**Est**: 2 hours | **Dependencies**: None | **Deliverable**: Basic project skeleton

**Steps**:
1. Create directory structure:
   ```
   synapse/
   ├── src/synapse_cli/
   │   ├── __init__.py
   │   └── __main__.py
   ├── resources/
   │   ├── commands/synapse/
   │   ├── settings/
   │   └── workflows/
   ├── tests/
   └── pyproject.toml
   ```
2. Create initial `pyproject.toml` with metadata
3. Create `MANIFEST.in` for resource packaging
4. Create `.gitignore` for Python project

**Validation**:
- [ ] Directory structure matches design
- [ ] `pyproject.toml` has correct package name and version
- [ ] Can run `pip install -e .` successfully

---

### Task 1.2: Implement CLI Entry Point
**Est**: 2 hours | **Dependencies**: 1.1 | **Deliverable**: Working CLI with --help

**Steps**:
1. Implement `main()` function in `__init__.py`
2. Set up argparse with top-level parser
3. Add `--version` and `--help` options
4. Configure setuptools entry point in `pyproject.toml`
5. Add basic error handling with exit codes

**Validation**:
- [ ] `synapse --help` displays help message
- [ ] `synapse --version` displays version
- [ ] Unknown commands show error and suggest --help
- [ ] Exit codes follow specification (0=success, 1=user error)

---

### Task 1.3: Implement Resource Discovery
**Est**: 2 hours | **Dependencies**: 1.1 | **Deliverable**: Can locate packaged resources

**Steps**:
1. Implement `get_resources_dir()` using `pkg_resources`
2. Add fallback to `importlib.resources` for Python 3.9+
3. Test in both editable and installed modes
4. Add error handling for missing resources

**Validation**:
- [ ] Can locate resources in editable install (`pip install -e .`)
- [ ] Can locate resources in regular install
- [ ] Raises clear error if resources missing
- [ ] Unit tests for resource discovery pass

---

### Task 1.4: Implement Init Command
**Est**: 3 hours | **Dependencies**: 1.2, 1.3 | **Deliverable**: `synapse init` works

**Steps**:
1. Add `init` subparser to argparse
2. Implement `.synapse/` directory creation
3. Create initial `config.json` with schema
4. Copy `sense.md` to `.synapse/commands/synapse/`
5. Add validation for existing initialization
6. Display success message with next steps

**Validation**:
- [ ] `synapse init` creates `.synapse/` directory
- [ ] `config.json` has correct schema and metadata
- [ ] Running `synapse init` twice shows warning
- [ ] Integration test for init command passes

---

## Phase 2: File Operations & Settings (Days 3-4)

### Task 2.1: Implement File Copying Functions
**Est**: 4 hours | **Dependencies**: 1.3 | **Deliverable**: Can copy workflow files

**Steps**:
1. Implement `copy_workflow_files(workflow_name, force)` function
2. Add logic to copy agents/, hooks/, commands/ subdirectories
3. Implement file conflict detection
4. Add `--force` flag handling
5. Track copied files for manifest

**Validation**:
- [ ] Copies all files from workflow to `.claude/`
- [ ] Skips existing files without --force
- [ ] Overwrites files with --force
- [ ] Returns list of copied files for tracking
- [ ] Unit tests for file operations pass

---

### Task 2.2: Implement Permission Management
**Est**: 2 hours | **Dependencies**: 2.1 | **Deliverable**: Shell scripts are executable

**Steps**:
1. Implement `make_executable(file_path)` function
2. Add logic to detect `.sh` files
3. Use `os.chmod()` with appropriate permissions
4. Handle permission errors gracefully

**Validation**:
- [ ] `.sh` files in `.claude/hooks/` are executable
- [ ] Other files retain normal permissions
- [ ] Permission errors are caught and reported
- [ ] Works on Unix/Mac and Windows

---

### Task 2.3: Implement Settings Merge
**Est**: 4 hours | **Dependencies**: None (parallelizable) | **Deliverable**: Settings merge works

**Steps**:
1. Implement `deep_merge(base, overlay)` function
2. Add special handling for array appending (hooks)
3. Implement JSON validation before/after merge
4. Add atomic write with temp file + rename
5. Track which settings sections were modified

**Validation**:
- [ ] Merges nested objects correctly
- [ ] Appends to arrays instead of replacing
- [ ] Preserves existing settings
- [ ] Validates JSON structure
- [ ] Unit tests for merge logic pass (including edge cases)

---

### Task 2.4: Implement Backup System
**Est**: 3 hours | **Dependencies**: None (parallelizable) | **Deliverable**: Backup/restore works

**Steps**:
1. Implement `create_backup()` function with timestamp
2. Add recursive directory copy for `.claude/`
3. Implement `restore_backup(backup_path)` function
4. Add `list_backups()` for status reporting
5. Preserve file permissions in backup/restore

**Validation**:
- [ ] Creates timestamped backup in `.synapse/backups/`
- [ ] Backup includes all `.claude/` contents
- [ ] Restore completely replaces `.claude/` from backup
- [ ] File permissions preserved
- [ ] Integration tests for backup/restore pass

---

### Task 2.5: Implement State Tracking
**Est**: 3 hours | **Dependencies**: 2.1, 2.3 | **Deliverable**: Manifest and config updates

**Steps**:
1. Implement `create_manifest()` function
2. Design manifest schema matching spec
3. Implement config.json update functions
4. Add `get_active_workflow()` helper
5. Implement atomic writes for both files

**Validation**:
- [ ] Manifest includes all copied files
- [ ] Manifest tracks hooks added
- [ ] Config.json updated with active workflow
- [ ] Both files written atomically
- [ ] Unit tests for state tracking pass

---

## Phase 3: Workflow Commands (Days 5-6)

### Task 3.1: Implement Workflow List Command
**Est**: 2 hours | **Dependencies**: 1.3 | **Deliverable**: `synapse workflow list` works

**Steps**:
1. Add `workflow` subparser with `list` action
2. Scan `resources/workflows/` directory
3. Format and display workflow names
4. Show active workflow indicator

**Validation**:
- [ ] Displays "feature-planning" and "feature-implementation"
- [ ] Shows which workflow is active (if any)
- [ ] Handles missing workflows directory gracefully

---

### Task 3.2: Implement Workflow Status Command
**Est**: 2 hours | **Dependencies**: 2.5 | **Deliverable**: `synapse workflow status` works

**Steps**:
1. Add `status` action to workflow subparser
2. Read config.json and manifest.json
3. Display active workflow information
4. Show file count, hook count, backup status

**Validation**:
- [ ] Displays active workflow name
- [ ] Shows number of managed files
- [ ] Shows number of configured hooks
- [ ] Handles no active workflow gracefully

---

### Task 3.3: Implement Workflow Apply Command
**Est**: 4 hours | **Dependencies**: 2.1-2.5 | **Deliverable**: Can apply workflows

**Steps**:
1. Add workflow name as positional argument
2. Add `--force` flag to workflow subparser
3. Orchestrate workflow application:
   - Validate workflow exists
   - Create backup
   - Copy files
   - Merge settings
   - Update state
4. Report success with details
5. Rollback on any failure

**Validation**:
- [ ] `synapse workflow feature-planning` applies workflow
- [ ] All files copied to `.claude/`
- [ ] Settings merged correctly
- [ ] Manifest and config updated
- [ ] Backup created before changes
- [ ] Integration test for apply passes

---

### Task 3.4: Implement Workflow Remove Command
**Est**: 3 hours | **Dependencies**: 2.4, 2.5, 3.3 | **Deliverable**: Can remove workflows

**Steps**:
1. Add `remove` action to workflow subparser
2. Implement workflow removal logic:
   - Verify active workflow exists
   - Restore from latest backup
   - Clear state from config.json
   - Delete manifest.json
3. Add user confirmation prompt
4. Report removed files

**Validation**:
- [ ] `synapse workflow remove` restores from backup
- [ ] `.claude/` directory restored to pre-workflow state
- [ ] Config.json cleared
- [ ] Manifest.json deleted
- [ ] Integration test for remove passes

---

## Phase 4: Feature Planning Workflow (Days 7-8)

### Task 4.1: Create Task Writer Agent
**Est**: 3 hours | **Dependencies**: None (content creation) | **Deliverable**: task-writer.md

**Steps**:
1. Write agent markdown file with:
   - Agent purpose and behavior
   - Task structure requirements
   - Quality standards reminder
   - Verification subtask format
2. Include examples of properly formatted tasks
3. Place in `resources/workflows/feature-planning/agents/`

**Validation**:
- [ ] Agent markdown file is well-formatted
- [ ] Instructions are clear and actionable
- [ ] Examples demonstrate all required elements
- [ ] File included in package resources

---

### Task 4.2: Create User Prompt Reminder Hook
**Est**: 1 hour | **Dependencies**: None (content creation) | **Deliverable**: reminder hook script

**Steps**:
1. Write bash script for UserPromptSubmit hook
2. Add shebang and simple echo statement
3. Make script executable
4. Place in `resources/workflows/feature-planning/hooks/`

**Validation**:
- [ ] Script has valid shebang
- [ ] Outputs helpful reminder message
- [ ] Script is executable
- [ ] File included in package resources

---

### Task 4.3: Create Planning Workflow Settings
**Est**: 1 hour | **Dependencies**: None (content creation) | **Deliverable**: settings.json

**Steps**:
1. Create settings.json with UserPromptSubmit hook configuration
2. Validate JSON structure
3. Place in `resources/workflows/feature-planning/`

**Validation**:
- [ ] Valid JSON structure
- [ ] Hook configuration matches spec
- [ ] File included in package resources

---

### Task 4.4: Test Feature Planning Workflow E2E
**Est**: 2 hours | **Dependencies**: 3.3, 4.1-4.3 | **Deliverable**: Working planning workflow

**Steps**:
1. Apply feature-planning workflow in test project
2. Verify all files copied correctly
3. Verify settings merged correctly
4. Test hook execution in Claude Code
5. Verify task-writer agent is accessible
6. Test workflow removal

**Validation**:
- [ ] All workflow files present in `.claude/`
- [ ] Hook triggers on user prompt submission
- [ ] Task-writer agent available
- [ ] Settings.json correctly configured
- [ ] Workflow removal restores original state

---

## Phase 5: Sense Command (Day 8)

### Task 5.1: Implement Project Detection
**Est**: 3 hours | **Dependencies**: None (parallelizable) | **Deliverable**: Detects project type

**Steps**:
1. Implement functions to scan for config files
2. Detect language from file extensions
3. Identify framework/runtime
4. Detect package manager

**Validation**:
- [ ] Detects Python projects (pyproject.toml)
- [ ] Detects JavaScript projects (package.json)
- [ ] Identifies primary language correctly
- [ ] Unit tests for detection logic pass

---

### Task 5.2: Implement Quality Tool Detection
**Est**: 4 hours | **Dependencies**: 5.1 | **Deliverable**: Detects quality tools

**Steps**:
1. Implement linter detection (ruff, pylint, eslint, etc.)
2. Implement type checker detection (mypy, tsc, etc.)
3. Implement test runner detection (pytest, jest, etc.)
4. Implement coverage tool detection
5. Check both installed packages and config files

**Validation**:
- [ ] Detects Python tools (ruff, mypy, pytest, coverage)
- [ ] Detects JavaScript tools (eslint, jest, nyc)
- [ ] Returns tool names and commands
- [ ] Unit tests for each tool type pass

---

### Task 5.3: Implement Configuration Generation
**Est**: 2 hours | **Dependencies**: 5.2 | **Deliverable**: Generates quality config

**Steps**:
1. Implement quality_config schema creation
2. Map detected tools to configuration entries
3. Add default thresholds (e.g., 80% coverage)
4. Update `.synapse/config.json` atomically

**Validation**:
- [ ] Creates quality_config section in config.json
- [ ] Includes all detected tools
- [ ] Has reasonable defaults
- [ ] Config.json remains valid JSON

---

### Task 5.4: Create Sense Command Content
**Est**: 2 hours | **Dependencies**: None (content creation) | **Deliverable**: sense.md

**Steps**:
1. Write sense command markdown file
2. Document command behavior and usage
3. Include examples of output
4. Place in `resources/commands/synapse/`

**Validation**:
- [ ] Command documentation is clear
- [ ] Examples are accurate
- [ ] File included in both workflows
- [ ] Accessible as `/sense` in Claude Code

---

## Phase 6: Feature Implementation Workflow (Days 9-11)

### Task 6.1: Create Implementer Agent
**Est**: 4 hours | **Dependencies**: None (content creation) | **Deliverable**: implementer.md

**Steps**:
1. Write agent markdown with:
   - Minimal change philosophy
   - Quality gate requirements
   - Task completion criteria
   - Integration with hooks
2. Include workflow examples
3. Place in `resources/workflows/feature-implementation/agents/`

**Validation**:
- [ ] Agent instructions are clear and specific
- [ ] Quality gate enforcement is explicit
- [ ] Examples demonstrate minimal changes
- [ ] File included in package resources

---

### Task 6.2: Create Verifier Agent
**Est**: 4 hours | **Dependencies**: None (content creation) | **Deliverable**: verifier.md

**Steps**:
1. Write agent markdown with:
   - Comprehensive QA approach
   - Playwright integration instructions
   - Screenshot capture requirements
   - Dev/QA/User verification process
2. Include Playwright examples
3. Place in `resources/workflows/feature-implementation/agents/`

**Validation**:
- [ ] Agent instructions cover comprehensive testing
- [ ] Playwright usage is well-documented
- [ ] Verification checkpoints are clear
- [ ] File included in package resources

---

### Task 6.3: Create PreToolUse Hook (Python)
**Est**: 4 hours | **Dependencies**: None (content creation) | **Deliverable**: pretool gate hook

**Steps**:
1. Write Python script for task validation
2. Add PEP 723 inline dependencies (if needed)
3. Implement task status parsing logic
4. Add prerequisite checks
5. Exit with appropriate codes (0=allow, 1=block)
6. Place in `resources/workflows/feature-implementation/hooks/`

**Validation**:
- [ ] Script has PEP 723 metadata if needed
- [ ] Parses task files correctly
- [ ] Validates task readiness
- [ ] Exit codes work as specified
- [ ] Can execute with `uv run`

---

### Task 6.4: Create PostToolUse Quality Gate Hook (Python)
**Est**: 5 hours | **Dependencies**: 5.3 | **Deliverable**: quality gate hook

**Steps**:
1. Write Python script for quality checks
2. Add PEP 723 inline dependencies
3. Implement quality config loading from `.synapse/config.json`
4. Run linter, type checker, tests, coverage
5. Report results and exit with appropriate code
6. Place in `resources/workflows/feature-implementation/hooks/`

**Validation**:
- [ ] Loads quality config correctly
- [ ] Runs all configured quality tools
- [ ] Reports pass/fail for each tool
- [ ] Exits 0 if all pass, non-zero if any fail
- [ ] Can execute with `uv run`

---

### Task 6.5: Create Verification Completion Hook (Python)
**Est**: 3 hours | **Dependencies**: None (content creation) | **Deliverable**: completion hook

**Steps**:
1. Write Python script for verification tracking
2. Add PEP 723 inline dependencies (if needed)
3. Implement task status update logic
4. Update verification subtasks
5. Place in `resources/workflows/feature-implementation/hooks/`

**Validation**:
- [ ] Parses task files correctly
- [ ] Updates verification subtasks
- [ ] Marks tasks complete when appropriate
- [ ] Can execute with `uv run`

---

### Task 6.6: Create Implementation Workflow Settings
**Est**: 1 hour | **Dependencies**: None (content creation) | **Deliverable**: settings.json

**Steps**:
1. Create settings.json with all hook configurations
2. Configure UserPromptSubmit, PreToolUse, PostToolUse hooks
3. Use `uv run` for Python hooks
4. Validate JSON structure
5. Place in `resources/workflows/feature-implementation/`

**Validation**:
- [ ] Valid JSON structure
- [ ] All hooks configured correctly
- [ ] Python hooks use `uv run`
- [ ] File included in package resources

---

### Task 6.7: Test Feature Implementation Workflow E2E
**Est**: 4 hours | **Dependencies**: 3.3, 6.1-6.6 | **Deliverable**: Working implementation workflow

**Steps**:
1. Apply feature-implementation workflow in test project
2. Verify all files copied correctly
3. Verify settings merged correctly
4. Test all hooks execute correctly:
   - UserPromptSubmit reminder
   - PreToolUse validation
   - PostToolUse quality checks
   - Verification completion
5. Verify agents are accessible
6. Test with actual quality tools
7. Test workflow removal

**Validation**:
- [ ] All workflow files present in `.claude/`
- [ ] All hooks trigger at correct times
- [ ] Quality checks run and block when failing
- [ ] Implementer and verifier agents available
- [ ] Python hooks execute via uv successfully
- [ ] Workflow removal restores original state

---

## Phase 7: Testing & Polish (Days 12-13)

### Task 7.1: Write Comprehensive Unit Tests
**Est**: 6 hours | **Dependencies**: All implementation tasks | **Deliverable**: Unit test suite

**Steps**:
1. Write tests for resource discovery
2. Write tests for file operations (copy, permissions)
3. Write tests for settings merge algorithm
4. Write tests for backup/restore
5. Write tests for state tracking
6. Write tests for sense command detection logic
7. Achieve >80% code coverage

**Validation**:
- [ ] All unit tests pass
- [ ] Code coverage > 80%
- [ ] Edge cases covered
- [ ] Error paths tested

---

### Task 7.2: Write Integration Tests
**Est**: 6 hours | **Dependencies**: All implementation tasks | **Deliverable**: Integration test suite

**Steps**:
1. Write E2E test for init command
2. Write E2E test for workflow application
3. Write E2E test for workflow removal
4. Write E2E test for workflow switching
5. Write E2E test for settings merge
6. Write E2E test for backup/restore
7. Test in temporary directory with cleanup

**Validation**:
- [ ] All integration tests pass
- [ ] Tests run in isolated environments
- [ ] Tests clean up after themselves
- [ ] Both workflows tested end-to-end

---

### Task 7.3: Manual Testing in Real Project
**Est**: 3 hours | **Dependencies**: All implementation tasks | **Deliverable**: Verified in real usage

**Steps**:
1. Install Synapse in a real development project
2. Initialize Synapse
3. Apply feature-planning workflow
4. Verify Claude Code integration
5. Test task-writer agent
6. Apply feature-implementation workflow
7. Test implementer and verifier agents
8. Verify hooks execute correctly
9. Test workflow removal

**Validation**:
- [ ] All commands work in real project
- [ ] Claude Code recognizes agents
- [ ] Hooks execute at correct times
- [ ] Quality gates work with real tools
- [ ] No data loss during any operation

---

### Task 7.4: Documentation & README
**Est**: 3 hours | **Dependencies**: Manual testing complete | **Deliverable**: Complete documentation

**Steps**:
1. Write comprehensive README.md
2. Document installation instructions
3. Document all commands with examples
4. Document workflow contents and behavior
5. Add troubleshooting section
6. Create CHANGELOG.md

**Validation**:
- [ ] README covers all functionality
- [ ] Installation instructions are clear
- [ ] Examples are accurate and tested
- [ ] Troubleshooting addresses common issues

---

### Task 7.5: Package & Publish Preparation
**Est**: 2 hours | **Dependencies**: All tasks complete | **Deliverable**: Ready for PyPI

**Steps**:
1. Verify pyproject.toml completeness
2. Verify MANIFEST.in includes all resources
3. Build source distribution (sdist)
4. Build wheel distribution
5. Test installation from built distributions
6. Verify entry point works after install

**Validation**:
- [ ] `python -m build` succeeds
- [ ] Both sdist and wheel created
- [ ] Can install from wheel
- [ ] All resources included in distributions
- [ ] `synapse` command works after install

---

## Testing Strategy Summary

### Unit Tests (pytest)
- Resource discovery
- File operations
- Settings merge logic
- Backup/restore logic
- State tracking
- Sense command detection
- All helper functions

**Coverage Target**: >80%

### Integration Tests (pytest)
- Full workflow application
- Full workflow removal
- Workflow switching
- Settings merge with existing files
- Backup and restore
- Error scenarios

**Test Environment**: Temporary directories with cleanup

### Manual Tests
- Install via pip/pipx
- Real project integration
- Claude Code interaction
- Hook execution
- Agent activation
- Quality tool integration

---

## Dependencies & Parallelization

### Can Be Done in Parallel:
- Task 2.3 (Settings Merge) with 2.1/2.2 (File Operations)
- Task 2.4 (Backup System) with any Phase 2 tasks
- Task 4.1-4.3 (Planning Workflow Content) with implementation tasks
- Task 5.1-5.3 (Sense Command) with Phase 4
- Task 6.1-6.6 (Implementation Workflow Content) with earlier phases

### Critical Path:
1. Foundation (1.1 → 1.2 → 1.3 → 1.4)
2. File & Settings (2.1 → 2.2, 2.5)
3. Workflow Commands (3.1 → 3.2 → 3.3 → 3.4)
4. Content & Testing (4.4, 6.7, 7.1-7.5)

---

## Timeline Summary

| Phase | Days | Key Deliverable |
|-------|------|-----------------|
| 1. Foundation | 1-2 | Working init command |
| 2. File & Settings | 3-4 | File operations & merge |
| 3. Workflow Commands | 5-6 | Apply & remove workflows |
| 4. Planning Workflow | 7-8 | Feature planning workflow |
| 5. Sense Command | 8 | Project analysis |
| 6. Implementation Workflow | 9-11 | Feature implementation workflow |
| 7. Testing & Polish | 12-13 | Production ready |

**Total Estimated Timeline**: 12-13 days

---

## Risk Mitigation

1. **Resource Discovery Issues**: Test early in both editable and installed modes
2. **Settings Merge Bugs**: Comprehensive unit tests with edge cases
3. **Hook Execution Failures**: Test with real uv installation
4. **Permission Problems**: Test on multiple platforms (Mac/Linux/Windows)
5. **Backup Failures**: Test with various filesystem conditions

---

## Success Metrics

- [ ] All unit tests pass (>80% coverage)
- [ ] All integration tests pass
- [ ] Manual testing successful in real project
- [ ] Can install via pip and pipx
- [ ] Both workflows work end-to-end
- [ ] No data loss in any scenario
- [ ] Documentation complete and accurate
