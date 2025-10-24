# Task Format Schema v2.0 - Design Specification

**Status**: Phase 1 - Design
**Created**: 2025-10-24
**Version**: 2.0

## Overview

This document defines the structure, semantics, and validation rules for Task Format Schema v2.0, which enables Synapse workflows to dynamically parse any task management format.

---

## Schema Structure

### Complete v2.0 Schema Example

```json
{
  "task_format_schema": {
    "schema_version": "2.0",
    "format_type": "markdown-checklist",

    "patterns": {
      "task_line": {
        "regex": "^\\s*-\\s*\\[([ xX])\\]\\s*-\\s*\\*\\*(?P<task_id>T\\d{3}):\\s*(?P<description>.+?)\\*\\*\\s*$",
        "groups": ["checkbox", "task_id", "description"],
        "example": "- [X] - **T001: Create database schema**",
        "required": true
      },
      "subtask_line": {
        "regex": "^\\s*-\\s*\\[([ xX])\\]\\s*-\\s*(?!\\*\\*)(?P<description>.+?)\\s*$",
        "groups": ["checkbox", "description"],
        "example": "- [X] - Add user table",
        "required": false
      },
      "status_line": {
        "regex": "^\\s*-\\s*\\[([ xX])\\]\\s*-\\s*(?P<field>[^:]+):\\s*\\[(?P<status>[^\\]]+)\\]\\s*$",
        "groups": ["checkbox", "field", "status"],
        "example": "- [X] - Dev Status: [Complete]",
        "required": true
      }
    },

    "status_semantics": {
      "fields": ["dev", "qa", "user_verification"],
      "field_mapping": {
        "dev": ["Dev Status", "Dev", "Development Status", "Development"],
        "qa": ["QA Status", "QA", "Quality Assurance Status", "Testing Status"],
        "user_verification": ["User Verification Status", "User Verification", "UV Status", "Verification"]
      },
      "states": {
        "dev": {
          "not_started": ["Not Started", "Pending", "Todo", "Waiting"],
          "in_progress": ["In Progress", "Working", "Active", "Ongoing", "Implementing"],
          "complete": ["Complete", "Done", "Finished", "Implemented"]
        },
        "qa": {
          "not_started": ["Not Started", "Pending", "Waiting"],
          "in_progress": ["In Progress", "Testing", "Under Review"],
          "complete": ["Complete", "Passed", "Done", "Verified"]
        },
        "user_verification": {
          "not_started": ["Not Started", "Pending", "Waiting"],
          "complete": ["Complete", "Verified", "Done", "Approved"]
        }
      }
    },

    "task_id_format": {
      "prefix": "T",
      "digits": 3,
      "pattern": "T\\d{3}",
      "example": "T001",
      "separator": ""
    },

    "validation": {
      "valid_sample_size": 50,
      "pattern_match_rate": 0.95,
      "last_validated": "2025-10-21T10:30:00Z",
      "validation_passed": true
    },

    "metadata": {
      "analyzed_at": "2025-10-21T10:30:00Z",
      "sample_size": 200,
      "total_tasks_found": 96,
      "confidence": 1.0,
      "format_detected_by": "sense_command",
      "source_file": "specs/feature-name/tasks.md"
    }
  }
}
```

---

## Field Definitions

### Top-Level Fields

#### `schema_version` (required)
- **Type**: String
- **Format**: Semantic versioning (e.g., "2.0", "2.1")
- **Purpose**: Enable schema evolution and backward compatibility
- **Validation**: Must match pattern `^\d+\.\d+$`

#### `format_type` (required)
- **Type**: String
- **Enum**: `"markdown-checklist"`, `"numbered-list"`, `"custom"`
- **Purpose**: Identify the high-level format category
- **Extensible**: New types can be added in future versions

---

### `patterns` Object (required)

Container for regex patterns that identify different line types in task files.

#### Pattern Object Structure
Each pattern key (e.g., `task_line`, `status_line`) must have:

```json
{
  "regex": "string (required)",
  "groups": ["array", "of", "group", "names"] (required),
  "example": "string (required)",
  "required": boolean (optional, default: false)
}
```

**Field Descriptions**:

- **`regex`**: Valid Python regex with named capture groups
  - Must compile without errors
  - Named groups must use `(?P<name>...)` syntax
  - Must not use numbered groups for extraction

- **`groups`**: Ordered list of capture group names in the regex
  - First element is first capture group, etc.
  - Must match named groups in regex
  - Used for documentation and validation

- **`example`**: Real example line from the tasks file
  - Must match the regex pattern
  - Provides human-readable documentation

- **`required`**: Whether this pattern must be present
  - `task_line` and `status_line` are typically required
  - `subtask_line` is typically optional

#### Standard Pattern Keys

