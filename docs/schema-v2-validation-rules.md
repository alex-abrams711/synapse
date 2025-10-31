# Task Format Schema v2.0 - Validation Rules

**Status**: Phase 1 - Design
**Created**: 2025-10-24
**Version**: 2.0

## Overview

This document defines comprehensive validation rules for Task Format Schema v2.0, including required fields, data types, value constraints, and validation thresholds.

---

## Validation Levels

### Level 1: Structural Validation
Validates schema structure, required fields, and data types.

### Level 2: Semantic Validation
Validates regex patterns compile, groups match, and semantic mappings are consistent.

### Level 3: Functional Validation
Validates schema works by parsing real tasks and measuring success rate.

---

## Required Fields

### Top-Level Required Fields

| Field Path | Type | Validation Rule |
|------------|------|-----------------|
| `schema_version` | String | Must match pattern `^\d+\.\d+$` |
| `format_type` | String | Must be one of: `"markdown-checklist"`, `"numbered-list"`, `"custom"` |
| `patterns` | Object | Must contain at least `task_line` and `status_line` |
| `status_semantics` | Object | Must contain `fields`, `field_mapping`, and `states` |
| `task_id_format` | Object | Must contain `prefix`, `digits`, `pattern`, and `example` |

### Optional Top-Level Fields

| Field Path | Type | Purpose |
|------------|------|---------|
| `validation` | Object | Records validation test results |
| `metadata` | Object | Debugging and diagnostic information |

---

## Field-Level Validation Rules

### `schema_version`

**Type**: String

**Rules**:
- MUST match regex: `^\d+\.\d+$`
- MUST be in supported versions list
- MUST NOT be empty

**Supported Versions**:
- `"2.0"` (current)
- Future versions will be added here

**Error Messages**:
```python
# Invalid format
"Invalid schema_version format: '{value}'. Expected format: 'X.Y' (e.g., '2.0')"

# Unsupported version
"Unsupported schema_version: '{value}'. Supported versions: {supported_list}"

# Missing
"Missing required field: 'schema_version'"
```

---

### `format_type`

**Type**: String (enum)

**Rules**:
- MUST be one of: `"markdown-checklist"`, `"numbered-list"`, `"custom"`
- MUST NOT be empty

**Error Messages**:
```python
"Invalid format_type: '{value}'. Must be one of: markdown-checklist, numbered-list, custom"
```

---

### `patterns` Object

**Type**: Object

**Rules**:
- MUST contain key `task_line`
- MUST contain key `status_line`
- MAY contain additional pattern keys (e.g., `subtask_line`)
- Each pattern key MUST map to a valid Pattern Object

**Error Messages**:
```python
"Missing required pattern: '{pattern_name}'"
"Invalid pattern structure for '{pattern_name}': must be an object"
```

---

### Pattern Object

**Type**: Object

**Required Fields**:
| Field | Type | Validation |
|-------|------|------------|
| `regex` | String | Must compile as valid Python regex |
| `groups` | Array[String] | Must list all capture group names in order |
| `example` | String | Must match the regex pattern |

**Optional Fields**:
| Field | Type | Default | Validation |
|-------|------|---------|------------|
| `required` | Boolean | false | Must be true or false |

#### `regex` Field Validation

**Rules**:
- MUST be a valid Python regex (compile without errors)
- MUST use named capture groups: `(?P<name>...)`
- MUST NOT use numbered groups for extraction
- SHOULD escape special characters correctly

**Error Messages**:
```python
# Compilation error
"Invalid regex in pattern '{pattern_name}': {regex_error}"

# No named groups
"Pattern '{pattern_name}' must use named capture groups (?P<name>...)"

# Example
"Invalid regex: unbalanced parenthesis at position 15"
```

**Validation Algorithm**:
```python
import re

def validate_regex(pattern_name: str, regex: str) -> Tuple[bool, str]:
    try:
        compiled = re.compile(regex)
        # Check for named groups
        if not compiled.groupindex:
            return False, f"Pattern '{pattern_name}' has no named capture groups"
        return True, ""
    except re.error as e:
        return False, f"Invalid regex in pattern '{pattern_name}': {e}"
```

#### `groups` Field Validation

**Rules**:
- MUST be a non-empty array
- All elements MUST be strings
- All elements MUST correspond to named groups in the regex

**Error Messages**:
```python
"Pattern '{pattern_name}' groups field must be a non-empty array"
"Group '{group_name}' listed in groups array but not found in regex"
"Named group '{group_name}' in regex but not listed in groups array"
```

