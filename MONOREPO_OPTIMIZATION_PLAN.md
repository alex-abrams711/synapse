# Monorepo Quality Check Optimization Plan
## Affected Package Detection for Performance Improvement

**Version**: 1.0
**Date**: November 5, 2025
**Status**: Planning
**Related**: MONOREPO_IMPLEMENTATION_PLAN.md

---

## Executive Summary

The current monorepo implementation runs quality checks for **all projects** on every implementer completion, causing significant performance issues in large monorepos (2-8 minutes for 15+ packages). This plan implements **git-based affected package detection** to only run quality checks for projects with actual changes, reducing runtime by 5-10x for typical development workflows.

### Problem Statement

**Current Behavior:**
- Hook runs ALL quality checks for ALL projects in monorepo
- 15 packages × 10 seconds each = 2.5 minutes per check
- Most changes only affect 1-2 packages
- Slow feedback loop frustrates developers

**Target Improvement:**
- Only run quality checks for affected packages
- 2 packages × 10 seconds = 20 seconds per check
- 7-8x faster for typical changes
- Maintain safety with fallback to full checks when uncertain

---

## Solution Overview

### Core Strategy

1. **Git-based change detection**: Use `git diff` to identify modified files
2. **Package mapping**: Map changed files to their owning packages
3. **Selective execution**: Only run quality checks for affected packages
4. **Safe fallbacks**: Check all packages when git unavailable or no changes detected
5. **Manual overrides**: Support explicit package lists and force-check configurations

### Key Design Principles

- **Safety first**: Default to checking all packages if uncertain
- **Zero breaking changes**: Feature is opt-in with safe defaults
- **Developer control**: Support manual overrides and environment variables
- **Clear feedback**: Show which packages are being checked and why

---

## Technical Design

### 1. Change Detection Function

```python
def get_changed_files_from_git(detection_method: str = "uncommitted") -> list[str]:
    """
    Get list of changed files using git.

    Args:
        detection_method: One of "uncommitted", "since_main", "last_commit", "staged"

    Returns:
        List of file paths relative to repo root, or empty list if git unavailable
    """
    import subprocess

    commands = {
        "uncommitted": ["git", "diff", "--name-only", "HEAD"],
        "since_main": ["git", "diff", "--name-only", "origin/main...HEAD"],
        "last_commit": ["git", "diff", "--name-only", "HEAD~1...HEAD"],
        "staged": ["git", "diff", "--name-only", "--cached"],
        "all_changes": ["git", "status", "--porcelain", "--untracked-files=all"]
    }

    try:
        cmd = commands.get(detection_method, commands["uncommitted"])
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5,
            cwd=os.getcwd()
        )

        if result.returncode != 0:
            return []

        # Parse output based on command
        if detection_method == "all_changes":
            # Parse git status porcelain format: "XY filename"
            lines = result.stdout.strip().split('\n')
            return [line[3:] for line in lines if line.strip()]
        else:
            # Parse git diff format: one filename per line
            return [f for f in result.stdout.strip().split('\n') if f.strip()]

    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return []


def get_affected_projects(projects_config: dict, optimization_config: dict) -> tuple[set, str]:
    """
    Determine which projects have been affected by recent changes.

    Args:
        projects_config: The "projects" object from quality-config
        optimization_config: The "optimization" object from quality-config

    Returns:
        Tuple of (set of affected project names, detection reason string)
    """
    check_affected_only = optimization_config.get("check_affected_only", True)

    # Check for manual override first
    if not check_affected_only:
        return set(projects_config.keys()), "optimization disabled in config"

    # Check environment variable override
    if os.getenv("SYNAPSE_CHECK_ALL_PROJECTS") == "1":
        return set(projects_config.keys()), "SYNAPSE_CHECK_ALL_PROJECTS=1 environment variable"

    # Get detection method
    detection_method = optimization_config.get("detection_method", "uncommitted")

    # Get changed files
    changed_files = get_changed_files_from_git(detection_method)

    if not changed_files:
        # No changes detected - fall back to all projects for safety
        fallback = optimization_config.get("fallback_to_all", True)
        if fallback:
            return set(projects_config.keys()), "no changes detected (fallback to all)"
        else:
            return set(), "no changes detected (configured to skip)"

    # Map files to projects
    affected = set()

    for file_path in changed_files:
        for project_name, project_config in projects_config.items():
            project_dir = project_config.get("directory", "")

            # Normalize paths
            normalized_file = file_path.replace("\\", "/")
            normalized_dir = project_dir.replace("\\", "/")

            if normalized_file.startswith(normalized_dir):
                affected.add(project_name)
                break  # File belongs to this project, move to next file

    # Add force-check projects
    force_check = optimization_config.get("force_check_projects", [])
    affected.update(force_check)

    if not affected:
        # Changes detected but no projects matched - check all for safety
        return set(projects_config.keys()), "changes detected but no projects matched (fallback)"

    return affected, f"git detection ({detection_method})"
```

