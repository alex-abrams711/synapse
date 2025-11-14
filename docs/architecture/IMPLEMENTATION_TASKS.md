# Synapse CLI Modularization - Implementation Task List

This document provides a detailed, actionable task breakdown for implementing the modularization proposal outlined in `modularization_proposal.md`.

---

## 📋 Project Overview

**Goal**: Transform the monolithic `__init__.py` (1,823 lines) into a clean, layered architecture with 15 focused modules.

**Timeline**: 2-3 weeks
**Approach**: 5-phase migration with parallel code paths
**Success Criteria**: All tests pass, zero breaking changes, >90% coverage

---

## Phase 1: Create Infrastructure (Days 1-2)

**Goal**: Set up new modules without breaking existing code

### ✅ Day 1: Core Layer

- [x] **1.1 Create directory structure**
  ```bash
  mkdir -p src/synapse_cli/{core,infrastructure,services,commands}
  touch src/synapse_cli/{core,infrastructure,services,commands}/__init__.py
  ```

- [x] **1.2 Create `core/types.py`**
  - [x] Define `WorkflowMode` enum
  - [x] Define `ExitCode` enum
  - [x] Define `ConfigDict` TypedDict
  - [x] Define `ManifestDict` TypedDict
  - [x] Add module docstring
  - [x] Ensure all imports work

- [x] **1.3 Create `core/models.py`**
  - [x] Implement `ProjectConfig` dataclass
    - [x] Add `from_dict()` classmethod
    - [x] Add `to_dict()` method
  - [x] Implement `WorkflowManifest` dataclass
    - [x] Add `from_dict()` classmethod
    - [x] Add `to_dict()` method
  - [x] Implement `WorkflowInfo` dataclass
  - [x] Implement `BackupInfo` dataclass
  - [x] Add comprehensive docstrings

- [x] **1.4 Write unit tests for core layer**
  - [x] Create `tests/unit/core/test_types.py`
  - [x] Create `tests/unit/core/test_models.py`
  - [x] Test `ProjectConfig.from_dict()` and `to_dict()`
  - [x] Test `WorkflowManifest.from_dict()` and `to_dict()`
  - [x] Test all dataclass instantiation
  - [x] Verify >90% coverage for core layer
  - [x] Run tests: `pytest tests/unit/core/ -v --cov=src/synapse_cli/core`

- [x] **1.5 Verify core layer**
  - [x] All tests pass
  - [x] No dependencies on existing code
  - [x] Type hints complete
  - [x] Docstrings complete

### ✅ Day 2: Infrastructure Base

- [x] **2.1 Create `infrastructure/persistence.py`**
  - [x] Implement `JsonStore[T]` generic class
    - [x] `__init__(base_dir, filename)`
    - [x] `get_path(target_dir)` method
    - [x] `exists(target_dir)` method
    - [x] `load(target_dir)` method
    - [x] `save(data, target_dir)` method
  - [x] Add error handling for JSON decode errors
  - [x] Add comprehensive docstrings

- [x] **2.2 Create `infrastructure/resources.py`**
  - [x] Implement `ResourceManager` class
    - [x] `resources_dir` property (lazy)
    - [x] `workflows_dir` property (lazy)
    - [x] `_locate_resources()` method
    - [x] `discover_workflows()` method
    - [x] `get_workflow_info()` method
    - [x] `validate_workflow_exists()` method
  - [x] Create singleton instance
  - [x] Add `get_resource_manager()` factory function

- [x] **2.3 Create `infrastructure/config_store.py`**
  - [x] Implement `ConfigStore` class
    - [x] Use `JsonStore` as base
    - [x] `get_path()` method
    - [x] `load()` method
    - [x] `save()` method
    - [x] `exists()` method
    - [x] `update_workflow_tracking()` method
    - [x] `clear_workflow_tracking()` method
    - [x] `get_active_workflow()` method
  - [x] Create singleton instance
  - [x] Add `get_config_store()` factory function

- [x] **2.4 Create `infrastructure/manifest_store.py`**
  - [x] Implement `ManifestStore` class
    - [x] `__init__(synapse_version)`
    - [x] `get_path()` method
    - [x] `load()` method (returns WorkflowManifest)
    - [x] `save()` method
    - [x] `exists()` method
    - [x] `create_manifest()` method
    - [x] `delete()` method
  - [x] Add `get_manifest_store()` factory function

