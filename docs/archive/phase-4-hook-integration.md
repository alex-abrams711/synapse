# Phase 4: Hook Integration - Implementation Summary

**Status**: Complete
**Created**: 2025-10-24

## Overview

Phase 4 integrates the TaskSchemaParser v2.0 into workflow hooks, replacing experimental v0 implementations with production-ready parsers that use semantic states.

## Key Improvements

### Before (v0 - Experimental)
```python
# Fragile: Numeric group extraction
task_id = match.group(2)  # Which field is this?

# Fragile: Array position mapping
if dev_vals[1] == current_status:  # Position 1 = in_progress?
    allow_work = True
```

### After (v2 - Production)
```python
# Clear: Named group extraction
task_id = match.group("task_id")

# Clear: Semantic state checking
if target_task.dev_state == "in_progress":
    allow_work = True
```

## Reference Implementation

### Pre-Tool-Use Hook (`docs/examples/hooks/pre-tool-use-v2.py`)

**Purpose**: Block work on tasks based on semantic states

**Features**:
- Uses TaskSchemaParser for robust parsing
- Works with semantic states (not_started, in_progress, complete)
- Clean blocking logic without hardcoded status strings
- Graceful error handling with fallback
- Comprehensive logging for debugging

**Blocking Rules**:
1. ✅ Allow continued work on in-progress tasks
2. ✅ Allow new tasks when no blockers exist
3. ❌ Block new tasks when others are in-progress
4. ❌ Block new tasks when others await QA/verification
5. ❌ Block work on completed tasks awaiting QA

**Exit Codes**:
- `1`: Allow (not applicable or validation passed)
- `2`: Block (blocking condition met)

### Integration Steps

1. **Import TaskSchemaParser**
   ```python
   from synapse_cli.parsers import (
       TaskSchemaParser,
       ParsedTask,
       SchemaValidationError,
   )
   ```

2. **Load Schema from Config**
   ```python
   config = load_synapse_config()
   tasks_file_path, schema = find_active_tasks_file(config)
   ```

3. **Parse Tasks with Schema**
   ```python
   parser = TaskSchemaParser(schema)
   parsed_tasks = parser.parse_tasks_file(tasks_file_path)
   ```

4. **Use Semantic States in Business Logic**
   ```python
   if target_task.dev_state == "in_progress":
       # Allow continued work
   elif target_task.dev_state == "complete" and target_task.qa_state != "complete":
       # Block - needs QA
   ```

## Business Logic Simplification

### Blocking Conditions (Semantic)

All logic uses semantic states - no hardcoded status strings:

```python
def check_task_blocking(target_task, all_tasks):
    # Check for in-progress tasks
    blocking_in_progress = [
        t for t in all_tasks
        if t.dev_state == "in_progress"
    ]

    # Check for tasks awaiting QA
    blocking_awaiting_qa = [
        t for t in all_tasks
        if t.dev_state == "complete"
        and (t.qa_state != "complete" or t.uv_state != "complete")
    ]

    # Clear, semantic logic - no string matching
```

### Benefits

1. **Format Agnostic**: Works with any status value variations
   - "Complete", "Done", "Finished" all map to `complete`
   - "Dev Status", "Development Status" both map to `dev`

2. **Maintainable**: Business logic separated from parsing
   - Change status values without updating hooks
   - Add new status variations without code changes

3. **Testable**: Mock ParsedTask objects for unit tests
   - No need for real tasks files
   - Fast, reliable tests

4. **Robust**: Comprehensive error handling
   - Schema validation on load
   - Graceful fallback if parsing fails
   - Clear error messages

## Error Handling Strategy

### Schema Validation Errors
```python
try:
    parser = TaskSchemaParser(schema)
except SchemaValidationError as e:
    print(f"❌ Schema validation failed: {e}")
    print("ℹ️  Run 'synapse sense' to regenerate schema")
    sys.exit(1)  # Allow with warning
```

### Parsing Errors
```python
try:
    parsed_tasks = parser.parse_tasks_file(tasks_file_path)
except Exception as e:
    print(f"❌ Error parsing tasks: {e}")
    sys.exit(1)  # Allow with warning
```

### Missing Config/Tasks
```python
if not tasks_file_path:
    print("ℹ️  No task management - allowing task")
    sys.exit(1)  # Allow when no tasks configured
```

## Hook Deployment

### File Locations

Hooks should be placed in workflow directories:
```
resources/workflows/feature-implementation/hooks/
├── pre-tool-use.py          # Uses v2 parser
├── post-tool-use.py         # Uses v2 parser
└── verification-complete.py # Uses v2 parser
```

### Hook Registration