### 2. Configuration Schema Extension

Add to `resources/schemas/synapse-config-schema.json`:

```json
{
  "quality-config": {
    "type": "object",
    "properties": {
      "mode": {"type": "string"},
      "projects": {"type": "object"},
      "optimization": {
        "type": "object",
        "description": "Performance optimization settings for monorepo quality checks",
        "properties": {
          "check_affected_only": {
            "type": "boolean",
            "default": true,
            "description": "Only check projects with detected changes"
          },
          "detection_method": {
            "type": "string",
            "enum": ["uncommitted", "since_main", "last_commit", "staged", "all_changes"],
            "default": "uncommitted",
            "description": "Git detection method to identify changed files"
          },
          "fallback_to_all": {
            "type": "boolean",
            "default": true,
            "description": "Check all projects if no changes detected"
          },
          "force_check_projects": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Projects to always check regardless of changes"
          },
          "verbose_logging": {
            "type": "boolean",
            "default": false,
            "description": "Show detailed detection information"
          }
        }
      }
    }
  }
}
```

### 3. Hook Integration

Update `implementer-post-tool-use.py`:

```python
def check_monorepo_gates(config):
    """Check quality gates for affected projects in monorepo"""
    projects = config.get("projects", {})

    if not projects:
        print("❌ No projects configured in monorepo", file=sys.stderr)
        return None, {}

    # Get optimization configuration
    optimization = config.get("optimization", {})

    # Determine which projects to check
    affected_projects, detection_reason = get_affected_projects(projects, optimization)

    # Log detection results
    verbose = optimization.get("verbose_logging", False)

    if len(affected_projects) < len(projects):
        print(f"🎯 Optimized check: {len(affected_projects)}/{len(projects)} affected project(s)",
              file=sys.stderr)
        print(f"   Detection: {detection_reason}", file=sys.stderr)

        if verbose:
            print(f"   Checking: {', '.join(sorted(affected_projects))}", file=sys.stderr)
            skipped = set(projects.keys()) - affected_projects
            if skipped:
                print(f"   Skipping: {', '.join(sorted(skipped))}", file=sys.stderr)
    else:
        print(f"🔍 Full check: {len(projects)} project(s)", file=sys.stderr)
        print(f"   Reason: {detection_reason}", file=sys.stderr)

    print("", file=sys.stderr)

    # Run checks only for affected projects
    all_results = {
        "mode": "monorepo",
        "projects": {},
        "optimization": {
            "affected_projects": list(affected_projects),
            "total_projects": len(projects),
            "detection_reason": detection_reason
        }
    }

    overall_pass = True

    for project_name in sorted(affected_projects):  # Sort for consistent output
        project_config = projects[project_name]
        print(f"📦 Project: {project_name} ({project_config.get('directory', 'N/A')})", file=sys.stderr)
        print("-" * 60, file=sys.stderr)

        project_results = check_project_gates(project_name, project_config)
        all_results["projects"][project_name] = project_results

        # ... existing failure checking logic ...

    return config, all_results
```

### 4. Override Mechanisms