- [x] **2.5 Write unit tests for infrastructure base**
  - [x] Create `tests/unit/infrastructure/test_persistence.py`
    - [x] Test JsonStore.get_path()
    - [x] Test JsonStore.exists()
    - [x] Test JsonStore.load() with missing file
    - [x] Test JsonStore.save() and load() roundtrip
    - [x] Test JsonStore error handling
  - [x] Create `tests/unit/infrastructure/test_resources.py`
    - [x] Test resource directory location
    - [x] Test workflow discovery
    - [x] Test get_workflow_info()
    - [x] Test validate_workflow_exists()
  - [x] Create `tests/unit/infrastructure/test_config_store.py`
    - [x] Test load/save roundtrip
    - [x] Test update_workflow_tracking()
    - [x] Test clear_workflow_tracking()
    - [x] Test get_active_workflow()
  - [x] Create `tests/unit/infrastructure/test_manifest_store.py`
    - [x] Test create_manifest()
    - [x] Test load/save roundtrip
    - [x] Test delete()
  - [x] Verify >90% coverage
  - [x] Run tests: `pytest tests/unit/infrastructure/ -v --cov=src/synapse_cli/infrastructure`

---

## Phase 2: Infrastructure Operations & Services (Days 3-5)

**Goal**: Complete infrastructure layer and build services layer

### ✅ Day 3: Infrastructure Operations

- [x] **3.1 Create `infrastructure/backup_manager.py`**
  - [x] Implement `BackupManager` class
    - [x] `get_backup_dir()` method
    - [x] `create_backup()` method
    - [x] `get_latest_backup()` method
    - [x] `restore_from_backup()` method
  - [x] Create singleton instance
  - [x] Add `get_backup_manager()` factory function

- [x] **3.2 Create `infrastructure/file_operations.py`**
  - [x] Implement `FileOperations` class
    - [x] `copy_directory_with_conflicts()` static method
    - [x] `cleanup_empty_directories()` static method
  - [x] Create singleton instance
  - [x] Add `get_file_operations()` factory function

- [x] **3.3 Write unit tests for infrastructure operations**
  - [x] Create `tests/unit/infrastructure/test_backup_manager.py`
    - [x] Test create_backup() with existing .claude
    - [x] Test create_backup() with no .claude
    - [x] Test get_latest_backup()
    - [x] Test restore_from_backup()
    - [x] Use tmp_path fixture for isolation
  - [x] Create `tests/unit/infrastructure/test_file_operations.py`
    - [x] Test copy_directory_with_conflicts() normal case
    - [x] Test copy_directory_with_conflicts() with conflicts
    - [x] Test copy_directory_with_conflicts() with force=True
    - [x] Test cleanup_empty_directories()
  - [x] Verify >90% coverage
  - [x] Run tests: `pytest tests/unit/infrastructure/ -v --cov=src/synapse_cli/infrastructure`

### ✅ Day 4: Services Layer - Part 1

- [x] **4.1 Create `services/validation_service.py`**
  - [x] Implement `ValidationService` class
    - [x] `__init__()` - inject dependencies
    - [x] `validate_synapse_initialized()` method
    - [x] `validate_workflow_exists()` method
    - [x] `check_uv_available()` method
    - [x] `validate_workflow_preconditions()` method
    - [x] `validate_removal_preconditions()` method
  - [x] Create singleton instance
  - [x] Add `get_validation_service()` factory function

- [x] **4.2 Create `services/settings_service.py`**
  - [x] Implement `SettingsService` class
    - [x] `__init__()` - inject dependencies
    - [x] `convert_hook_paths_to_absolute()` method
    - [x] `merge_settings_json()` method
    - [x] `_merge_hooks()` private method
    - [x] `remove_hooks_from_settings()` method
  - [x] Create singleton instance
  - [x] Add `get_settings_service()` factory function

- [x] **4.3 Write unit tests for services - part 1**
  - [x] Create `tests/unit/services/test_validation_service.py`
    - [x] Test validate_synapse_initialized()
    - [x] Test validate_workflow_exists()
    - [x] Test check_uv_available()
    - [x] Test validate_workflow_preconditions() success
    - [x] Test validate_workflow_preconditions() failures
    - [x] Mock dependencies (config_store, resource_manager)
  - [x] Create `tests/unit/services/test_settings_service.py`
    - [x] Test convert_hook_paths_to_absolute()
    - [x] Test merge_settings_json() - new file
    - [x] Test merge_settings_json() - existing file
    - [x] Test _merge_hooks()
    - [x] Test remove_hooks_from_settings()
  - [x] Verify >90% coverage
  - [x] Run tests: `pytest tests/unit/services/ -v --cov=src/synapse_cli/services`

### ✅ Day 5: Services Layer - Part 2