1. **`task_line`** (required)
   - Matches main task declarations
   - Must extract: `task_id`, `description`
   - May extract: `checkbox`, `priority`, etc.

2. **`status_line`** (required)
   - Matches status field declarations
   - Must extract: `field`, `status`
   - May extract: `checkbox`

3. **`subtask_line`** (optional)
   - Matches sub-task items under main tasks
   - Must extract: `description`
   - May extract: `checkbox`

---

### `status_semantics` Object (required)

Maps raw status field names and values to semantic categories for consistent business logic.

#### `fields` Array (required)
- **Type**: Array of strings
- **Purpose**: List of semantic field categories
- **Standard values**: `["dev", "qa", "user_verification"]`
- **Extensible**: Projects can add custom fields

#### `field_mapping` Object (required)
Maps semantic field names to possible raw field name variations.

```json
{
  "semantic_field_name": ["Raw Field 1", "Raw Field 2", ...]
}
```

**Example**:
```json
{
  "dev": ["Dev Status", "Dev", "Development Status"],
  "qa": ["QA Status", "Testing Status", "Quality Assurance"]
}
```

**Purpose**: Allows parser to recognize "Dev Status" and "Development Status" as the same semantic field.

#### `states` Object (required)
Maps semantic states to possible raw status value variations for each field.

```json
{
  "semantic_field": {
    "semantic_state": ["Raw Value 1", "Raw Value 2", ...]
  }
}
```

**Standard semantic states**:
- `not_started`: Task hasn't begun
- `in_progress`: Task is actively being worked on
- `complete`: Task is finished

**Example**:
```json
{
  "dev": {
    "not_started": ["Not Started", "Pending", "Todo"],
    "in_progress": ["In Progress", "Working", "Active"],
    "complete": ["Complete", "Done", "Finished"]
  }
}
```

**Special cases**:
- Binary fields (e.g., `user_verification`) may omit `in_progress` state
- Custom fields can define custom states beyond the standard three

---

### `task_id_format` Object (required)

Defines the structure of task identifiers.

#### Fields:

- **`prefix`** (required): String prefix (e.g., "T", "TASK", "BUG")
- **`digits`** (required): Number of digits in numeric portion
- **`pattern`** (required): Regex pattern for task ID (e.g., `"T\\d{3}"`)
- **`example`** (required): Sample task ID (e.g., "T001")
- **`separator`** (optional): Separator between prefix and number (e.g., "-", "_")

**Examples**:
```json
// Simple: T001
{"prefix": "T", "digits": 3, "pattern": "T\\d{3}", "example": "T001", "separator": ""}

// With separator: TASK-001
{"prefix": "TASK", "digits": 3, "pattern": "TASK-\\d{3}", "example": "TASK-001", "separator": "-"}

// Four digits: T0001
{"prefix": "T", "digits": 4, "pattern": "T\\d{4}", "example": "T0001", "separator": ""}
```

---

### `validation` Object (optional)

Records the results of schema validation tests.

#### Fields:

- **`valid_sample_size`**: Number of tasks successfully parsed in validation
- **`pattern_match_rate`**: Percentage of tasks matched (0.0 - 1.0)
- **`last_validated`**: ISO 8601 timestamp of last validation
- **`validation_passed`**: Boolean indicating if validation threshold was met

**Validation criteria**:
- `pattern_match_rate >= 0.95` (95%+ match rate)
- `valid_sample_size >= 10` (at least 10 tasks parsed)

**Example**:
```json
{
  "valid_sample_size": 50,
  "pattern_match_rate": 0.98,
  "last_validated": "2025-10-21T10:30:00Z",
  "validation_passed": true
}
```

---

### `metadata` Object (optional)

Debugging and diagnostic information about schema generation.

#### Fields:

- **`analyzed_at`**: ISO 8601 timestamp when schema was generated
- **`sample_size`**: Number of lines analyzed from tasks file
- **`total_tasks_found`**: Number of task IDs detected
- **`confidence`**: Float 0.0-1.0 indicating schema quality
  - 1.0: High confidence (>50 tasks, 95%+ match rate)
  - 0.8-0.99: Medium confidence (10-50 tasks, 90%+ match rate)
  - <0.8: Low confidence (manual review recommended)
- **`format_detected_by`**: How format was determined ("sense_command", "manual", "default")
- **`source_file`**: Path to the tasks file analyzed

---

## Schema Versions

### Version History

| Version | Status | Changes |
|---------|--------|---------|
| 0.0 | Experimental | Initial proof-of-concept in `experiments/` |
| 1.0 | (Reserved) | Not used |
| 2.0 | Current | Production-ready with validation and semantics |

### Supported Versions

Parsers MUST support:
- v2.0 (current)

Parsers MAY support:
- v0.0 (experimental) with automatic migration