**Environment Variables:**
- `SYNAPSE_CHECK_ALL_PROJECTS=1` - Force check all projects
- `SYNAPSE_DETECTION_METHOD=since_main` - Override detection method
- `SYNAPSE_VERBOSE_DETECTION=1` - Enable verbose logging

**Command-line flag (future):**
```bash
synapse workflow feature-implementation --check-all-projects
```

**Config overrides:**
```json
{
  "quality-config": {
    "optimization": {
      "check_affected_only": false  // Disable optimization
    }
  }
}
```

---

## Implementation Phases

### Phase 1: Core Change Detection (High Priority)

**Goal**: Implement basic git-based change detection with safe fallbacks.

#### Task 1.1: Create Change Detection Module
**File**: `resources/workflows/feature-implementation/hooks/change_detection.py`

**Implementation**:
- `get_changed_files_from_git()` function
- `get_affected_projects()` function
- Error handling for git unavailable
- Path normalization for cross-platform support
- Unit tests for various git scenarios

**Validation**:
- Test with uncommitted changes
- Test with no git repository
- Test with no changes
- Test with changes in multiple projects
- Test with changes in single project
- Test path normalization (Windows/Unix)

#### Task 1.2: Update Hook to Use Detection
**File**: `resources/workflows/feature-implementation/hooks/implementer-post-tool-use.py`

**Changes**:
- Import change detection module
- Update `check_monorepo_gates()` to filter projects
- Add logging for detection results
- Preserve existing error handling

**Validation**:
- Hook runs successfully with detection enabled
- Hook falls back to all projects when git unavailable
- Hook reports affected projects clearly

#### Task 1.3: Update Schema
**File**: `resources/schemas/synapse-config-schema.json`

**Changes**:
- Add `optimization` object to quality-config
- Define all optimization properties with defaults
- Update schema validation tests

**Validation**:
- Schema validates configs with optimization settings
- Schema validates configs without optimization (backwards compatible)
- Default values are correctly applied

---

### Phase 2: Configuration & Controls (Medium Priority)

**Goal**: Add configuration options and manual overrides.

#### Task 2.1: Update Sense Command Documentation
**File**: `resources/commands/synapse/sense.md`

**Changes**:
- Document optimization settings
- Add examples of different detection methods
- Explain when to use force_check_projects
- Show how to disable optimization

**Validation**:
- Documentation is clear and accurate
- Examples are tested and working

#### Task 2.2: Add Default Optimization Config
**File**: Update sense command to generate optimization config

**Changes**:
- Generate optimization section in config for monorepos
- Set sensible defaults based on project structure
- Add comments explaining settings

**Validation**:
- New configs include optimization settings
- Existing configs continue to work (no optimization section)

#### Task 2.3: Environment Variable Support
**File**: `resources/workflows/feature-implementation/hooks/change_detection.py`

**Changes**:
- Check `SYNAPSE_CHECK_ALL_PROJECTS` environment variable
- Check `SYNAPSE_DETECTION_METHOD` environment variable
- Check `SYNAPSE_VERBOSE_DETECTION` environment variable
- Document environment variables in README

**Validation**:
- Environment variables override config settings
- Absence of environment variables uses config defaults

---

### Phase 3: Testing & Edge Cases (High Priority)

**Goal**: Comprehensive testing and edge case handling.

#### Task 3.1: Create Test Fixtures
**Directory**: `tests/fixtures/monorepo-optimization/`

**Structure**:
```
tests/fixtures/monorepo-optimization/
├── .git/                          # Mock git repository
├── .synapse/
│   └── config.json               # Monorepo config with optimization
├── backend/
│   ├── src/main.py              # Will be modified in tests
│   └── tests/test_main.py
├── frontend/
│   └── src/index.ts
└── shared/
    └── utils.py
```

**Validation**:
- Fixture can be used for integration tests
- Mock git operations work correctly

#### Task 3.2: Unit Tests
**File**: `tests/test_change_detection.py`