- [x] **5.1 Create `services/workflow_service.py`**
  - [x] Implement `WorkflowService` class
    - [x] `__init__(synapse_version)` - inject all dependencies
    - [x] `list_workflows()` method
    - [x] `get_workflow_status()` method
    - [x] `apply_workflow()` method
    - [x] `_apply_workflow_directories()` private method
    - [x] `_display_copy_results()` private method
    - [x] `_display_merge_results()` private method
  - [x] Add `get_workflow_service()` factory function

- [x] **5.2 Create `services/removal_service.py`**
  - [x] Implement `RemovalService` class
    - [x] `__init__(synapse_version)` - inject dependencies
    - [x] `remove_workflow()` method
    - [x] `_remove_from_manifest()` private method
    - [x] `_display_removal_plan()` private method
    - [x] `_confirm_removal()` private method
    - [x] `_display_manual_cleanup_instructions()` private method
  - [x] Add `get_removal_service()` factory function

- [x] **5.3 Write unit tests for services - part 2**
  - [x] Create `tests/unit/services/test_workflow_service.py`
    - [x] Test list_workflows()
    - [x] Test get_workflow_status()
    - [x] Test apply_workflow() success path
    - [x] Test apply_workflow() error handling
    - [x] Mock all dependencies
  - [x] Create `tests/unit/services/test_removal_service.py`
    - [x] Test remove_workflow() with backup
    - [x] Test remove_workflow() with manifest
    - [x] Test _remove_from_manifest()
    - [x] Mock dependencies
  - [x] Verify >90% coverage
  - [x] Run tests: `pytest tests/unit/services/ -v --cov=src/synapse_cli/services`

- [ ] **5.4 Write integration tests**
  - [ ] Create `tests/integration/test_workflow_application.py`
    - [ ] Test complete workflow application flow
    - [ ] Test workflow removal flow
    - [ ] Test workflow switching
    - [ ] Use real file system (tmp_path)
  - [ ] Run integration tests: `pytest tests/integration/ -v`

---

## Phase 3: Commands & CLI (Days 6-7)

**Goal**: Extract command handlers and create CLI interface

### ✅ Day 6: Commands Layer

- [x] **6.1 Create `commands/init.py`**
  - [x] Implement `InitCommand` class
    - [x] `__init__(synapse_version)`
    - [x] `execute()` method
    - [x] `_prompt_agent_selection()` private method
    - [x] `_create_config()` private method
  - [x] Add `get_init_command()` factory function

- [x] **6.2 Create `commands/workflow.py`**
  - [x] Implement `WorkflowCommand` class
    - [x] `__init__(synapse_version)`
    - [x] `list()` method
    - [x] `status()` method
    - [x] `apply()` method
    - [x] `remove()` method
  - [x] Add `get_workflow_command()` factory function

- [x] **6.3 Write unit tests for commands**
  - [x] Create `tests/unit/commands/test_init.py`
    - [x] Test execute() success path
    - [x] Test execute() when already initialized
    - [x] Mock user input
    - [x] Mock config_store
  - [x] Create `tests/unit/commands/test_workflow.py`
    - [x] Test list()
    - [x] Test status()
    - [x] Test apply()
    - [x] Test remove()
    - [x] Mock services
  - [x] Verify >90% coverage
  - [x] Run tests: `pytest tests/unit/commands/ -v --cov=src/synapse_cli/commands`

### ✅ Day 7: CLI Setup

- [ ] **7.1 Create `cli.py`**
  - [ ] Implement `create_parser()` function
    - [ ] Define init subcommand
    - [ ] Define workflow subcommand with args
    - [ ] Add help text and examples
  - [ ] Implement `dispatch_command()` function
    - [ ] Route to init command
    - [ ] Route to workflow commands
    - [ ] Handle list/status/remove/apply
  - [ ] Implement `main()` function
    - [ ] Parse args
    - [ ] Dispatch to commands

- [ ] **7.2 Update `__init__.py` for parallel paths**
  - [ ] Keep all existing functions
  - [ ] Add new exports:
    ```python
    from .cli import main as cli_main
    from .infrastructure.config_store import get_config_store
    from .services.workflow_service import get_workflow_service
    ```
  - [ ] Add to `__all__`

- [ ] **7.3 Update `__main__.py`**
  - [ ] Keep old main() as fallback
  - [ ] Add try/except to use new CLI
  - [ ] Ensure backward compatibility

- [ ] **7.4 Write CLI tests**
  - [ ] Create `tests/unit/test_cli.py`
    - [ ] Test create_parser()
    - [ ] Test dispatch_command() routing
    - [ ] Test main() integration
  - [ ] Create `tests/e2e/test_cli_commands.py`
    - [ ] Test `synapse init` end-to-end
    - [ ] Test `synapse workflow list`
    - [ ] Test `synapse workflow status`
    - [ ] Use subprocess to invoke CLI
  - [ ] Run all tests: `pytest -v --cov=src/synapse_cli`