### Version Compatibility

- Breaking changes require major version bump (2.0 → 3.0)
- New optional fields can be added in minor versions (2.0 → 2.1)
- Parsers should validate version and reject unsupported versions

---

## Design Rationale

### Why Named Groups in Patterns?

**Problem**: v0 used numeric group positions (`group(2)`, `group(3)`), causing mismatches when patterns changed.

**Solution**: v2 requires named groups and documents them in the `groups` array.

```python
# v0 - Fragile
match.group(2)  # Which field is this?

# v2 - Clear
match.group("task_id")  # Explicit and self-documenting
```

### Why Semantic Status Mapping?

**Problem**: v0 used array positions to assign meaning:
```json
["Not Started", "In Progress", "Complete"]
 ↑ position 0    ↑ position 1    ↑ position 2
```

If extraction order changed (e.g., alphabetical), business logic broke.

**Solution**: v2 explicitly maps raw values to semantic states:
```json
{
  "not_started": ["Not Started", "Pending"],
  "in_progress": ["In Progress", "Working"],
  "complete": ["Complete", "Done"]
}
```

### Why Field Mapping?

**Problem**: Different projects use different field names:
- "Dev Status" vs "Development Status" vs "Dev"
- "QA Status" vs "Testing Status" vs "Quality Assurance"

**Solution**: Map all variations to a single semantic category:
```json
{
  "dev": ["Dev Status", "Dev", "Development Status"]
}
```

Business logic works with semantic names (`dev`, `qa`), agnostic to raw field names.

### Why Validation Metadata?

**Problem**: No way to know if generated schema actually works.

**Solution**: Validate schema by re-parsing tasks and record success rate:
```json
{
  "validation": {
    "pattern_match_rate": 0.98,
    "validation_passed": true
  }
}
```

---

## Format Type Definitions

### `markdown-checklist`

Task files using markdown checkbox syntax.

**Characteristics**:
- Lines start with `- [ ]` or `- [x]`
- Task IDs in bold: `**T001: Description**`
- Status fields: `- [ ] - Field: [Value]`

**Example**:
```markdown
- [ ] - **T001: Create user table**
- [ ] - Dev Status: [Not Started]
- [ ] - QA Status: [Not Started]
```

### `numbered-list`

Task files using numbered list syntax.

**Characteristics**:
- Lines start with `1.`, `2.`, etc.
- Task IDs in bold: `**T001: Description**`
- Status fields may use brackets or plain text

**Example**:
```markdown
1. **T001: Create user table**
   - Dev Status: [Not Started]
   - QA Status: [Not Started]
```

### `custom`

Non-standard or hybrid formats.

**Characteristics**:
- Uses project-specific syntax
- May combine elements of multiple formats
- Requires manual pattern tuning

---

## Extensibility

### Adding Custom Fields

Projects can define custom status fields beyond `dev`, `qa`, `user_verification`:

```json
{
  "status_semantics": {
    "fields": ["dev", "qa", "user_verification", "security_review", "performance_test"],
    "field_mapping": {
      "security_review": ["Security Review", "SecReview"],
      "performance_test": ["Performance Test", "Perf Test"]
    },
    "states": {
      "security_review": {
        "not_started": ["Not Started"],
        "complete": ["Passed", "Approved"]
      }
    }
  }
}
```

### Adding Custom States

Fields can define states beyond the standard three:

```json
{
  "dev": {
    "not_started": ["Not Started"],
    "planning": ["Planning", "Designing"],
    "in_progress": ["In Progress"],
    "blocked": ["Blocked", "On Hold"],
    "complete": ["Complete"]
  }
}
```

Business logic should handle unknown states gracefully (treat as `not_started` or skip).

---

## Migration from v0

### Key Changes

| Aspect | v0 | v2 |
|--------|----|----|
| Versioning | None | `schema_version: "2.0"` |
| Pattern format | String | Object with `regex`, `groups`, `example` |
| Status values | Array (positional) | Object with semantic mapping |
| Field mapping | None | Explicit mapping to semantic categories |
| Validation | None | Recorded validation results |

### Migration Strategy

1. **Detect v0 schema**: Missing `schema_version` field
2. **Extract patterns**: Convert string patterns to objects
3. **Add named groups**: Update regex if needed
4. **Convert status arrays**: Map position 0→not_started, 1→in_progress, 2→complete
5. **Add field mapping**: Create standard mapping for dev/qa/user_verification
6. **Set version**: `schema_version: "2.0"`
7. **Validate**: Re-parse tasks to ensure migration worked

See `docs/schema-migration-guide.md` for detailed migration steps.

---

## Next Steps

- [x] T001: Design schema v2 structure
- [ ] T002: Define schema validation rules
- [ ] T003: Create schema migration strategy