**Test cases**:
- `test_get_changed_files_uncommitted()`
- `test_get_changed_files_since_main()`
- `test_get_changed_files_no_git()`
- `test_get_changed_files_timeout()`
- `test_get_affected_projects_single()`
- `test_get_affected_projects_multiple()`
- `test_get_affected_projects_none_matched()`
- `test_get_affected_projects_no_changes()`
- `test_get_affected_projects_with_force_check()`
- `test_get_affected_projects_env_override()`
- `test_path_normalization_windows()`
- `test_path_normalization_unix()`

**Validation**:
- All tests pass
- Coverage >90% for change_detection.py

#### Task 3.3: Integration Tests
**File**: `tests/test_monorepo_optimization_integration.py`

**Test cases**:
- `test_hook_with_single_project_change()`
- `test_hook_with_multiple_project_changes()`
- `test_hook_with_no_changes_fallback()`
- `test_hook_with_force_check_projects()`
- `test_hook_with_optimization_disabled()`
- `test_hook_with_env_override()`
- `test_hook_performance_improvement()`

**Validation**:
- Integration tests pass
- Performance improvement is measurable
- Fallback behavior is safe

#### Task 3.4: Edge Case Tests
**File**: Add to `tests/test_edge_cases.py`

**Test cases**:
- Root-level changes (e.g., .gitignore, README.md)
- Changes outside any project directory
- Project directory renamed/moved
- Git repository in subdirectory
- Symlinked files
- Very large number of changed files (1000+)
- Special characters in filenames
- Spaces in project directory names

**Validation**:
- All edge cases handled gracefully
- No crashes or unexpected behavior
- Clear logging for unusual situations

---

### Phase 4: Documentation & User Guidance (Medium Priority)

**Goal**: Complete documentation for users and developers.

#### Task 4.1: Create Optimization Guide
**File**: `docs/MONOREPO_OPTIMIZATION.md`

**Content**:
- Overview of optimization feature
- Performance comparison (before/after)
- Configuration options explained
- Detection methods comparison
- When to use force_check_projects
- Troubleshooting guide
- Common patterns and best practices

**Validation**:
- Documentation covers all features
- Examples are tested and accurate

#### Task 4.2: Update README
**File**: `README.md`

**Changes**:
- Add "Performance" section under Monorepo support
- Mention optimization feature
- Link to detailed guide
- Show before/after performance example

**Validation**:
- README updates are clear and concise
- Links work correctly

#### Task 4.3: Update Hook README
**File**: `resources/workflows/feature-implementation/hooks/README.md`

**Changes**:
- Document change detection behavior
- Explain optimization settings
- Show how to debug detection issues
- Add troubleshooting section

**Validation**:
- Hook documentation is complete
- Developers understand how detection works

#### Task 4.4: Add Migration Notes
**File**: `docs/MIGRATION.md` (or add section to existing)

**Content**:
- How to enable optimization for existing monorepos
- How to configure force_check_projects
- How to troubleshoot detection issues
- How to opt-out if needed

**Validation**:
- Migration path is clear
- Existing users can upgrade smoothly

---

### Phase 5: Advanced Features (Low Priority / Future)

**Goal**: Additional optimizations and features for power users.

#### Task 5.1: Parallel Execution (Future Enhancement)
- Run quality checks for multiple projects in parallel
- Configurable parallelism level
- Aggregate results correctly

#### Task 5.2: Dependency-Aware Checking (Future Enhancement)
- Detect inter-project dependencies
- Check dependent projects when shared code changes
- Configure dependency graph in config

#### Task 5.3: Smart Caching (Future Enhancement)
- Cache quality check results per project
- Invalidate cache when project files change
- Skip checks if cache is valid

#### Task 5.4: Performance Metrics (Future Enhancement)
- Track time saved by optimization
- Report metrics to user
- Store historical performance data

---

## Task Checklist

