# Synapse Tests

This directory contains tests for the Synapse workflow system.

## Directory Structure

```
tests/
├── README.md                                    # This file
├── legacy/                                      # Tests for legacy implementation (pre-Option 6)
│   ├── README.md
│   ├── test_verification_workflow.py
│   ├── test_change_detection.py
│   ├── test_monorepo_optimization_integration.py
│   ├── test_schema_aware_blocking.py
│   ├── test_strict_lint_warnings.py
│   └── test_task_parser.py
├── integration/                                 # Integration tests (if any)
├── fixtures/                                    # Test fixtures
├── test_stop_qa_check.py                        # Option 6: Simple stop hook tests
├── test_edge_cases.py                           # Shared: Schema edge cases
├── test_multi_format_support.py                 # Shared: Format detection
├── test_schema_generator.py                     # Shared: Schema generation
├── test_task_schema_parser.py                   # Shared: Schema-based parsing
└── test_integration_workflow.py                 # Shared: Sense command workflow
```

## Test Categories

### Option 6 Tests (New Implementation)
Tests for the simplified, two-stage QA verification architecture:
- `test_stop_qa_check.py` - Simple hook that checks QA status of active tasks

### Shared Infrastructure Tests
Tests for components used by both legacy and new implementations:
- `test_schema_generator.py` - Schema generation from task files
- `test_task_schema_parser.py` - Schema-driven task parsing
- `test_edge_cases.py` - Edge case handling (empty files, malformed content, Unicode, etc.)
- `test_multi_format_support.py` - Multi-format support (OpenSpec, GitHub Spec Kit, custom formats)
- `test_integration_workflow.py` - End-to-end sense → parser workflow

### Legacy Tests
See `tests/legacy/README.md` for legacy implementation tests.

## Running Tests

```bash
# Run all tests
pytest tests/

# Run only new implementation tests
pytest tests/test_stop_qa_check.py

# Run only shared infrastructure tests
pytest tests/test_schema_*.py tests/test_edge_cases.py tests/test_multi_format_support.py tests/test_integration_workflow.py

# Run only legacy tests
pytest tests/legacy/

# Run with coverage
pytest tests/ --cov=resources --cov=synapse_cli --cov-report=html

# Run with verbose output
pytest tests/ -v

# Run specific test class
pytest tests/test_stop_qa_check.py::TestStopQACheck

# Run specific test
pytest tests/test_stop_qa_check.py::TestStopQACheck::test_empty_active_tasks
```

## Test Organization

### By Implementation Type

```bash
# New Option 6 tests
pytest tests/ -k "not legacy" --ignore=tests/legacy/

# Legacy tests only
pytest tests/legacy/

# Shared infrastructure tests
pytest tests/test_schema_generator.py tests/test_task_schema_parser.py tests/test_edge_cases.py
```

### By Feature

```bash
# Schema-related tests
pytest tests/ -k "schema"

# QA verification tests
pytest tests/test_stop_qa_check.py tests/legacy/test_verification_workflow.py

# Parser tests
pytest tests/test_task_schema_parser.py tests/legacy/test_task_parser.py
```

## CI/CD Integration

Both legacy and new tests should run in CI to ensure:
1. **Legacy workflows** remain functional for users who haven't migrated
2. **New Option 6** implementation works correctly
3. **Shared infrastructure** supports both systems

Example GitHub Actions workflow:

```yaml
- name: Run all tests
  run: pytest tests/ -v --cov=resources --cov=synapse_cli

- name: Run legacy tests
  run: pytest tests/legacy/ -v

- name: Run Option 6 tests
  run: pytest tests/test_stop_qa_check.py -v
```

## Adding New Tests

### For Option 6 Implementation
Add tests to `tests/test_*.py` that reference:
- `resources/workflows/feature-implementation-v2/`
- New config structure: `third_party_workflow` (object)
- Three-category QA Status: `[Not Started]`, `[Passed]`, `[Failed - reason]`

### For Shared Infrastructure
Add tests to `tests/test_*.py` that test:
- `synapse_cli.parsers` modules
- Schema generation and validation
- Task parsing logic

### For Legacy Implementation
Add tests to `tests/legacy/test_*.py` that reference:
- `legacy/resources/workflows/feature-implementation/`
- Old config structure: `third_party_workflows.detected[]` (array)
- Legacy hooks and agents

## Test Fixtures

Test fixtures are located in `tests/fixtures/`:
- `formats/` - Sample task files in different formats (OpenSpec, Spec Kit, custom)
- `monorepo-optimization/` - Sample monorepo structure for integration tests

## Troubleshooting

### Import Errors
If you see import errors like `ModuleNotFoundError: No module named 'task_parser'`:
- Legacy tests import from `legacy/resources/workflows/feature-implementation/hooks/`
- Ensure the legacy directory structure exists
- Check that import paths in test files reference `legacy/`

### Path Issues
If tests can't find files:
- Most tests use `Path(__file__).parent` for relative paths
- Check that fixtures are in the correct location
- Ensure temporary files are created in test-specific temp directories

### Test Failures After Migration
If tests fail after migration:
1. Check import paths point to correct location (`legacy/` vs `resources/`)
2. Verify test fixtures still exist
3. Run legacy tests separately to isolate issues: `pytest tests/legacy/ -v`

## Migration Notes

This test structure was created during the Option 6 migration:
- **Legacy tests** moved to `tests/legacy/` to preserve backward compatibility
- **Import paths** updated to reference `legacy/resources/`
- **New tests** added to `tests/` for Option 6 implementation
- **Shared tests** remain in `tests/` for infrastructure used by both

See `SIMPLIFIED_APPROACH.md` for details on the Option 6 architecture.
