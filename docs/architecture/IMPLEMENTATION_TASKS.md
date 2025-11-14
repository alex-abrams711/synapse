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

- [ ] **1.1 Create directory structure**
  ```bash
  mkdir -p src/synapse_cli/{core,infrastructure,services,commands}
  touch src/synapse_cli/{core,infrastructure,services,commands}/__init__.py
  ```

- [ ] **1.2 Create `core/types.py`**
  - [ ] Define `WorkflowMode` enum
  - [ ] Define `ExitCode` enum
  - [ ] Define `ConfigDict` TypedDict
  - [ ] Define `ManifestDict` TypedDict
  - [ ] Add module docstring
  - [ ] Ensure all imports work

- [ ] **1.3 Create `core/models.py`**
  - [ ] Implement `ProjectConfig` dataclass
    - [ ] Add `from_dict()` classmethod
    - [ ] Add `to_dict()` method
  - [ ] Implement `WorkflowManifest` dataclass
    - [ ] Add `from_dict()` classmethod
    - [ ] Add `to_dict()` method
  - [ ] Implement `WorkflowInfo` dataclass
  - [ ] Implement `BackupInfo` dataclass
  - [ ] Add comprehensive docstrings

- [ ] **1.4 Write unit tests for core layer**
  - [ ] Create `tests/unit/core/test_types.py`
  - [ ] Create `tests/unit/core/test_models.py`
  - [ ] Test `ProjectConfig.from_dict()` and `to_dict()`
  - [ ] Test `WorkflowManifest.from_dict()` and `to_dict()`
  - [ ] Test all dataclass instantiation
  - [ ] Verify >90% coverage for core layer
  - [ ] Run tests: `pytest tests/unit/core/ -v --cov=src/synapse_cli/core`

- [ ] **1.5 Verify core layer**
  - [ ] All tests pass
  - [ ] No dependencies on existing code
  - [ ] Type hints complete
  - [ ] Docstrings complete

### ✅ Day 2: Infrastructure Base

- [ ] **2.1 Create `infrastructure/persistence.py`**
  - [ ] Implement `JsonStore[T]` generic class
    - [ ] `__init__(base_dir, filename)`
    - [ ] `get_path(target_dir)` method
    - [ ] `exists(target_dir)` method
    - [ ] `load(target_dir)` method
    - [ ] `save(data, target_dir)` method
  - [ ] Add error handling for JSON decode errors
  - [ ] Add comprehensive docstrings

- [ ] **2.2 Create `infrastructure/resources.py`**
  - [ ] Implement `ResourceManager` class
    - [ ] `resources_dir` property (lazy)
    - [ ] `workflows_dir` property (lazy)
    - [ ] `_locate_resources()` method
    - [ ] `discover_workflows()` method
    - [ ] `get_workflow_info()` method
    - [ ] `validate_workflow_exists()` method
  - [ ] Create singleton instance
  - [ ] Add `get_resource_manager()` factory function

- [ ] **2.3 Create `infrastructure/config_store.py`**
  - [ ] Implement `ConfigStore` class
    - [ ] Use `JsonStore` as base
    - [ ] `get_path()` method
    - [ ] `load()` method
    - [ ] `save()` method
    - [ ] `exists()` method
    - [ ] `update_workflow_tracking()` method
    - [ ] `clear_workflow_tracking()` method
    - [ ] `get_active_workflow()` method
  - [ ] Create singleton instance
  - [ ] Add `get_config_store()` factory function

- [ ] **2.4 Create `infrastructure/manifest_store.py`**
  - [ ] Implement `ManifestStore` class
    - [ ] `__init__(synapse_version)`
    - [ ] `get_path()` method
    - [ ] `load()` method (returns WorkflowManifest)
    - [ ] `save()` method
    - [ ] `exists()` method
    - [ ] `create_manifest()` method
    - [ ] `delete()` method
  - [ ] Add `get_manifest_store()` factory function