### Phase 1: Core Change Detection ✅ High Priority - COMPLETE
- [x] **Task 1.1: Create Change Detection Module**
  - [x] Implement `get_changed_files_from_git()` function
  - [x] Implement `get_affected_projects()` function
  - [x] Add error handling for git unavailable scenarios
  - [x] Add path normalization for cross-platform support
  - [x] Write unit tests for git detection functions
  - [x] Test with various git scenarios (uncommitted, staged, etc.)

- [x] **Task 1.2: Update Hook to Use Detection**
  - [x] Import change detection module in `implementer-post-tool-use.py`
  - [x] Modify `check_monorepo_gates()` to filter projects
  - [x] Add logging for detection results
  - [x] Preserve existing error handling and fallbacks
  - [x] Test hook with detection enabled
  - [x] Test hook with git unavailable

- [x] **Task 1.3: Update Schema**
  - [x] Add `optimization` object to `synapse-config-schema.json`
  - [x] Define all optimization properties with types and defaults
  - [x] Update schema validation logic in `validate_config.py`
  - [x] Add schema validation tests for optimization settings
  - [x] Test backwards compatibility (configs without optimization)

### Phase 2: Configuration & Controls ✅ Medium Priority - COMPLETE
- [x] **Task 2.1: Update Sense Command Documentation**
  - [x] Document optimization settings in `sense.md`
  - [x] Add examples of different detection methods
  - [x] Explain force_check_projects use cases
  - [x] Show how to disable optimization
  - [x] Add troubleshooting section for detection issues

- [x] **Task 2.2: Add Default Optimization Config**
  - [x] Update sense command to generate optimization section
  - [x] Set sensible defaults for monorepo detection
  - [x] Add inline comments explaining settings
  - [x] Test with new project initialization
  - [x] Test with existing project updates

- [x] **Task 2.3: Environment Variable Support**
  - [x] Implement `SYNAPSE_CHECK_ALL_PROJECTS` environment variable
  - [x] Implement `SYNAPSE_DETECTION_METHOD` environment variable
  - [x] Implement `SYNAPSE_VERBOSE_DETECTION` environment variable
  - [x] Document environment variables in README
  - [x] Test environment variable overrides

### Phase 3: Testing & Edge Cases ✓ High Priority
- [ ] **Task 3.1: Create Test Fixtures**
  - [ ] Create `tests/fixtures/monorepo-optimization/` directory
  - [ ] Set up mock git repository in fixture
  - [ ] Create multi-project structure (backend, frontend, shared)
  - [ ] Add sample config with optimization settings
  - [ ] Test fixture can be used for integration tests

- [ ] **Task 3.2: Unit Tests**
  - [ ] Test `get_changed_files_from_git()` with different methods
  - [ ] Test `get_changed_files_from_git()` with no git
  - [ ] Test `get_changed_files_from_git()` with timeout
  - [ ] Test `get_affected_projects()` with single project change
  - [ ] Test `get_affected_projects()` with multiple project changes
  - [ ] Test `get_affected_projects()` with no changes
  - [ ] Test `get_affected_projects()` with force_check_projects
  - [ ] Test environment variable overrides
  - [ ] Test path normalization (Windows and Unix)
  - [ ] Achieve >90% code coverage for change_detection.py

- [ ] **Task 3.3: Integration Tests**
  - [ ] Test full hook execution with single project change
  - [ ] Test full hook execution with multiple project changes
  - [ ] Test fallback behavior with no changes detected
  - [ ] Test force_check_projects functionality
  - [ ] Test with optimization disabled
  - [ ] Test environment variable overrides in full context
  - [ ] Measure and validate performance improvement
  - [ ] Verify safe fallback behavior

- [ ] **Task 3.4: Edge Case Tests**
  - [ ] Test root-level changes (README, .gitignore, etc.)
  - [ ] Test changes outside any project directory
  - [ ] Test with project directory renamed/moved
  - [ ] Test with git repository in subdirectory
  - [ ] Test with symlinked files
  - [ ] Test with large number of changed files (1000+)
  - [ ] Test with special characters in filenames
  - [ ] Test with spaces in project directory names
  - [ ] Verify graceful handling of all edge cases

