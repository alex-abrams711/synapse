# Schema Format Comparison: Current vs v2.0

**Date**: 2025-11-10

---

## Overview

There are **THREE schema formats** being referenced in Synapse:

1. **v0 (Experimental)** - Old experimental format from early development
2. **Current/Legacy** - What the canonical schema currently expects (production)
3. **v2.0 (Future)** - Planned migration target described in migration guide

**Confusion Point**: The canonical schema documentation says "v2.0" but it's actually describing the **Current/Legacy** format. The migration guide describes a **future v2.0** that hasn't been implemented yet.

---

## Complete Side-by-Side Comparison

### 1. Version Field

| Format | Field Name | Value | Required? |
|--------|-----------|-------|-----------|
| v0 (Experimental) | None | N/A | No ❌ |
| **Current/Legacy** | **`"version"`** | `"2.0"` | **Yes ✅** |
| v2.0 (Future) | `"schema_version"` | `"2.0"` | Yes ✅ |

**Key Difference**: Field is named `version` (current) vs `schema_version` (future)

**Canonical Schema** (line 445-448):
```json
{
  "version": {
    "type": "string",
    "pattern": "^2\\.\\d+$",
    "description": "Schema version (2.x)"
  }
}
```

**What Implementation Sense Generates**:
```json
{
  "schema_version": "2.0"  // ❌ Wrong field name
}
```

---

### 2. Pattern Structure

#### **v0 (Experimental)**
```json
{
  "patterns": {
    "task_line": "^\\s*-\\s*\\[[ xX]\\].*",
    "status_line": "^\\s*-\\s*\\[[ xX]\\].*"
  }
}
```
- Patterns are **strings**
- Uses `task_line`, `status_line` names

#### **Current/Legacy (Canonical)**
```json
{
  "patterns": {
    "task": "^\\[\\s*\\]\\s*-\\s*(?P<task_code>T\\d{3,})\\s+-\\s+(?P<description>(?!.*:).*)",
    "subtask": "^\\s+\\[\\s*\\]\\s*-\\s*(?P<subtask_code>T\\d{3,}-ST\\d{3,})\\s*-\\s*(?P<description>.*)",
    "status_field": "^\\s+\\[\\s*\\]\\s*-\\s*T\\d{3,}-(?P<field_code>[A-Z]{2,})\\s*-\\s*.*:\\s*\\[(?P<status_value>[^\\]]+)\\]"
  }
}
```
- Patterns are **strings** ✅
- Uses `task`, `subtask`, `status_field` names ✅
- Uses capture groups: `task_code`, `field_code`, `status_value` ✅

#### **v2.0 (Future/Migration Guide)**
```json
{
  "patterns": {
    "task_line": {
      "regex": "^\\[([ xX])\\] - \\*\\*(?P<task_id>T\\d+):\\s*(?P<description>.*?)\\*\\*",
      "groups": ["checkbox", "task_id", "description"],
      "example": "- [X] - **T001: Create schema**",
      "required": true
    },
    "status_line": {
      "regex": "...",
      "groups": ["checkbox", "field", "status"],
      "example": "- [X] - Dev Status: [Complete]",
      "required": true
    }
  }
}
```
- Patterns are **objects** with nested structure ❌
- Uses `task_line`, `status_line` names ❌
- Uses capture groups: `task_id`, `field`, `status` ❌
- Includes metadata: `groups`, `example`, `required` ❌

**Key Differences**:

| Aspect | Current/Legacy | v2.0 Future |
|--------|----------------|-------------|
| **Pattern type** | String | Object with `{regex, groups, example}` |
| **Pattern names** | `task`, `status_field` | `task_line`, `status_line` |
| **Regex groups** | `task_code`, `field_code`, `status_value` | `task_id`, `field`, `status` |
| **Metadata** | None | Includes `groups`, `example`, `required` |

---

### 3. Field Mapping Location