Hooks are registered in workflow configuration:
```json
{
  "hooks": {
    "pre-tool-use": "hooks/pre-tool-use.py",
    "post-tool-use": "hooks/post-tool-use.py",
    "verification-complete": "hooks/verification-complete.py"
  }
}
```

## Testing Hooks

### Unit Testing

Test business logic with mock ParsedTask objects:

```python
def test_blocking_logic():
    # Create mock tasks
    task1 = ParsedTask(
        task_id="T001",
        description="Task one",
        dev_state="in_progress",
        qa_state="not_started",
        uv_state="not_started",
        keywords=["task", "one"],
        line_number=1
    )

    task2 = ParsedTask(
        task_id="T002",
        description="Task two",
        dev_state="not_started",
        qa_state="not_started",
        uv_state="not_started",
        keywords=["task", "two"],
        line_number=5
    )

    # Test blocking
    should_block, reason = check_task_blocking(task2, [task1, task2])
    assert should_block
    assert "in progress" in reason.lower()
```

### Integration Testing

Test with real tasks files:

```python
def test_hook_with_real_tasks():
    # Generate schema
    generator = SchemaGenerator()
    schema = generator.generate_schema("tasks.md")

    # Parse with schema
    parser = TaskSchemaParser(schema)
    tasks = parser.parse_tasks_file("tasks.md")

    # Test blocking logic
    result = check_task_blocking(tasks[0], tasks)
    assert isinstance(result, tuple)
```

## Migration from v0

### Breaking Changes

1. **Import Changes**
   ```python
   # Old (v0)
   from experimental_parser import parse_tasks

   # New (v2)
   from synapse_cli.parsers import TaskSchemaParser
   ```

2. **Semantic States**
   ```python
   # Old (v0)
   if task.dev_status == "In Progress":

   # New (v2)
   if task.dev_state == "in_progress":
   ```

3. **Schema Loading**
   ```python
   # Old (v0)
   schema = config.get("task_format_schema", {})

   # New (v2)
   tasks_file, schema = find_active_tasks_file(config)
   parser = TaskSchemaParser(schema)
   ```

### Migration Steps

1. Update imports to use `synapse_cli.parsers`
2. Replace status string comparisons with semantic state checks
3. Replace numeric group extraction with named groups
4. Add schema validation error handling
5. Update tests to use ParsedTask objects
6. Test with real workflow

## Performance Considerations

### Parsing Overhead

- **Initial parse**: ~10-50ms for typical tasks files (100-500 tasks)
- **Cached**: Subsequent parses reuse compiled regex patterns
- **Memory**: Minimal - tasks are lightweight dataclass objects

### Optimization Tips

1. **Parse once per hook invocation**
   ```python
   # Good: Parse once
   parsed_tasks = parser.parse_tasks_file(tasks_file)
   for check in blocking_checks:
       check(parsed_tasks)

   # Bad: Parse multiple times
   for check in blocking_checks:
       parsed_tasks = parser.parse_tasks_file(tasks_file)
   ```

2. **Limit sample size for large files**
   ```python
   # SchemaGenerator automatically limits to 500 lines
   generator = SchemaGenerator(max_sample_lines=500)
   ```

3. **Cache parsed tasks between hooks** (future optimization)
   - Store ParsedTask list in memory
   - Invalidate on file modification
   - Skip re-parsing if unchanged

## Future Enhancements

### Planned Features

1. **Multi-field blocking** - Block based on custom fields
2. **Time-based blocking** - Block tasks with deadlines
3. **Dependency blocking** - Block tasks with unmet dependencies
4. **Team-based blocking** - Block tasks assigned to others

### Extensibility

The v2 design supports custom fields and states:

```python
# Custom field in schema
{
  "status_semantics": {
    "fields": ["dev", "qa", "user_verification", "security_review"],
    "field_mapping": {
      "security_review": ["Security Review", "SecReview"]
    },
    "states": {
      "security_review": {
        "not_started": ["Not Started"],
        "complete": ["Approved", "Passed"]
      }
    }
  }
}

# Custom blocking logic
if task.security_review_state != "complete":
    block("Security review required")
```

## Summary

Phase 4 delivers production-ready hooks that:
- ✅ Use robust TaskSchemaParser v2.0
- ✅ Work with semantic states for clean logic
- ✅ Handle errors gracefully with fallback
- ✅ Support any task format (OpenSpec, Spec Kit, custom)
- ✅ Provide clear, actionable error messages

The reference implementation (`pre-tool-use-v2.py`) demonstrates best practices and can be adapted for other hooks (post-tool-use, verification-complete).

---

**Phase 4 Complete** ✅