**Validation Algorithm**:
```python
def validate_groups(pattern_name: str, regex: str, groups: List[str]) -> Tuple[bool, str]:
    if not isinstance(groups, list) or len(groups) == 0:
        return False, f"Pattern '{pattern_name}' groups must be non-empty array"

    compiled = re.compile(regex)
    regex_groups = set(compiled.groupindex.keys())
    declared_groups = set(groups)

    # Check all declared groups exist in regex
    missing = declared_groups - regex_groups
    if missing:
        return False, f"Groups {missing} declared but not in regex for '{pattern_name}'"

    # Warn about undeclared groups (not an error)
    undeclared = regex_groups - declared_groups
    if undeclared:
        print(f"⚠️  Pattern '{pattern_name}' has undeclared groups: {undeclared}")

    return True, ""
```

#### `example` Field Validation

**Rules**:
- MUST be a non-empty string
- MUST match the regex pattern
- SHOULD be a real example from the tasks file

**Error Messages**:
```python
"Pattern '{pattern_name}' example is empty"
"Pattern '{pattern_name}' example does not match its regex"
```

**Validation Algorithm**:
```python
def validate_example(pattern_name: str, regex: str, example: str) -> Tuple[bool, str]:
    if not example or not example.strip():
        return False, f"Pattern '{pattern_name}' example is empty"

    compiled = re.compile(regex)
    if not compiled.match(example):
        return False, f"Pattern '{pattern_name}' example does not match regex"

    return True, ""
```

---

### `status_semantics` Object

**Type**: Object

**Required Fields**:
| Field | Type | Validation |
|-------|------|------------|
| `fields` | Array[String] | Non-empty array of semantic field names |
| `field_mapping` | Object | Maps semantic names to raw name variations |
| `states` | Object | Maps semantic fields to state mappings |

#### `fields` Array Validation

**Rules**:
- MUST be a non-empty array
- All elements MUST be strings
- All elements MUST be valid identifiers (alphanumeric + underscore)
- SHOULD include standard fields: `["dev", "qa", "user_verification"]`

**Error Messages**:
```python
"status_semantics.fields must be a non-empty array"
"Invalid field name '{field}': must be alphanumeric + underscore only"
```

#### `field_mapping` Object Validation

**Rules**:
- MUST contain an entry for each field in `fields` array
- Each entry MUST map to a non-empty array of strings
- Raw field names MUST be unique (no field appears in multiple mappings)

**Error Messages**:
```python
"field_mapping missing entry for semantic field '{field}'"
"field_mapping['{field}'] must be a non-empty array of strings"
"Raw field '{raw_field}' appears in multiple mappings: {semantic_fields}"
```

**Validation Algorithm**:
```python
def validate_field_mapping(fields: List[str], field_mapping: Dict[str, List[str]]) -> Tuple[bool, str]:
    # Check all semantic fields have mappings
    for field in fields:
        if field not in field_mapping:
            return False, f"field_mapping missing entry for '{field}'"

        mappings = field_mapping[field]
        if not isinstance(mappings, list) or len(mappings) == 0:
            return False, f"field_mapping['{field}'] must be non-empty array"

    # Check for duplicate raw field names
    seen = {}
    for semantic, raw_fields in field_mapping.items():
        for raw_field in raw_fields:
            if raw_field in seen:
                return False, f"Raw field '{raw_field}' in both '{seen[raw_field]}' and '{semantic}'"
            seen[raw_field] = semantic

    return True, ""
```

#### `states` Object Validation

**Rules**:
- MUST contain an entry for each field in `fields` array
- Each entry MUST map to a State Mapping Object
- State Mapping MUST contain at least `not_started` and `complete` keys
- MAY contain `in_progress` key (binary fields like user_verification may omit)

**Error Messages**:
```python
"states missing entry for field '{field}'"
"states['{field}'] must contain 'not_started' and 'complete' keys"
"states['{field}']['{state}'] must be a non-empty array of strings"
```

**State Mapping Object**:
```json
{
  "not_started": ["Value1", "Value2", ...],
  "in_progress": ["Value1", "Value2", ...],  // Optional
  "complete": ["Value1", "Value2", ...]
}
```

**Validation Algorithm**:
```python
def validate_states(fields: List[str], states: Dict) -> Tuple[bool, str]:
    for field in fields:
        if field not in states:
            return False, f"states missing entry for field '{field}'"

        state_mapping = states[field]

        # Check required states
        if "not_started" not in state_mapping:
            return False, f"states['{field}'] missing 'not_started'"
        if "complete" not in state_mapping:
            return False, f"states['{field}'] missing 'complete'"

        # Validate each state has non-empty array
        for state, values in state_mapping.items():
            if not isinstance(values, list) or len(values) == 0:
                return False, f"states['{field}']['{state}'] must be non-empty array"

    return True, ""
```

