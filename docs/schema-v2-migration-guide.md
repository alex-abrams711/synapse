# Task Format Schema v2.0 - Migration Guide

**Status**: Phase 1 - Design
**Created**: 2025-10-24
**Version**: 2.0

## Overview

This document provides a comprehensive strategy for migrating Task Format Schemas from experimental v0 format to production v2.0 format.

---

## Migration Overview

### What's Changing

| Component | v0 (Experimental) | v2.0 (Production) |
|-----------|-------------------|-------------------|
| Version field | None | `schema_version: "2.0"` required |
| Pattern format | String regex | Object with `{regex, groups, example}` |
| Status values | Array (positional) | Object (semantic mapping) |
| Field mapping | Implicit | Explicit `field_mapping` object |
| Validation | None | Optional `validation` results |
| Metadata | Minimal | Enhanced diagnostics |

### Migration Types

1. **Automatic Migration**: System detects v0 and auto-migrates
2. **Manual Migration**: User runs `synapse sense --migrate`
3. **Fresh Generation**: User runs `synapse sense` to regenerate

---

## Detecting v0 Schemas

### Detection Algorithm

```python
def detect_schema_version(schema: Dict) -> str:
    """
    Detect schema version from structure

    Returns: "0.0", "2.0", or "unknown"
    """
    # Explicit version field
    if "schema_version" in schema:
        return schema["schema_version"]

    # v0 detection: has patterns but no schema_version
    if "patterns" in schema and "status_values" in schema:
        # Check for v0 characteristics
        patterns = schema["patterns"]

        # v0 patterns are strings, not objects
        if isinstance(patterns.get("task_line"), str):
            return "0.0"

        # v0 has status_values as arrays
        status_values = schema.get("status_values", {})
        if any(isinstance(v, list) for v in status_values.values()):
            return "0.0"

    return "unknown"
```

### v0 Schema Characteristics

Identifying features:
- Missing `schema_version` field
- `patterns` values are strings (not objects)
- `status_values` object with array values
- Has `structure` object with `task_id_prefix`, `task_id_digits`
- Missing `field_mapping` in `status_semantics`

---

## Migration Strategy

### Step-by-Step Process

#### Step 1: Backup Current Config

Before any migration, create backup:

```bash
# Automatic backup
cp .synapse/config.json .synapse/config.json.backup-$(date +%Y%m%d-%H%M%S)

# Or use synapse command
synapse config backup
```

#### Step 2: Detect Schema Version

```python
config = load_config(".synapse/config.json")
workflows = config.get("third_party_workflows", {}).get("detected", [])

for workflow in workflows:
    schema = workflow.get("task_format_schema")
    if schema:
        version = detect_schema_version(schema)
        print(f"Detected schema version: {version}")
```

#### Step 3: Migrate v0 → v2

Apply migration transformations:

```python
if version == "0.0":
    migrated_schema = migrate_v0_to_v2(schema)
    workflow["task_format_schema"] = migrated_schema
```

#### Step 4: Validate Migrated Schema

```python
from synapse_cli.parsers.task_schema_parser import TaskSchemaParser

try:
    parser = TaskSchemaParser(migrated_schema)
    print("✅ Migration validation passed")
except SchemaValidationError as e:
    print(f"❌ Migration validation failed: {e}")
    # Rollback
    restore_backup()
```

#### Step 5: Functional Testing

Test migrated schema by parsing tasks:

```python
tasks_file = workflow.get("active_tasks_file")
if tasks_file and os.path.exists(tasks_file):
    parsed_tasks = parser.parse_tasks_file(tasks_file)
    match_rate = len(parsed_tasks) / expected_task_count

    if match_rate >= 0.95:
        print(f"✅ Functional test passed: {match_rate:.1%} match rate")
    else:
        print(f"⚠️  Low match rate: {match_rate:.1%}")
```

#### Step 6: Save Migrated Config

```python
with open(".synapse/config.json", 'w') as f:
    json.dump(config, f, indent=2)

print("✅ Migration complete")
```

---

## Migration Algorithm

### Complete Migration Function

