# Legacy Tests

This directory contains tests for the legacy feature-implementation workflow (pre-Option 6).

These tests validate the original implementation located in `legacy/resources/workflows/feature-implementation/`.

## Legacy Components Tested

- **Hooks**: `verification-complete.py`, `pre-tool-use.py`, `post-tool-use.py`, `change_detection.py`
- **Agents**: Verifier and Implementer workflow
- **Task Format**: `[[Task ID: Description]]` with checkbox validation
- **Config**: `third_party_workflows.detected[]` (array structure)

## Running Legacy Tests

```bash
# Run all legacy tests
pytest tests/legacy/

# Run specific legacy test
pytest tests/legacy/test_verification_workflow.py
```

## Test Files

| Test File | Component Tested |
|-----------|------------------|
| `test_verification_workflow.py` | `verification-complete.py` hook, checkbox and status validation |
| `test_change_detection.py` | `change_detection.py` module, git detection patterns |
| `test_monorepo_optimization_integration.py` | Monorepo optimization with change detection |
| `test_schema_aware_blocking.py` | `pre-tool-use.py` blocking logic |
| `test_strict_lint_warnings.py` | `post-tool-use.py` quality commands with strict/flexible modes |
| `test_task_parser.py` | Old `task_parser.py` module with checkbox validation |

These tests remain to ensure backward compatibility and that legacy workflows continue functioning for users who haven't migrated to Option 6 yet.