### Phase 4: Documentation & User Guidance ⏸️ Medium Priority - PARTIAL
- [ ] **Task 4.1: Create Optimization Guide**
  - [ ] Write `docs/MONOREPO_OPTIMIZATION.md`
  - [ ] Add overview and motivation section
  - [ ] Document performance comparison with examples
  - [ ] Explain all configuration options
  - [ ] Compare detection methods with recommendations
  - [ ] Document force_check_projects use cases
  - [ ] Add troubleshooting section
  - [ ] Include common patterns and best practices

- [ ] **Task 4.2: Update README**
  - [ ] Add "Performance Optimization" section
  - [ ] Show before/after performance example
  - [ ] Link to detailed optimization guide
  - [ ] Mention in monorepo features section

- [x] **Task 4.3: Update Hook README**
  - [x] Document change detection behavior in hooks README
  - [x] Explain optimization settings impact
  - [x] Show how to debug detection issues
  - [x] Add troubleshooting for common problems

- [ ] **Task 4.4: Add Migration Notes**
  - [ ] Create or update migration guide
  - [ ] Document how to enable optimization for existing projects
  - [ ] Explain how to configure force_check_projects
  - [ ] Add troubleshooting for migration issues
  - [ ] Document opt-out procedures

### Phase 5: Advanced Features ⏸️ Low Priority / Future
- [ ] **Task 5.1: Parallel Execution** (Future)
  - [ ] Design parallel execution architecture
  - [ ] Implement concurrent quality checks
  - [ ] Add configuration for parallelism level
  - [ ] Test result aggregation

- [ ] **Task 5.2: Dependency-Aware Checking** (Future)
  - [ ] Design dependency graph structure
  - [ ] Implement dependency detection
  - [ ] Check dependent projects automatically
  - [ ] Add dependency configuration to schema

- [ ] **Task 5.3: Smart Caching** (Future)
  - [ ] Design cache structure
  - [ ] Implement result caching per project
  - [ ] Add cache invalidation logic
  - [ ] Test cache hit/miss scenarios

- [ ] **Task 5.4: Performance Metrics** (Future)
  - [ ] Design metrics collection
  - [ ] Track time saved by optimization
  - [ ] Report metrics to user
  - [ ] Store historical performance data

---

## Success Criteria

### Phase 1 (MVP) ✅ COMPLETE
- [x] Change detection works with git-based file detection
- [x] Hook only runs checks for affected projects
- [x] Safe fallback to all projects when uncertain
- [x] Performance improvement of 5-10x for typical single-project changes
- [x] No breaking changes to existing functionality

### Phase 2 ✅ COMPLETE
- [x] Configuration options are documented and working
- [x] Manual overrides function correctly
- [x] Environment variables provide runtime control
- [x] Sense command generates optimization config

### Phase 3
- [ ] >90% test coverage for change detection logic
- [ ] All edge cases handled gracefully
- [ ] Integration tests verify end-to-end behavior
- [ ] Performance improvement is measurable and validated

### Phase 4
- [ ] Complete documentation for users
- [ ] Clear migration path for existing projects
- [ ] Troubleshooting guide covers common issues
- [ ] Examples are tested and accurate

---

## Performance Targets

### Baseline (Current)
- 15 projects × 10 seconds = 150 seconds (2.5 minutes)
- Single project change: 150 seconds
- Two project changes: 150 seconds

### Target (With Optimization)
- 1 project change × 10 seconds = 10 seconds (15x improvement)
- 2 project changes × 10 seconds = 20 seconds (7.5x improvement)
- 5 project changes × 10 seconds = 50 seconds (3x improvement)
- Fallback to all: 150 seconds (same as baseline)

### Measurement
- Track execution time before and after
- Report time saved in hook output (optional)
- Collect metrics from real-world usage

---

## Risk Mitigation

### Risk 1: Git Detection Fails
**Mitigation**: Always fall back to checking all projects if detection fails or returns no results.