---

### `task_id_format` Object

**Type**: Object

**Required Fields**:
| Field | Type | Validation |
|-------|------|------------|
| `prefix` | String | Non-empty string, typically uppercase letters |
| `digits` | Integer | Positive integer (typically 1-5) |
| `pattern` | String | Valid regex matching task ID format |
| `example` | String | Must match the pattern |

**Optional Fields**:
| Field | Type | Default | Validation |
|-------|------|---------|------------|
| `separator` | String | "" | String (may be empty) |

**Validation Rules**:
```python
def validate_task_id_format(fmt: Dict) -> Tuple[bool, str]:
    # Check required fields
    required = ["prefix", "digits", "pattern", "example"]
    for field in required:
        if field not in fmt:
            return False, f"task_id_format missing required field '{field}'"

    # Validate prefix
    prefix = fmt["prefix"]
    if not prefix or not isinstance(prefix, str):
        return False, "task_id_format.prefix must be non-empty string"

    # Validate digits
    digits = fmt["digits"]
    if not isinstance(digits, int) or digits < 1:
        return False, "task_id_format.digits must be positive integer"

    # Validate pattern compiles
    try:
        compiled = re.compile(fmt["pattern"])
    except re.error as e:
        return False, f"task_id_format.pattern invalid regex: {e}"

    # Validate example matches pattern
    if not compiled.match(fmt["example"]):
        return False, "task_id_format.example does not match pattern"

    return True, ""
```

---

### `validation` Object (Optional)

**Type**: Object

**Fields**:
| Field | Type | Validation |
|-------|------|------------|
| `valid_sample_size` | Integer | Non-negative integer |
| `pattern_match_rate` | Float | Between 0.0 and 1.0 inclusive |
| `last_validated` | String | ISO 8601 timestamp |
| `validation_passed` | Boolean | Must be boolean |

**Validation Rules**:
```python
def validate_validation_object(val: Dict) -> Tuple[bool, str]:
    if "pattern_match_rate" in val:
        rate = val["pattern_match_rate"]
        if not isinstance(rate, (int, float)) or not (0.0 <= rate <= 1.0):
            return False, "pattern_match_rate must be between 0.0 and 1.0"

    if "valid_sample_size" in val:
        size = val["valid_sample_size"]
        if not isinstance(size, int) or size < 0:
            return False, "valid_sample_size must be non-negative integer"

    if "last_validated" in val:
        # Validate ISO 8601 format
        try:
            from datetime import datetime
            datetime.fromisoformat(val["last_validated"].replace('Z', '+00:00'))
        except ValueError:
            return False, "last_validated must be ISO 8601 timestamp"

    return True, ""
```

---

### `metadata` Object (Optional)

**Type**: Object

**Fields**: All optional, no strict validation

**Common Fields**:
- `analyzed_at`: ISO 8601 timestamp
- `sample_size`: Non-negative integer
- `total_tasks_found`: Non-negative integer
- `confidence`: Float between 0.0 and 1.0
- `format_detected_by`: String
- `source_file`: String (file path)

---

## Validation Thresholds

### Schema Quality Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Pattern match rate | ≥ 95% | Required for validation to pass |
| Sample size | ≥ 10 tasks | Minimum for meaningful validation |
| Confidence | ≥ 0.8 | Recommended minimum (0.8-1.0) |

### Confidence Scoring

```python
def calculate_confidence(
    total_tasks: int,
    pattern_match_rate: float,
    has_validation: bool
) -> float:
    """
    Calculate schema confidence score (0.0 - 1.0)

    Factors:
    - Number of tasks analyzed
    - Pattern match rate
    - Whether validation was performed
    """
    if not has_validation:
        return 0.5  # Unvalidated schemas get medium confidence

    # Base confidence from task count
    if total_tasks >= 50:
        task_confidence = 1.0
    elif total_tasks >= 10:
        task_confidence = 0.7 + (total_tasks - 10) / 40 * 0.3
    else:
        task_confidence = 0.5 + (total_tasks / 10) * 0.2

    # Weight match rate heavily
    match_confidence = pattern_match_rate

    # Combine (60% match rate, 40% task count)
    return match_confidence * 0.6 + task_confidence * 0.4
```

---

## Complete Validation Algorithm

### ValidationResult Class

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ValidationError:
    level: str  # "error" | "warning"
    field_path: str
    message: str

