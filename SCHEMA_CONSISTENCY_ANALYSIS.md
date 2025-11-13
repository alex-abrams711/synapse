# Synapse Configuration Schema - Consistency Analysis

**Date**: 2025-11-10
**Analyzed Files**:
1. `resources/workflows/feature-planning/commands/synapse/sense.md` (Planning Sense)
2. `resources/workflows/feature-implementation-v2/commands/synapse/sense.md` (Implementation Sense)
3. `resources/schemas/synapse-config-schema.json` (Canonical Schema)
4. `resources/settings/config-template.json` (Base Template)

---

## Executive Summary

### Critical Issues Found: 🔴 **3 MAJOR INCONSISTENCIES**

1. **Pattern naming conventions differ between sense commands and schema**
2. **Regex group names inconsistent (task_code vs task_id, field_code vs field)**
3. **Field mapping location inconsistent in documentation vs schema**

### Status by File

| File | Consistency | Issues |
|------|-------------|--------|
| Canonical Schema | ✅ Reference | 0 |
| Config Template | ✅ Consistent | 0 |
| Planning Sense | 🔴 Major Issues | 3 |
| Implementation Sense | 🟡 Minor Issues | 2 |

---

## Detailed Analysis

## 1. Base Configuration Structure

### ✅ CONSISTENT - Core Fields

All files agree on the base structure:

```json
{
  "synapse_version": "0.1.0",
  "initialized_at": "ISO 8601 timestamp",
  "agent": { "type": ..., "description": ... },
  "project": { "name": ..., "description": ..., "root_directory": ... },
  "workflows": { "active_workflow": ..., "applied_workflows": [] },
  "settings": { "auto_backup": true, "strict_validation": true, "uv_required": true }
}
```

**Verdict**: ✅ Perfect alignment

---

## 2. Third-Party Workflow Structure

### ✅ CONSISTENT - Top-Level Field Name

All documents use: **`third_party_workflow`** (singular, object)

**Breaking change correctly applied**: Old array-based `third_party_workflows` removed everywhere

| File | Field Name | Type | Status |
|------|-----------|------|--------|
| Canonical Schema | `third_party_workflow` | object | ✅ |
| Planning Sense | `third_party_workflow` | object | ✅ |
| Implementation Sense | `third_party_workflow` | object | ✅ |

**Verdict**: ✅ Perfect alignment on breaking change

---

## 3. Task Format Schema Structure

### 🔴 CRITICAL INCONSISTENCY - Pattern Naming

**Canonical Schema** (lines 450-467):
```json
{
  "patterns": {
    "task": "...",           // ← Uses "task"
    "subtask": "...",
    "status_field": "..."    // ← Uses "status_field"
  }
}
```

**Planning Sense Command** (lines 116-118):
```json
{
  "patterns": {
    "task": "...",           // ← Uses "task" ✅
    "subtask": "...",
    "status_field": "..."    // ← Uses "status_field" ✅
  }
}
```

**Implementation Sense Command** (lines 555-566):
```json
{
  "patterns": {
    "task_line": { ... },    // ← Uses "task_line" ❌
    "status_line": { ... }   // ← Uses "status_line" ❌
  }
}
```

**Issue**: Implementation sense uses `task_line`/`status_line` while canonical schema uses `task`/`status_field`.

**Impact**:
- Our updated `stop_qa_check.py` now supports BOTH via fallback logic: ✅
- But we're creating inconsistency in what sense commands generate

**Root Cause**: Implementation sense is following migration guide naming (v2.0) while canonical schema still uses legacy names.

---

## 4. Pattern Object Structure

### 🟡 INCONSISTENCY - Pattern Format

**Canonical Schema** (lines 455-467):
Patterns are **strings**:
```json
{
  "task": "regex string",
  "status_field": "regex string"
}
```

**Planning Sense Command** (lines 116-118):
Patterns are **strings**:
```json
{
  "task": "regex string",
  "status_field": "regex string"
}
```

**Implementation Sense Command** (lines 555-566):
Patterns are **objects**:
```json
{
  "task_line": {
    "regex": "...",
    "groups": [...],
    "example": "...",
    "required": true
  }
}
```

**Canonical Schema Documentation** (migration guide):
- States v2.0 will use object format
- But current canonical schema still defines string format

**Issue**: Implementation sense is generating v2.0 object patterns, but canonical schema still validates string patterns.

**Impact**:
- Code generates objects but schema expects strings
- Our updated `stop_qa_check.py` handles both ✅
- But schema validation would fail on objects

---

## 5. Regex Named Capture Groups