```python
def migrate_v0_to_v2(v0_schema: Dict) -> Dict:
    """
    Migrate v0 experimental schema to v2 production schema

    Args:
        v0_schema: Experimental schema from experiments/

    Returns:
        v2_schema: Production-ready v2.0 schema
    """
    v2_schema = {
        "schema_version": "2.0",
        "format_type": v0_schema.get("format_type", "markdown-checklist")
    }

    # Migrate patterns
    v2_schema["patterns"] = migrate_patterns(v0_schema.get("patterns", {}))

    # Migrate status semantics
    v2_schema["status_semantics"] = migrate_status_semantics(
        v0_schema.get("status_values", {}),
        v0_schema.get("structure", {})
    )

    # Migrate task ID format
    v2_schema["task_id_format"] = migrate_task_id_format(
        v0_schema.get("structure", {}),
        v0_schema.get("patterns", {})
    )

    # Preserve metadata
    if "metadata" in v0_schema:
        v2_schema["metadata"] = v0_schema["metadata"].copy()
        v2_schema["metadata"]["migrated_at"] = datetime.now().isoformat()
        v2_schema["metadata"]["migrated_from"] = "0.0"

    return v2_schema
```

### Pattern Migration

```python
def migrate_patterns(v0_patterns: Dict) -> Dict:
    """
    Convert v0 string patterns to v2 pattern objects

    v0: {"task_line": "^\\[([ xX])\\] - \\*\\*(T\\d+):\\s*(.*?)\\*\\*"}
    v2: {"task_line": {"regex": "...", "groups": [...], "example": "..."}}
    """
    v2_patterns = {}

    # Task line pattern
    if "task_line" in v0_patterns:
        task_regex = v0_patterns["task_line"]

        # Add named groups if not present
        if "(?P<task_id>" not in task_regex:
            # Convert numbered groups to named groups
            # Original: ^\\[([ xX])\\] - \\*\\*(T\\d+):\\s*(.*?)\\*\\*
            # Updated:  ^\\[([ xX])\\] - \\*\\*(?P<task_id>T\\d+):\\s*(?P<description>.*?)\\*\\*
            task_regex = re.sub(
                r'\(T\\d\+\)',
                r'(?P<task_id>T\\d+)',
                task_regex
            )
            task_regex = re.sub(
                r'\(\.\*\?\)(?!>)',  # Find (.*?) not preceded by (?P<name>
                r'(?P<description>.*?)',
                task_regex
            )

        v2_patterns["task_line"] = {
            "regex": task_regex,
            "groups": ["checkbox", "task_id", "description"],
            "example": "- [X] - **T001: Create database schema**",
            "required": True
        }

    # Status line pattern
    if "status_line" in v0_patterns:
        status_regex = v0_patterns["status_line"]

        # Add named groups if not present
        if "(?P<field>" not in status_regex:
            # Detect field names pattern and convert
            status_regex = re.sub(
                r'\(Dev Status\|QA Status\|User Verification Status\)',
                r'(?P<field>Dev Status|QA Status|User Verification Status)',
                status_regex
            )
            status_regex = re.sub(
                r'\(\[\^\\\]\]\+\)',
                r'(?P<status>[^\\]]+)',
                status_regex
            )

        v2_patterns["status_line"] = {
            "regex": status_regex,
            "groups": ["checkbox", "field", "status"],
            "example": "- [X] - Dev Status: [Complete]",
            "required": True
        }

    # Subtask line pattern
    if "subtask_line" in v0_patterns:
        subtask_regex = v0_patterns["subtask_line"]

        v2_patterns["subtask_line"] = {
            "regex": subtask_regex,
            "groups": ["checkbox", "description"],
            "example": "- [X] - Add user table",
            "required": False
        }

    return v2_patterns
```

### Status Semantics Migration

```python
def migrate_status_semantics(v0_status_values: Dict, v0_structure: Dict) -> Dict:
    """
    Convert v0 positional status arrays to v2 semantic mappings

    v0:
    {
      "dev": ["Not Started", "In Progress", "Complete"],
      "qa": ["Not Started", "In Progress", "Complete"]
    }

    v2:
    {
      "fields": ["dev", "qa", "user_verification"],
      "field_mapping": {...},
      "states": {
        "dev": {
          "not_started": ["Not Started"],
          "in_progress": ["In Progress"],
          "complete": ["Complete"]
        }
      }
    }
    """
    fields = list(v0_status_values.keys())

    # Build field mapping from structure
    field_mapping = {}
    status_fields = v0_structure.get("status_fields", [])

    for semantic_field in fields:
        # Find corresponding raw field names
        raw_fields = [
            f for f in status_fields
            if semantic_field in f.lower().replace(" ", "_")
        ]

        if not raw_fields:
            # Fallback: capitalize semantic field
            if semantic_field == "dev":
                raw_fields = ["Dev Status", "Dev"]
            elif semantic_field == "qa":
                raw_fields = ["QA Status", "QA"]
            elif semantic_field == "user_verification":
                raw_fields = ["User Verification Status", "User Verification"]
            else:
                raw_fields = [semantic_field.replace("_", " ").title()]

        field_mapping[semantic_field] = raw_fields

    # Convert status arrays to semantic state mappings
    states = {}

    for field, values in v0_status_values.items():
        if not isinstance(values, list):
            continue

        field_states = {}

        # Map array positions to semantic states
        if len(values) >= 1:
            field_states["not_started"] = [values[0]]

        if len(values) >= 2:
            # Check if second value is "In Progress" or "Complete"
            second_val_lower = values[1].lower()
            if "progress" in second_val_lower or "working" in second_val_lower:
                field_states["in_progress"] = [values[1]]
                if len(values) >= 3:
                    field_states["complete"] = [values[2]]
            else:
                # Binary field (no in_progress state)
                field_states["complete"] = [values[1]]
        elif len(values) == 2:
            # Binary field
            field_states["complete"] = [values[1]]

        if len(values) >= 3 and "complete" not in field_states:
            field_states["complete"] = [values[2]]

        states[field] = field_states

    return {
        "fields": fields,
        "field_mapping": field_mapping,
        "states": states
    }
```