#### **v0 (Experimental)**
```json
{
  "field_mapping": {
    "dev": "DS",
    "qa": "QA"
  },
  "status_values": {
    "dev": ["Not Started", "In Progress", "Complete"]
  }
}
```
- Field mapping at **top level**
- Uses positional `status_values` arrays

#### **Current/Legacy (Canonical)**
```json
{
  "field_mapping": {
    "dev_status": "DS",
    "qa": "QA",
    "user_verification": "UV"
  },
  "status_semantics": {
    "states": {
      "qa": {
        "not_verified": ["Not Started"],
        "verified_success": ["Complete", "Passed"],
        "verified_failure_pattern": "^Failed - .*"
      }
    }
  }
}
```
- Field mapping at **top level** ✅
- Uses semantic `status_semantics.states` objects ✅
- Field mapping values are **strings** ✅

#### **v2.0 (Future/Migration Guide)**
```json
{
  "status_semantics": {
    "fields": ["dev", "qa", "user_verification"],
    "field_mapping": {
      "dev": ["Dev Status", "Development Status"],
      "qa": ["QA Status", "QA"],
      "user_verification": ["User Verification Status"]
    },
    "states": {
      "qa": {
        "not_verified": ["Not Started"],
        "verified_success": ["Complete", "Passed"],
        "verified_failure_pattern": "^Failed - .*"
      }
    }
  }
}
```
- Field mapping **nested** under `status_semantics` ❌
- Field mapping values are **arrays** (multiple field name variants) ❌
- Includes top-level `fields` array ❌

**Key Differences**:

| Aspect | Current/Legacy | v2.0 Future |
|--------|----------------|-------------|
| **field_mapping location** | Top-level | Nested under `status_semantics` |
| **field_mapping values** | String | Array of strings |
| **fields array** | None | Present at `status_semantics.fields` |

**Canonical Schema** (lines 469-486):
```json
{
  "field_mapping": {  // ← TOP LEVEL
    "type": "object",
    "description": "Maps field types to their codes in the task file",
    "properties": {
      "dev_status": { "type": "string" },
      "qa": { "type": "string" },
      "user_verification": { "type": "string" }
    }
  },
  "status_semantics": {
    "type": "object",
    "description": "Semantic meaning of status values",
    "required": ["states"],
    "properties": {
      "states": { ... }
    }
  }
}
```

---

### 4. Additional Fields

#### **v0 (Experimental)**
```json
{
  "structure": {
    "task_id_prefix": "T",
    "task_id_digits": 3
  }
}
```
- Has `structure` object for task ID format

#### **Current/Legacy (Canonical)**
```json
{
  // No extra fields beyond what's shown above
}
```
- Minimal, focused structure

#### **v2.0 (Future/Migration Guide)**
```json
{
  "schema_version": "2.0",
  "format_type": "markdown-checklist",
  "task_id_format": {
    "prefix": "T",
    "digits": 3,
    "pattern": "T\\d{3}",
    "example": "T001",
    "separator": ""
  },
  "metadata": {
    "analyzed_at": "2025-01-15T10:00:00Z",
    "sample_size": 200,
    "total_tasks_found": 96,
    "confidence": 1.0,
    "format_detected_by": "sense_command",
    "source_file": "tasks.md"
  },
  "validation": {
    "valid_sample_size": 96,
    "pattern_match_rate": 1.0,
    "last_validated": "2025-01-15T10:00:00Z",
    "validation_passed": true
  }
}
```
- Adds `format_type` field
- Has structured `task_id_format` object (replaces `structure`)
- Extensive `metadata` object
- Optional `validation` results

**Key Differences**:

| Field | Current/Legacy | v2.0 Future |
|-------|----------------|-------------|
| `format_type` | ❌ Not present | ✅ Present (e.g., "markdown-checklist") |
| `task_id_format` | ❌ Not present | ✅ Present (structured object) |
| `metadata` | ❌ Minimal/none | ✅ Extensive (timestamps, confidence, etc.) |
| `validation` | ❌ Not present | ✅ Optional (validation results) |