### 🔴 CRITICAL INCONSISTENCY - Group Names

**Canonical Schema** (line 457):
```
"must have task_code capture group"  // ← task_code
```

**Planning Sense Command** (line 116):
```regex
(?P<task_code>T\\d{3,})  // ← Uses task_code ✅
(?P<field_code>[A-Z]{2,})  // ← Uses field_code ✅
(?P<status_value>[^\\]]+)  // ← Uses status_value ✅
```

**Implementation Sense Command** (lines 556-563):
```json
"groups": ["checkbox", "task_id", "description"]  // ← Uses task_id ❌
"groups": ["checkbox", "field", "status"]          // ← Uses field/status ❌
```

**Migration Guide** (schema-v2-migration-guide.md):
- v2.0 uses: `task_id`, `field`, `status`
- v0 uses: `task_code`, `field_code`, `status_value`

**Issue**: Implementation sense generates v2.0 naming, planning sense generates legacy naming, canonical schema documents legacy naming.

**Impact**:
- Different sense commands generate incompatible schemas
- Our updated `stop_qa_check.py` handles both via fallback ✅
- But creates confusion about which is "correct"

---

## 6. Field Mapping Structure

### ✅ CONSISTENT - Top-Level Location

**Canonical Schema** (lines 469-486):
```json
{
  "task_format_schema": {
    "field_mapping": { ... },  // ← TOP LEVEL ✅
    "status_semantics": {
      "states": { ... }
    }
  }
}
```

**Planning Sense Command** (lines 120-124):
```json
{
  "field_mapping": {          // ← TOP LEVEL ✅
    "dev_status": "DS",
    "qa": "QA",
    "user_verification": "UV"
  }
}
```

**Implementation Sense Command** (lines 569-571):
```json
{
  "status_semantics": {
    "fields": [...],
    "field_mapping": { ... },  // ← NESTED ❌
    "states": { ... }
  }
}
```

**Issue**: Implementation sense nests field_mapping under status_semantics, which contradicts canonical schema.

**Impact**: This is the EXACT issue we found in live_testing and rejected! ❌

---

## 7. Field Mapping Value Types

### ✅ CONSISTENT - String Values

**Canonical Schema** (lines 478-479):
```json
"qa": {
  "type": "string"  // ← String ✅
}
```

**Planning Sense Command** (line 122):
```json
"qa": "QA"  // ← String ✅
```

**Implementation Sense Command** (line 570):
```json
"field_mapping": field_mapping  // ← Generated from code, could be string or array
```

The implementation sense generates field_mapping dynamically, which could produce arrays (the issue we rejected from live_testing).

**Issue**: Implementation sense can generate arrays when canonical schema requires strings.

---

## 8. QA Status Semantics (Option 6)

### ✅ CONSISTENT - Three-Category Pattern

All files correctly implement Option 6 three-category pattern:

```json
{
  "qa": {
    "not_verified": ["Not Started"],
    "verified_success": ["Complete", "Passed"],
    "verified_failure_pattern": "^Failed - .*"
  }
}
```

| File | Implementation | Status |
|------|----------------|--------|
| Canonical Schema | Lines 522-536 | ✅ Correct |
| Planning Sense | Lines 132-136 | ✅ Correct |
| Implementation Sense | Lines 493-516 | ✅ Correct |

**Verdict**: ✅ Perfect alignment

---

## 9. Required Fields

### 🟡 MINOR INCONSISTENCY - Schema Requirements

**Canonical Schema** (line 443):
```json
"required": ["version", "patterns", "field_mapping", "status_semantics"]
```

**Planning Sense Command**:
Generates: `version`, `patterns`, `field_mapping`, `status_semantics` ✅

**Implementation Sense Command**:
Generates: `schema_version`, `format_type`, `patterns`, `status_semantics`, `task_id_format`, `metadata`

**Issues**:
1. Implementation uses `schema_version`, canonical expects `version`
2. Implementation nests `field_mapping` under `status_semantics` (missing at top level)
3. Implementation adds extra fields not in canonical schema

---

## 10. Schema Version Field

### 🔴 INCONSISTENCY - Field Name

**Canonical Schema** (lines 445-448):
```json
"version": {
  "type": "string",
  "pattern": "^2\\.\\d+$"
}
```

**Planning Sense Command** (line 114):
```json
"version": "2.0"  // ← Matches canonical ✅
```

**Implementation Sense Command** (line 552):
```python
schema = {
    "schema_version": "2.0",  // ← Different name ❌
```

**Issue**: Field named `version` vs `schema_version`

---

## Summary of Inconsistencies

### 🔴 Critical Issues