### Task ID Format Migration

```python
def migrate_task_id_format(v0_structure: Dict, v0_patterns: Dict) -> Dict:
    """
    Extract task ID format from v0 structure

    v0:
    {
      "structure": {
        "task_id_prefix": "T",
        "task_id_digits": 3
      },
      "patterns": {
        "task_id_format": "T\\d{3}"
      }
    }

    v2:
    {
      "prefix": "T",
      "digits": 3,
      "pattern": "T\\d{3}",
      "example": "T001",
      "separator": ""
    }
    """
    prefix = v0_structure.get("task_id_prefix", "T")
    digits = v0_structure.get("task_id_digits", 3)

    # Get pattern from patterns dict or construct
    pattern = v0_patterns.get("task_id_format")
    if not pattern:
        pattern = f"{prefix}\\d{{{digits}}}"

    # Generate example
    example = f"{prefix}{str(1).zfill(digits)}"

    # Detect separator
    separator = ""
    if "-" in pattern:
        separator = "-"
    elif "_" in pattern:
        separator = "_"

    return {
        "prefix": prefix,
        "digits": digits,
        "pattern": pattern,
        "example": example,
        "separator": separator
    }
```

---

## Migration Commands

### CLI Integration

```bash
# Check if migration needed
synapse sense --check-migration

# Migrate schema (with backup)
synapse sense --migrate

# Migrate and validate
synapse sense --migrate --validate

# Regenerate schema from scratch (recommended)
synapse sense --regenerate
```

### Command Output Examples

#### Check Migration

```bash
$ synapse sense --check-migration

🔍 Checking schema version...

Found schema in workflow: custom-specs-workflow
  Current version: 0.0 (experimental)
  Latest version: 2.0

⚠️  Migration recommended

Run: synapse sense --migrate
```

#### Migrate

```bash
$ synapse sense --migrate

🔄 Migrating schema...

✅ Backup created: .synapse/config.json.backup-20251024-143022
🔍 Detected schema version: 0.0
📝 Migrating to v2.0...
  ✓ Patterns migrated (3 patterns)
  ✓ Status semantics migrated (3 fields)
  ✓ Task ID format migrated
✅ Schema validation passed
🧪 Testing with tasks file...
  ✓ Parsed 96/96 tasks (100% match rate)

✅ Migration complete

Schema version: 0.0 → 2.0
```

#### Regenerate (Recommended)

```bash
$ synapse sense --regenerate

🔄 Regenerating schema from tasks file...

✅ Backup created: .synapse/config.json.backup-20251024-143045
📖 Reading tasks file: specs/feature/tasks.md
  Sample size: 200 lines
  Tasks found: 96
🔍 Analyzing format...
  Format type: markdown-checklist
  Task ID pattern: T\d{3}
  Status fields: 3 (Dev Status, QA Status, User Verification Status)
✅ Schema generated
🧪 Validating schema...
  ✓ Parsed 96/96 tasks (100% match rate)

✅ Schema generation complete

Schema version: 2.0
Confidence: 1.0
```

---

## Breaking Changes

### 1. Pattern Structure Change

**v0**: Patterns are strings
```json
{
  "patterns": {
    "task_line": "^\\[([ xX])\\] - \\*\\*(?P<task_id>T\\d+):\\s*(?P<description>.*?)\\*\\*"
  }
}
```