- [ ] **7.5 Manual testing**
  - [ ] Install package in editable mode: `pip install -e .`
  - [ ] Test `synapse init`
  - [ ] Test `synapse workflow list`
  - [ ] Test `synapse workflow feature-planning`
  - [ ] Test `synapse workflow status`
  - [ ] Test `synapse workflow remove`
  - [ ] Verify all outputs match old behavior

---

## Phase 4: Switch Over (Days 8-9)

**Goal**: Make new code the default, deprecate old code

### ✅ Day 8: Deprecation & Migration

- [ ] **8.1 Add deprecation warnings to old functions**
  - [ ] Update each function in `__init__.py`:
    ```python
    def workflow_apply(name: str, force: bool = False) -> None:
        """DEPRECATED: Use WorkflowService.apply_workflow()"""
        import warnings
        warnings.warn(
            "workflow_apply is deprecated. Use get_workflow_service().apply_workflow()",
            DeprecationWarning,
            stacklevel=2
        )
        from .services.workflow_service import get_workflow_service
        service = get_workflow_service(__version__)
        return service.apply_workflow(name, force=force)
    ```
  - [ ] Add delegation to new code for all 40 functions

- [ ] **8.2 Update internal imports**
  - [ ] Search for internal uses of old functions
  - [ ] Update to use new services/commands
  - [ ] Verify no internal code uses deprecated functions

- [ ] **8.3 Update `__main__.py` to use new CLI by default**
  - [ ] Change to call `cli_main()` from `cli.py`
  - [ ] Keep old `main()` as emergency fallback

- [ ] **8.4 Run full test suite**
  - [ ] Run all unit tests: `pytest tests/unit/ -v --cov=src/synapse_cli`
  - [ ] Run all integration tests: `pytest tests/integration/ -v`
  - [ ] Run all e2e tests: `pytest tests/e2e/ -v`
  - [ ] Verify >90% total coverage
  - [ ] Fix any failing tests

### ✅ Day 9: Regression Testing

- [ ] **9.1 Run existing test suite**
  - [ ] Run all legacy tests
  - [ ] Verify 100% pass rate
  - [ ] Check for deprecation warnings in test output
  - [ ] Update tests to use new APIs

- [ ] **9.2 Performance benchmarking**
  - [ ] Benchmark import time: `python -c "import time; s=time.time(); import synapse_cli; print(time.time()-s)"`
  - [ ] Benchmark workflow apply time
  - [ ] Compare with baseline (before refactor)
  - [ ] Ensure no >10% regression

- [ ] **9.3 Manual regression testing**
  - [ ] Test all CLI commands manually
  - [ ] Test error cases
  - [ ] Test edge cases
  - [ ] Document any behavioral changes

- [ ] **9.4 Documentation updates**
  - [ ] Update README.md with new architecture
  - [ ] Update API documentation
  - [ ] Add migration guide for users
  - [ ] Update developer docs

---

## Phase 5: Cleanup & Polish (Days 10-12)

**Goal**: Remove old code, finalize documentation

### ✅ Day 10: Code Cleanup

- [ ] **10.1 Remove old function implementations from `__init__.py`**
  - [ ] Keep only exports and version
  - [ ] Remove all 40 function implementations
  - [ ] Final `__init__.py` should be ~30 lines:
    ```python
    """Synapse CLI - AI-first workflow system."""

    __version__ = "0.3.0"

    # Public API exports
    from .cli import main
    from .infrastructure.resources import get_resource_manager
    from .infrastructure.config_store import get_config_store
    from .services.workflow_service import get_workflow_service

    __all__ = [
        'main',
        'get_resource_manager',
        'get_config_store',
        'get_workflow_service',
        '__version__'
    ]
    ```

- [ ] **10.2 Remove deprecation warnings**
  - [ ] Delete deprecated function wrappers
  - [ ] Clean up any temporary migration code

- [ ] **10.3 Final code review**
  - [ ] Review all new modules for consistency
  - [ ] Check type hints are complete
  - [ ] Check docstrings are complete
  - [ ] Check imports are optimized
  - [ ] Run linter: `ruff check src/`
  - [ ] Run formatter: `ruff format src/`

### ✅ Day 11: Documentation

- [ ] **11.1 Update architecture documentation**
  - [ ] Update `docs/ARCHITECTURE.md`
  - [ ] Add module dependency diagrams
  - [ ] Document each layer's responsibilities
  - [ ] Add code examples