- [ ] **2.5 Write unit tests for infrastructure base**
  - [ ] Create `tests/unit/infrastructure/test_persistence.py`
    - [ ] Test JsonStore.get_path()
    - [ ] Test JsonStore.exists()
    - [ ] Test JsonStore.load() with missing file
    - [ ] Test JsonStore.save() and load() roundtrip
    - [ ] Test JsonStore error handling
  - [ ] Create `tests/unit/infrastructure/test_resources.py`
    - [ ] Test resource directory location
    - [ ] Test workflow discovery
    - [ ] Test get_workflow_info()
    - [ ] Test validate_workflow_exists()
  - [ ] Create `tests/unit/infrastructure/test_config_store.py`
    - [ ] Test load/save roundtrip
    - [ ] Test update_workflow_tracking()
    - [ ] Test clear_workflow_tracking()
    - [ ] Test get_active_workflow()
  - [ ] Create `tests/unit/infrastructure/test_manifest_store.py`
    - [ ] Test create_manifest()
    - [ ] Test load/save roundtrip
    - [ ] Test delete()
  - [ ] Verify >90% coverage
  - [ ] Run tests: `pytest tests/unit/infrastructure/ -v --cov=src/synapse_cli/infrastructure`

---

## Phase 2: Infrastructure Operations & Services (Days 3-5)

**Goal**: Complete infrastructure layer and build services layer

### ✅ Day 3: Infrastructure Operations

- [ ] **3.1 Create `infrastructure/backup_manager.py`**
  - [ ] Implement `BackupManager` class
    - [ ] `get_backup_dir()` method
    - [ ] `create_backup()` method
    - [ ] `get_latest_backup()` method
    - [ ] `restore_from_backup()` method
  - [ ] Create singleton instance
  - [ ] Add `get_backup_manager()` factory function

- [ ] **3.2 Create `infrastructure/file_operations.py`**
  - [ ] Implement `FileOperations` class
    - [ ] `copy_directory_with_conflicts()` static method
    - [ ] `cleanup_empty_directories()` static method
  - [ ] Create singleton instance
  - [ ] Add `get_file_operations()` factory function

- [ ] **3.3 Write unit tests for infrastructure operations**
  - [ ] Create `tests/unit/infrastructure/test_backup_manager.py`
    - [ ] Test create_backup() with existing .claude
    - [ ] Test create_backup() with no .claude
    - [ ] Test get_latest_backup()
    - [ ] Test restore_from_backup()
    - [ ] Use tmp_path fixture for isolation
  - [ ] Create `tests/unit/infrastructure/test_file_operations.py`
    - [ ] Test copy_directory_with_conflicts() normal case
    - [ ] Test copy_directory_with_conflicts() with conflicts
    - [ ] Test copy_directory_with_conflicts() with force=True
    - [ ] Test cleanup_empty_directories()
  - [ ] Verify >90% coverage
  - [ ] Run tests: `pytest tests/unit/infrastructure/ -v --cov=src/synapse_cli/infrastructure`

### ✅ Day 4: Services Layer - Part 1

- [ ] **4.1 Create `services/validation_service.py`**
  - [ ] Implement `ValidationService` class
    - [ ] `__init__()` - inject dependencies
    - [ ] `validate_synapse_initialized()` method
    - [ ] `validate_workflow_exists()` method
    - [ ] `check_uv_available()` method
    - [ ] `validate_workflow_preconditions()` method
    - [ ] `validate_removal_preconditions()` method
  - [ ] Create singleton instance
  - [ ] Add `get_validation_service()` factory function

- [ ] **4.2 Create `services/settings_service.py`**
  - [ ] Implement `SettingsService` class
    - [ ] `__init__()` - inject dependencies
    - [ ] `convert_hook_paths_to_absolute()` method
    - [ ] `merge_settings_json()` method
    - [ ] `_merge_hooks()` private method
    - [ ] `remove_hooks_from_settings()` method
  - [ ] Create singleton instance
  - [ ] Add `get_settings_service()` factory function