@dataclass
class ValidationResult:
    valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]

    def add_error(self, field_path: str, message: str):
        self.valid = False
        self.errors.append(ValidationError("error", field_path, message))

    def add_warning(self, field_path: str, message: str):
        self.warnings.append(ValidationError("warning", field_path, message))
```

### Main Validation Function

```python
def validate_schema(schema: Dict) -> ValidationResult:
    """
    Comprehensive schema validation

    Returns ValidationResult with errors and warnings
    """
    result = ValidationResult(valid=True, errors=[], warnings=[])

    # Level 1: Structural Validation

    # Check schema_version
    if "schema_version" not in schema:
        result.add_error("schema_version", "Missing required field")
        return result  # Cannot continue without version

    version = schema["schema_version"]
    if not re.match(r'^\d+\.\d+$', version):
        result.add_error("schema_version", f"Invalid format: '{version}'")
        return result

    if version not in ["2.0"]:
        result.add_error("schema_version", f"Unsupported version: '{version}'")
        return result

    # Check format_type
    if "format_type" not in schema:
        result.add_error("format_type", "Missing required field")
    elif schema["format_type"] not in ["markdown-checklist", "numbered-list", "custom"]:
        result.add_error("format_type", f"Invalid value: '{schema['format_type']}'")

    # Check patterns
    if "patterns" not in schema:
        result.add_error("patterns", "Missing required field")
    else:
        patterns = schema["patterns"]

        # Validate required patterns exist
        for required in ["task_line", "status_line"]:
            if required not in patterns:
                result.add_error(f"patterns.{required}", "Missing required pattern")

        # Validate each pattern
        for pattern_name, pattern_obj in patterns.items():
            validate_pattern(pattern_name, pattern_obj, result)

    # Check status_semantics
    if "status_semantics" not in schema:
        result.add_error("status_semantics", "Missing required field")
    else:
        validate_status_semantics(schema["status_semantics"], result)

    # Check task_id_format
    if "task_id_format" not in schema:
        result.add_error("task_id_format", "Missing required field")
    else:
        validate_task_id_format_obj(schema["task_id_format"], result)

    # Level 2: Semantic Validation
    if result.valid:
        validate_semantic_consistency(schema, result)

    # Validate optional fields if present
    if "validation" in schema:
        validate_validation_obj(schema["validation"], result)

    return result
```

---

## Error Message Standards

### Error Format

All validation errors should follow this format:

```
{severity}: {field_path}: {description}

Example:
ERROR: patterns.task_line.regex: Invalid regex: unbalanced parenthesis at position 15
WARNING: status_semantics.field_mapping: Raw field 'Dev' appears in multiple mappings
```

### Severity Levels

| Level | When to Use | Blocks Parsing |
|-------|-------------|----------------|
| ERROR | Invalid structure, missing required fields, invalid data types | Yes |
| WARNING | Suboptimal but functional, potential issues | No |
| INFO | Suggestions for improvement | No |

### Example Error Messages

**Structural Errors**:
```
ERROR: schema_version: Missing required field
ERROR: schema_version: Invalid format '2' (expected '2.0')
ERROR: schema_version: Unsupported version '3.0'
ERROR: patterns.task_line: Missing required pattern
```

**Pattern Errors**:
```
ERROR: patterns.task_line.regex: Invalid regex - unbalanced parenthesis
ERROR: patterns.task_line.groups: Must be non-empty array
ERROR: patterns.task_line.example: Does not match its regex pattern
WARNING: patterns.task_line: Named group 'priority' in regex but not in groups array
```

**Semantic Errors**:
```
ERROR: status_semantics.field_mapping: Missing entry for field 'dev'
ERROR: status_semantics.states.dev: Missing required state 'complete'
WARNING: status_semantics.states.dev: Only 1 variation for 'complete' (consider adding synonyms)
```

---

## Validation Command

### CLI Integration

```bash
# Validate current schema
synapse sense --validate

# Validate specific schema file
synapse sense --validate-file .synapse/config.json

# Validate and show warnings
synapse sense --validate --verbose
```

### Expected Output

```
🔍 Validating schema...

✅ Schema structure: Valid
✅ Pattern validation: All patterns valid
✅ Semantic validation: Consistent mappings
⚠️  Warning: patterns.subtask_line.example does not match latest regex

📊 Validation Summary:
  - Schema version: 2.0
  - Format type: markdown-checklist
  - Patterns defined: 3
  - Fields mapped: 3
  - Match rate: 98% (49/50 tasks)

✅ Schema validation PASSED
```

---

## Next Steps

- [x] T001: Design schema v2 structure
- [x] T002: Define schema validation rules
- [ ] T003: Create schema migration strategy