- [ ] **11.2 Create migration guide**
  - [ ] Document breaking changes (if any)
  - [ ] Provide before/after code examples
  - [ ] Explain new import paths
  - [ ] Add FAQ section

- [ ] **11.3 Update API documentation**
  - [ ] Generate API docs from docstrings
  - [ ] Document public interfaces
  - [ ] Add usage examples
  - [ ] Document factory functions

- [ ] **11.4 Update developer guide**
  - [ ] Explain new architecture
  - [ ] Document how to add new features
  - [ ] Explain testing strategy
  - [ ] Add contribution guidelines

### ✅ Day 12: Final Validation & Release Prep

- [ ] **12.1 Final test suite run**
  - [ ] Run complete test suite: `pytest -v --cov=src/synapse_cli`
  - [ ] Verify >90% coverage
  - [ ] Check for any flaky tests
  - [ ] Run tests on Python 3.9, 3.10, 3.11, 3.12

- [ ] **12.2 Integration testing**
  - [ ] Test in fresh virtual environment
  - [ ] Test pip install from source
  - [ ] Test CLI in real projects
  - [ ] Test workflows end-to-end

- [ ] **12.3 Performance validation**
  - [ ] Run performance benchmarks
  - [ ] Compare with baseline
  - [ ] Document any improvements/regressions
  - [ ] Profile memory usage

- [ ] **12.4 Release preparation**
  - [ ] Update CHANGELOG.md
  - [ ] Update version number
  - [ ] Tag release commit
  - [ ] Prepare release notes

---

## Buffer Days (Days 13-15)

**Purpose**: Handle unexpected issues, additional testing, polish

### Potential Issues to Address

- [ ] **Circular import issues**
  - [ ] Use lazy imports if needed
  - [ ] Refactor module boundaries

- [ ] **Test failures**
  - [ ] Debug failing tests
  - [ ] Update test fixtures
  - [ ] Fix edge cases

- [ ] **Performance regressions**
  - [ ] Profile slow operations
  - [ ] Optimize critical paths
  - [ ] Add caching if needed

- [ ] **Documentation gaps**
  - [ ] Fill in missing docs
  - [ ] Add more examples
  - [ ] Create video tutorials

---

## Success Checklist

Before considering the refactor complete, verify:

- [ ] ✅ All existing tests pass (100%)
- [ ] ✅ New test coverage >90%
- [ ] ✅ No breaking API changes
- [ ] ✅ Performance within 10% of baseline
- [ ] ✅ Import time <100ms
- [ ] ✅ All 15 modules created
- [ ] ✅ Zero circular dependencies
- [ ] ✅ Complete type hints
- [ ] ✅ Complete docstrings
- [ ] ✅ Documentation updated
- [ ] ✅ Migration guide created
- [ ] ✅ Code review approved
- [ ] ✅ Manual testing complete
- [ ] ✅ Ready for production

---

## Quick Reference

### Module Count & Line Estimates

| Layer | Modules | Total Lines |
|-------|---------|-------------|
| Core | 2 | ~200 |
| Infrastructure | 6 | ~600 |
| Services | 4 | ~700 |
| Commands | 2 | ~300 |
| CLI | 1 | ~100 |
| **Total** | **15** | **~1,900** |

### Test Coverage Goals

| Category | Target |
|----------|--------|
| Unit tests | >90% per module |
| Integration tests | All workflows |
| E2E tests | All CLI commands |
| Regression tests | 100% pass |

### Key Commands

```bash
# Run all tests
pytest -v --cov=src/synapse_cli

# Run specific layer tests
pytest tests/unit/core/ -v --cov=src/synapse_cli/core
pytest tests/unit/infrastructure/ -v --cov=src/synapse_cli/infrastructure
pytest tests/unit/services/ -v --cov=src/synapse_cli/services

# Run integration tests
pytest tests/integration/ -v

# Check coverage
pytest --cov=src/synapse_cli --cov-report=html

# Run linter
ruff check src/

# Run formatter
ruff format src/

# Install editable
pip install -e .

# Test CLI
synapse --help
synapse init
synapse workflow list
```

---

## Notes

- **Commit frequently**: After each completed task, commit with descriptive message
- **Test continuously**: Run tests after each module is created
- **Document as you go**: Don't leave documentation for the end
- **Ask for help**: If stuck, consult the proposal or ask for clarification
- **Stay focused**: One task at a time, verify before moving on

---

**Last Updated**: 2024-11-14
**Related**: `modularization_proposal.md`, `SUMMARY.txt`