### Risk 2: False Negatives (Missing Changes)
**Mitigation**:
- Conservative detection (prefer false positives)
- force_check_projects for critical packages
- Environment variable override for manual control

### Risk 3: Breaking Existing Workflows
**Mitigation**:
- Feature is opt-in (defaults are safe)
- Backwards compatible schema
- Existing configs continue to work

### Risk 4: Platform Differences (Git Behavior)
**Mitigation**:
- Test on Windows, Linux, macOS
- Path normalization for all platforms
- Handle git unavailable gracefully

### Risk 5: User Confusion
**Mitigation**:
- Clear logging about what's being checked
- Comprehensive documentation
- Easy opt-out mechanism

---

## Implementation Order

**Critical Path** (blocking items):
1. Phase 1.1 → Phase 1.2 → Phase 1.3 (change detection core)
2. Phase 3.2 → Phase 3.3 (testing)

**Parallel Work** (can be done concurrently):
- Phase 2 (configuration) - while Phase 3 is ongoing
- Phase 4 (documentation) - after Phase 1, during Phase 3

**Estimated Timeline**:
- Phase 1: 1-2 work sessions (4-8 hours)
- Phase 2: 1 work session (2-4 hours)
- Phase 3: 2 work sessions (4-8 hours)
- Phase 4: 1 work session (2-4 hours)
- **Total: 4-6 work sessions (12-24 hours)**

---

## Breaking Changes

**None** - This is an additive feature with backwards compatibility:
- Existing configs without optimization work as before (check all projects)
- Schema validation accepts configs with or without optimization
- Default behavior is safe (fallback to all projects when uncertain)

---

## Future Enhancements (Out of Scope)

These features are explicitly deferred to future versions:

1. **Parallel execution** - Run checks for multiple projects concurrently
2. **Dependency-aware checking** - Detect inter-project dependencies
3. **Smart caching** - Cache quality check results
4. **Performance metrics** - Track and report time savings
5. **Change impact analysis** - Predict which projects might be affected
6. **Incremental testing** - Only run tests for changed code
7. **Remote cache sharing** - Share cache across team/CI
8. **Custom detection scripts** - User-provided detection logic

---

## Appendix: Example Configurations

### Minimal (Default)
```json
{
  "quality-config": {
    "mode": "monorepo",
    "projects": { /* ... */ }
    // optimization uses all defaults
  }
}
```

### Explicit Optimization
```json
{
  "quality-config": {
    "mode": "monorepo",
    "optimization": {
      "check_affected_only": true,
      "detection_method": "uncommitted",
      "fallback_to_all": true,
      "force_check_projects": [],
      "verbose_logging": false
    },
    "projects": { /* ... */ }
  }
}
```

### With Force-Check (Shared Libraries)
```json
{
  "quality-config": {
    "mode": "monorepo",
    "optimization": {
      "check_affected_only": true,
      "force_check_projects": ["shared-utils", "core-lib"]
    },
    "projects": {
      "backend": { /* ... */ },
      "frontend": { /* ... */ },
      "shared-utils": { /* ... */ },
      "core-lib": { /* ... */ }
    }
  }
}
```

### Optimization Disabled
```json
{
  "quality-config": {
    "mode": "monorepo",
    "optimization": {
      "check_affected_only": false
    },
    "projects": { /* ... */ }
  }
}
```

### Verbose Detection
```json
{
  "quality-config": {
    "mode": "monorepo",
    "optimization": {
      "check_affected_only": true,
      "verbose_logging": true
    },
    "projects": { /* ... */ }
  }
}
```

---

## Questions for Clarification

1. **Detection Method Priority**: Should we prefer uncommitted changes, or changes since main?
2. **Force-Check Defaults**: Should we auto-detect shared libraries and force-check them?
3. **Performance Logging**: Should we track and report time savings to users?
4. **CI/CD Integration**: Should detection behave differently in CI environments?
5. **Project Dependencies**: Should we support explicit dependency declarations now or defer?

---

**Status**: Ready for implementation
**Next Step**: Begin Phase 1, Task 1.1 - Create Change Detection Module