| Issue | Planning Sense | Implementation Sense | Canonical Schema | Impact |
|-------|----------------|---------------------|------------------|--------|
| **Pattern names** | `task`, `status_field` ✅ | `task_line`, `status_line` ❌ | `task`, `status_field` ✅ | Hook fallback handles it |
| **Pattern format** | Strings ✅ | Objects ❌ | Strings ✅ | Hook handles both |
| **Regex groups** | `task_code`, `field_code` ✅ | `task_id`, `field`, `status` ❌ | `task_code` ✅ | Hook handles both |
| **field_mapping location** | Top-level ✅ | Nested ❌ | Top-level ✅ | Would break parsing |
| **Version field** | `version` ✅ | `schema_version` ❌ | `version` ✅ | Schema validation fails |

### Root Cause Analysis

**Implementation Sense Command** is implementing the **future v2.0 schema format** described in migration docs, while:
- **Canonical Schema** still defines the **current/legacy format**
- **Planning Sense Command** follows the **canonical schema**

This creates a **temporal inconsistency**: Implementation sense is "ahead" of the canonical schema.

---

## Recommendations

### Option 1: Update Implementation Sense to Match Current Schema ⭐ **RECOMMENDED**

**Action**: Modify `resources/workflows/feature-implementation-v2/commands/synapse/sense.md` to generate schemas matching the canonical format:

1. Use `task`, `status_field` pattern names (not `task_line`, `status_line`)
2. Generate string patterns (not objects)
3. Use `task_code`, `field_code`, `status_value` groups (not `task_id`, `field`, `status`)
4. Keep `field_mapping` at top level (not nested)
5. Use `version` field (not `schema_version`)

**Pros**:
- Immediate consistency
- Works with current canonical schema
- No breaking changes

**Cons**:
- Stays on legacy format longer

---

### Option 2: Update Canonical Schema to v2.0 Format

**Action**: Update `resources/schemas/synapse-config-schema.json` to accept v2.0 format:

1. Allow both `task`/`task_line` pattern names
2. Allow both string and object pattern formats
3. Allow both `task_code`/`task_id` group naming
4. Update documentation

**Pros**:
- Future-proof
- Aligns with migration guide

**Cons**:
- More complex schema validation
- Requires testing all consumers

---

### Option 3: Make Both Sense Commands Identical

**Action**: Copy Planning Sense logic to Implementation Sense, ensuring they generate identical schemas.

**Pros**:
- Guaranteed consistency
- Single source of truth

**Cons**:
- Implementation sense loses v2.0 features
- DRY violation (duplicate logic)

---

## Immediate Action Items

### Priority 1: Fix Implementation Sense Command 🔥

The implementation sense command has **3 breaking inconsistencies** that will cause:
- Schema validation failures (wrong field names)
- Hook parsing failures (wrong structure)
- User confusion (different outputs from different commands)

**Required changes to `resources/workflows/feature-implementation-v2/commands/synapse/sense.md`**:

1. **Line 552**: Change `"schema_version"` → `"version"`
2. **Line 555**: Change `"task_line"` → `"task"`
3. **Line 562**: Change `"status_line"` → `"status_field"`
4. **Lines 556-566**: Change object patterns to string patterns
5. **Lines 569-571**: Move `field_mapping` from nested to top-level
6. **Regex groups**: Use `task_code`, `field_code`, `status_value` instead of `task_id`, `field`, `status`

### Priority 2: Add Validation to Sense Commands

Both sense commands should validate their generated config against the canonical schema before saving.

### Priority 3: Document the Inconsistencies

Add a note in CLAUDE.md or sense command docs warning that the schema is in transition.

---

## Testing Checklist

After fixing inconsistencies:

- [ ] Run planning sense command, verify generated schema
- [ ] Run implementation sense command, verify generated schema
- [ ] Compare both generated schemas - should be identical
- [ ] Validate both against canonical schema
- [ ] Test stop_qa_check.py with both schema formats
- [ ] Run full test suite: `pytest tests/test_stop_qa_check.py`

---

## Conclusion

The **Implementation Sense Command** is out of sync with the **Canonical Schema** because it's implementing a future v2.0 format that hasn't been formally adopted yet. This creates **3 critical inconsistencies** that will break schema validation and potentially hook functionality.

**Recommended Fix**: Update Implementation Sense to match the canonical schema (Option 1), ensuring both sense commands generate identical, valid configurations.

The good news: Our updated `stop_qa_check.py` already handles both formats via fallback logic, so existing systems won't break. But we need to fix the sense commands to prevent future inconsistencies.