**v2**: Patterns are objects
```json
{
  "patterns": {
    "task_line": {
      "regex": "^\\[([ xX])\\] - \\*\\*(?P<task_id>T\\d+):\\s*(?P<description>.*?)\\*\\*",
      "groups": ["checkbox", "task_id", "description"],
      "example": "- [X] - **T001: Task**"
    }
  }
}
```

**Impact**: Code accessing `schema["patterns"]["task_line"]` directly will break

**Migration**: Update code to access `schema["patterns"]["task_line"]["regex"]`

### 2. Status Values Array → Object

**v0**: Positional arrays
```json
{
  "status_values": {
    "dev": ["Not Started", "In Progress", "Complete"]
  }
}
```

**v2**: Semantic mapping object
```json
{
  "status_semantics": {
    "states": {
      "dev": {
        "not_started": ["Not Started"],
        "in_progress": ["In Progress"],
        "complete": ["Complete"]
      }
    }
  }
}
```

**Impact**: Code using array indices will break

**Migration**: Use semantic state names instead of positions

### 3. Field Mapping Required

**v0**: Field names hardcoded in business logic
```python
if status_field == "Dev Status":
    # ...
elif status_field == "Development Status":
    # ...
```

**v2**: Field mapping required in schema
```json
{
  "status_semantics": {
    "field_mapping": {
      "dev": ["Dev Status", "Development Status"]
    }
  }
}
```

**Impact**: Schemas without field mapping are invalid

**Migration**: Add field_mapping or regenerate schema

### 4. Schema Version Required

**v0**: No version field

**v2**: `schema_version: "2.0"` required

**Impact**: Schemas without version will be rejected

**Migration**: Add version field or regenerate

---

## Rollback Strategy

### If Migration Fails

```bash
# Restore from automatic backup
cp .synapse/config.json.backup-TIMESTAMP .synapse/config.json

# Or use synapse command
synapse config restore --backup .synapse/config.json.backup-TIMESTAMP

# Verify restoration
synapse sense --check-migration
```

### If Parsing Fails After Migration

```bash
# Regenerate schema from scratch
synapse sense --regenerate

# Or restore and get help
synapse config restore --latest
synapse sense --debug
```

---

## Testing Migration

### Manual Testing Checklist

After migration, verify:

- [ ] Schema validation passes: `synapse sense --validate`
- [ ] Tasks parse correctly: Check match rate ≥ 95%
- [ ] Hooks work: Test blocking logic with implementer agent
- [ ] Semantic states map correctly: Verify "Complete" → `complete`
- [ ] Field mapping works: Test with various field name formats

### Automated Testing

```bash
# Run migration test suite
pytest tests/test_schema_migration.py

# Test end-to-end workflow
pytest tests/e2e/test_v0_to_v2_migration.py
```

### Test Cases

1. **Minimal v0 schema**: Only required fields
2. **Full v0 schema**: All optional fields present
3. **Binary status field**: user_verification with 2 values
4. **Custom task ID format**: TASK-001 instead of T001
5. **Multiple field name variations**: "Dev Status", "Dev", "Development Status"

---

## Migration Timeline

### Phase 1: Preparation (Week 1)
- Announce migration in docs
- Create backup strategy
- Build migration utilities

### Phase 2: Testing (Week 2)
- Test migration with experimental schemas
- Validate with real projects
- Fix migration bugs

### Phase 3: Rollout (Week 3)
- Release migration command
- Provide migration guide
- Monitor for issues

### Phase 4: Deprecation (Month 2+)
- Mark v0 as deprecated
- Encourage regeneration over migration
- Remove v0 support in future version

---

## FAQ

### Q: Should I migrate or regenerate?

**A**: Regenerate is recommended. It produces cleaner schemas and validates against current task files.

```bash
# Recommended
synapse sense --regenerate

# Only if you need to preserve custom changes
synapse sense --migrate
```

### Q: Will migration break my hooks?

**A**: Updated hooks in v2.0 use the new schema format. Old hooks will break.

**Solution**: Update hooks to use `TaskSchemaParser` class (provided in Phase 2).

### Q: Can I keep using v0?

**A**: No. v0 is experimental and will not be supported in production releases.

### Q: What if migration fails?

**A**: Automatic backup is created. Restore with:
```bash
synapse config restore --latest
```

### Q: Do I need to migrate multiple times?

**A**: No. Once migrated to v2.0, future updates will be handled automatically.

---

## Next Steps

- [x] T001: Design schema v2 structure
- [x] T002: Define schema validation rules
- [x] T003: Create schema migration strategy

**Phase 1 Complete** ✅

Ready for review and approval to proceed to Phase 2 (Parser Implementation).