---

## Complete Examples

### Current/Legacy Format (What Canonical Schema Expects)

```json
{
  "task_format_schema": {
    "version": "2.0",
    "patterns": {
      "task": "^\\[\\s*\\]\\s*-\\s*(?P<task_code>T\\d{3,})\\s+-\\s+(?P<description>(?!.*:).*)",
      "subtask": "^\\s+\\[\\s*\\]\\s*-\\s*(?P<subtask_code>T\\d{3,}-ST\\d{3,})\\s*-\\s*(?P<description>.*)",
      "status_field": "^\\s+\\[\\s*\\]\\s*-\\s*T\\d{3,}-(?P<field_code>[A-Z]{2,})\\s*-\\s*.*:\\s*\\[(?P<status_value>[^\\]]+)\\]"
    },
    "field_mapping": {
      "dev_status": "DS",
      "qa": "QA",
      "user_verification": "UV"
    },
    "status_semantics": {
      "states": {
        "dev": {
          "not_started": ["Not Started"],
          "in_progress": ["In Progress"],
          "complete": ["Complete"]
        },
        "qa": {
          "not_verified": ["Not Started"],
          "verified_success": ["Complete", "Passed"],
          "verified_failure_pattern": "^Failed - .*"
        },
        "user_verification": {
          "not_started": ["Not Started"],
          "verified": ["Verified"]
        }
      }
    }
  }
}
```

**Characteristics**:
- ✅ Version field: `"version": "2.0"`
- ✅ Patterns are strings
- ✅ Pattern names: `task`, `subtask`, `status_field`
- ✅ Regex groups: `task_code`, `field_code`, `status_value`
- ✅ Field mapping at top level
- ✅ Field mapping values are strings
- ✅ Minimal, focused structure

---

### v2.0 Future Format (What Migration Guide Describes)

```json
{
  "task_format_schema": {
    "schema_version": "2.0",
    "format_type": "markdown-checklist",
    "patterns": {
      "task_line": {
        "regex": "^\\[([ xX])\\] - \\*\\*(?P<task_id>T\\d+):\\s*(?P<description>.*?)\\*\\*",
        "groups": ["checkbox", "task_id", "description"],
        "example": "- [X] - **T001: Create database schema**",
        "required": true
      },
      "status_line": {
        "regex": "^\\s*-\\s*\\[([ xX])\\]\\s*-\\s*(?P<field>[^:]+):\\s*\\[(?P<status>[^\\]]+)\\]",
        "groups": ["checkbox", "field", "status"],
        "example": "- [X] - Dev Status: [Complete]",
        "required": true
      },
      "subtask_line": {
        "regex": "^\\s+\\[([ xX])\\] - (?P<description>.*)",
        "groups": ["checkbox", "description"],
        "example": "  - [X] - Add user table",
        "required": false
      }
    },
    "status_semantics": {
      "fields": ["dev", "qa", "user_verification"],
      "field_mapping": {
        "dev": ["Dev Status", "Development Status"],
        "qa": ["QA Status", "QA"],
        "user_verification": ["User Verification Status", "User Verification"]
      },
      "states": {
        "dev": {
          "not_started": ["Not Started"],
          "in_progress": ["In Progress"],
          "complete": ["Complete"]
        },
        "qa": {
          "not_verified": ["Not Started"],
          "verified_success": ["Complete", "Passed"],
          "verified_failure_pattern": "^Failed - .*"
        },
        "user_verification": {
          "not_started": ["Not Started"],
          "verified": ["Verified"]
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
    "metadata": {
      "analyzed_at": "2025-01-15T10:00:00Z",
      "sample_size": 200,
      "total_tasks_found": 96,
      "confidence": 1.0,
      "format_detected_by": "sense_command",
      "source_file": "specs/feature/tasks.md"
    },
    "validation": {
      "valid_sample_size": 96,
      "pattern_match_rate": 1.0,
      "last_validated": "2025-01-15T10:00:00Z",
      "validation_passed": true
    }
  }
}
```

