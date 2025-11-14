# Synapse Tests

This directory contains tests for the Synapse workflow system.

## Directory Structure

```
tests/
├── README.md                        # This file
├── integration/                     # Integration tests
│   └── test_full_workflow.py       # Full workflow integration tests
├── fixtures/                        # Test fixtures
│   └── formats/                    # Sample task files (OpenSpec, Spec Kit, custom)
├── test_stop_qa_check.py           # Stop hook QA verification tests
├── test_edge_cases.py              # Schema edge cases
├── test_multi_format_support.py    # Format detection and parsing
├── test_schema_generator.py        # Schema generation
├── test_task_schema_parser.py      # Schema-based task parsing
└── test_integration_workflow.py    # Sense command workflow
```

## Test Categories

### Hook Tests
Tests for the QA verification hook system:
- `test_stop_qa_check.py` - Stop hook that verifies QA status of active tasks

### Parser Tests
Tests for schema-driven task parsing:
- `test_schema_generator.py` - Automatic schema generation from task files
- `test_task_schema_parser.py` - Schema-based task file parsing
- `test_edge_cases.py` - Edge case handling (empty files, malformed content, Unicode)
- `test_multi_format_support.py` - Multi-format support (OpenSpec, GitHub Spec Kit, custom)

### Integration Tests
End-to-end workflow tests:
- `test_integration_workflow.py` - Schema generation → parsing workflow
- `integration/test_full_workflow.py` - Complete QA verification workflow

## Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_stop_qa_check.py

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

### By Feature

```bash
# Schema-related tests
pytest tests/ -k "schema"

# QA verification tests
pytest tests/test_stop_qa_check.py tests/integration/test_full_workflow.py

# Parser tests
pytest tests/test_task_schema_parser.py tests/test_schema_generator.py

# Edge cases and multi-format
pytest tests/test_edge_cases.py tests/test_multi_format_support.py
```

## Adding New Tests

### For Hook Verification
Add tests to `tests/test_stop_qa_check.py` or `tests/integration/test_full_workflow.py` that test:
- Hook behavior with different QA statuses
- Active tasks management
- Quality gate enforcement
- Multi-task scenarios

### For Schema and Parsing
Add tests to `tests/test_*.py` that test:
- `synapse_cli.parsers` modules
- Schema generation and validation
- Task parsing logic
- Format detection

### For Integration
Add tests to `tests/integration/` that test:
- Complete workflows from start to finish
- Schema generation → parsing → verification
- Real-world scenarios

## Test Fixtures

Test fixtures are located in `tests/fixtures/`:
- `formats/` - Sample task files in different formats:
  - `openspec_tasks.md` - OpenSpec format example
  - `github_spec_kit_tasks.md` - GitHub Spec Kit format example
  - `custom_format_tasks.md` - Custom format example

## Configuration References

Tests reference the current workflow configuration:
- **Workflow**: `resources/workflows/feature-implementation-v2/`
- **Config structure**: `.synapse/config.json` with `third_party_workflow` object
- **QA Status values**: `[Not Started]`, `[Passed]`, `[Complete]`, `[Failed - reason]`
- **Schema version**: 2.0 (format-agnostic, schema-driven)

## Troubleshooting

### Import Errors
If you see `ModuleNotFoundError`:
- Ensure you've installed Synapse: `pip install -e .`
- Check that import paths reference correct modules in `synapse_cli.parsers`

### Path Issues
If tests can't find files:
- Tests use `Path(__file__).parent` for relative paths
- Ensure fixtures are in `tests/fixtures/`
- Temporary files should be created in test-specific temp directories

### Hook Path Issues
If integration tests fail finding hooks:
- Hook path: `resources/workflows/feature-implementation-v2/hooks/stop_qa_check.py`
- Tests navigate from test file location to project root
- Check that the workflow directory structure is intact