- [ ] **4.3 Write unit tests for services - part 1**
  - [ ] Create `tests/unit/services/test_validation_service.py`
    - [ ] Test validate_synapse_initialized()
    - [ ] Test validate_workflow_exists()
    - [ ] Test check_uv_available()
    - [ ] Test validate_workflow_preconditions() success
    - [ ] Test validate_workflow_preconditions() failures
    - [ ] Mock dependencies (config_store, resource_manager)
  - [ ] Create `tests/unit/services/test_settings_service.py`
    - [ ] Test convert_hook_paths_to_absolute()
    - [ ] Test merge_settings_json() - new file
    - [ ] Test merge_settings_json() - existing file
    - [ ] Test _merge_hooks()
    - [ ] Test remove_hooks_from_settings()
  - [ ] Verify >90% coverage
  - [ ] Run tests: `pytest tests/unit/services/ -v --cov=src/synapse_cli/services`

### ✅ Day 5: Services Layer - Part 2

- [ ] **5.1 Create `services/workflow_service.py`**
  - [ ] Implement `WorkflowService` class
    - [ ] `__init__(synapse_version)` - inject all dependencies
    - [ ] `list_workflows()` method
    - [ ] `get_workflow_status()` method
    - [ ] `apply_workflow()` method
    - [ ] `_apply_workflow_directories()` private method
    - [ ] `_display_copy_results()` private method
    - [ ] `_display_merge_results()` private method
  - [ ] Add `get_workflow_service()` factory function

- [ ] **5.2 Create `services/removal_service.py`**
  - [ ] Implement `RemovalService` class
    - [ ] `__init__(synapse_version)` - inject dependencies
    - [ ] `remove_workflow()` method
    - [ ] `_remove_from_manifest()` private method
    - [ ] `_display_removal_plan()` private method
    - [ ] `_confirm_removal()` private method
    - [ ] `_display_manual_cleanup_instructions()` private method
  - [ ] Add `get_removal_service()` factory function

- [ ] **5.3 Write unit tests for services - part 2**
  - [ ] Create `tests/unit/services/test_workflow_service.py`
    - [ ] Test list_workflows()
    - [ ] Test get_workflow_status()
    - [ ] Test apply_workflow() success path
    - [ ] Test apply_workflow() error handling
    - [ ] Mock all dependencies
  - [ ] Create `tests/unit/services/test_removal_service.py`
    - [ ] Test remove_workflow() with backup
    - [ ] Test remove_workflow() with manifest
    - [ ] Test _remove_from_manifest()
    - [ ] Mock dependencies
  - [ ] Verify >90% coverage
  - [ ] Run tests: `pytest tests/unit/services/ -v --cov=src/synapse_cli/services`

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

- [ ] **6.1 Create `commands/init.py`**
  - [ ] Implement `InitCommand` class
    - [ ] `__init__(synapse_version)`
    - [ ] `execute()` method
    - [ ] `_prompt_agent_selection()` private method
    - [ ] `_create_config()` private method
  - [ ] Add `get_init_command()` factory function

- [ ] **6.2 Create `commands/workflow.py`**
  - [ ] Implement `WorkflowCommand` class
    - [ ] `__init__(synapse_version)`
    - [ ] `list()` method
    - [ ] `status()` method
    - [ ] `apply()` method
    - [ ] `remove()` method
  - [ ] Add `get_workflow_command()` factory function

- [ ] **6.3 Write unit tests for commands**
  - [ ] Create `tests/unit/commands/test_init.py`
    - [ ] Test execute() success path
    - [ ] Test execute() when already initialized
    - [ ] Mock user input
    - [ ] Mock config_store
  - [ ] Create `tests/unit/commands/test_workflow.py`
    - [ ] Test list()
    - [ ] Test status()
    - [ ] Test apply()
    - [ ] Test remove()
    - [ ] Mock services
  - [ ] Verify >90% coverage
  - [ ] Run tests: `pytest tests/unit/commands/ -v --cov=src/synapse_cli/commands`

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