**Characteristics**:
- ❌ Version field: `"schema_version": "2.0"` (different name)
- ❌ Patterns are objects with metadata
- ❌ Pattern names: `task_line`, `status_line`, `subtask_line`
- ❌ Regex groups: `task_id`, `field`, `status`
- ❌ Field mapping nested under `status_semantics`
- ❌ Field mapping values are arrays
- ❌ Extensive metadata and validation sections

---

## Migration Guide Claims vs Reality

The migration guide says it's documenting migration from "v0" → "v2.0", but:

**Reality Check**:
- The **canonical schema** is actually the **current production format**
- The migration guide's "v2.0" is a **future target** that hasn't been adopted yet
- The canonical schema says "v2.0" in its description but defines the **current/legacy format**

**This creates confusion because**:
1. Canonical schema documentation claims to be "v2.0"
2. Migration guide describes a different "v2.0" format
3. Implementation Sense command implements the migration guide's "v2.0"
4. Planning Sense command implements the canonical "v2.0" (really current/legacy)

**Result**: Two different "v2.0" formats exist in documentation!

---

## What Should We Call These Formats?

To avoid confusion, here's clearer naming:

| Old Name | Better Name | Status | Used By |
|----------|-------------|--------|---------|
| v0 | Experimental | Deprecated | Nothing (historical) |
| v2.0 (canonical) | **Current** | Production | Canonical schema, Planning Sense, stop_qa_check.py |
| v2.0 (migration) | **Future** | Planned | Migration guide, Implementation Sense |

---

## Impact on Code

### What stop_qa_check.py Expects

Our updated `stop_qa_check.py` now handles **both Current and Future formats** via fallback logic:

```python
# Pattern names
task_pattern_obj = patterns.get("task_line") or patterns.get("task")  # Future OR Current
status_field_pattern_obj = patterns.get("status_line") or patterns.get("status_field")  # Future OR Current

# Pattern format
task_pattern = task_pattern_obj.get("regex") if isinstance(task_pattern_obj, dict) else task_pattern_obj  # Object OR String

# Regex groups
task_code = task_match.group("task_id") if "task_id" in task_match.groupdict() else task_match.group("task_code")  # Future OR Current
field_code = field_match.group("field") if "field" in field_match.groupdict() else field_match.group("field_code")  # Future OR Current
```

**This is why our hook works with both formats!** ✅

But the **canonical schema validation** will **fail** on Future format configs.

---

## Recommendations

### Option 1: Stay on Current Format (RECOMMENDED)

**Action**: Fix Implementation Sense to generate Current format

**Pros**:
- Immediate consistency
- Passes canonical schema validation
- No breaking changes

**Cons**:
- Delays adoption of Future format features

---

### Option 2: Adopt Future Format

**Action**: Update canonical schema to define Future format

**Pros**:
- Gets benefits of Future format (metadata, validation, etc.)
- Aligns with migration guide

**Cons**:
- Requires updating all consumers
- More complex schema
- Breaking change for existing systems

---

### Option 3: Support Both (What We Did)

**Action**: Keep fallback logic in hooks to support both

**Pros**:
- Maximum flexibility
- No breaking changes
- Allows gradual migration

**Cons**:
- Complexity in parsers
- Two "correct" formats exist
- Confusion in documentation

---

## Bottom Line

**We have TWO different "v2.0" formats**:

1. **Current Format** (canonical schema) - Production standard, what planning sense uses
2. **Future Format** (migration guide) - Planned evolution, what implementation sense uses

The **stop_qa_check.py** now supports both, but the **sense commands generate incompatible schemas**.

**Fix**: Make Implementation Sense generate Current format to match Planning Sense and canonical schema.
