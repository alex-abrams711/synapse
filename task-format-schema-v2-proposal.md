# Task Format Schema System v2.0 - Enhancement Proposal

**Status**: Draft
**Created**: 2025-10-24
**Author**: Analysis of experiments/ directory findings
**Target**: Synapse CLI v0.3.0+

## Executive Summary

This proposal outlines improvements to the experimental task format schema system that enables Synapse workflows to dynamically detect and parse task management formats (OpenSpec, GitHub Spec Kit, custom) without hard-coded parsers.

The current experimental implementation (in `experiments/`) proves the concept works but has production readiness issues around error handling, schema validation, and status value mapping. This proposal addresses these issues with concrete architectural improvements.

---

## Task Checklist

### Phase 1: Schema Design
- [x] **T001: Design schema v2 structure** - Create comprehensive schema format with versioning, validation metadata, and semantic status mapping
- [x] **T002: Define schema validation rules** - Specify required fields, data types, and validation thresholds
- [x] **T003: Create schema migration strategy** - Design approach for migrating v0 (experimental) schemas to v2

### Phase 2: Parser Implementation
- [x] **T004: Implement TaskSchemaParser class** - Build robust parser with named group extraction and error handling
- [x] **T005: Implement status normalization** - Create semantic mapping from raw status strings to canonical states
- [x] **T006: Add schema validation logic** - Validate schema structure, version compatibility, and required fields
- [x] **T007: Write parser unit tests** - Test parsing with valid schemas, malformed schemas, edge cases

### Phase 3: Sense Command Enhancement
- [x] **T008: Add Phase 6 extraction algorithm** - Implement concrete logic for extracting patterns from tasks.md files
- [x] **T009: Implement status value detection** - Extract and normalize all status field names and values
- [x] **T010: Add schema validation tests** - Validate generated schema by re-parsing tasks with 95%+ match rate
- [x] **T011: Enhance error reporting** - Provide actionable feedback when schema generation fails

### Phase 4: Hook Integration
- [x] **T012: Update pre-tool-use.py to use v2 schema** - Integrate TaskSchemaParser into pre-tool-use hook
- [x] **T013: Update post-tool-use.py to use v2 schema** - Integrate TaskSchemaParser into post-tool-use hook
- [x] **T014: Update verification-complete.py to use v2 schema** - Integrate TaskSchemaParser into verification hook
- [x] **T015: Simplify business logic with semantic states** - Refactor blocking conditions to use semantic states

### Phase 5: Testing & Validation
- [ ] **T016: Test with OpenSpec format** - Validate schema generation and parsing with OpenSpec tasks.md
- [ ] **T017: Test with GitHub Spec Kit format** - Validate schema generation and parsing with Spec Kit format
- [ ] **T018: Test with custom format (benchmarks)** - Validate with experimental benchmarks project format
- [ ] **T019: Test with edge cases** - Empty files, malformed tasks, special characters, very long descriptions
- [ ] **T020: Create integration test suite** - End-to-end tests for sense → hook workflow

### Phase 6: Documentation & Migration
- [ ] **T021: Document schema v2 format** - Write comprehensive schema documentation
- [ ] **T022: Create migration guide** - Document how to migrate experimental configs to v2
- [ ] **T023: Update sense.md documentation** - Reflect new Phase 6 implementation details
- [ ] **T024: Update hook documentation** - Document schema consumption and error handling

### Phase 7: Deployment
- [ ] **T025: Move experimental files to main workflows** - Integrate tested improvements into feature-implementation workflow
- [ ] **T026: Add schema version check to CLI** - Warn users of outdated schemas
- [ ] **T027: Create sense --validate command** - Allow users to validate existing schemas
- [ ] **T028: Update CHANGELOG.md** - Document breaking changes and migration path

---

## Current State Analysis

### What Works (Strengths)

1. **Excellent Abstraction** - Separates format detection from business logic
2. **Future-Proof Design** - Supports multiple task management systems automatically
3. **Real-World Validation** - Proven with benchmarks project (96 tasks, monorepo)
4. **Graceful Degradation** - Falls back to defaults when schema unavailable

### Issues Identified

#### 1. **Regex Group Mismatch** (Critical)
**Location**: `experiments/pre-tool-use.py:62-94`

**Problem**: Schema patterns use named groups `(?P<task_id>...)` but parser uses numeric positions:
```python
patterns = {
    "task_line": r'^(\[ \]|\[X\]|\[x\]) - \*\*(T\d+):\s*(.*?)\*\*',
    "task_id_group": 2,  # ← Numeric position
    "description_group": 3
}
```

**Risk**: Mismatch between named/numbered groups causes parsing failures
**Impact**: Hook fails to extract task IDs, blocks all work

---

#### 2. **Fragile Status Value Mapping** (High)
**Location**: `experiments/pre-tool-use.py:128-165`

**Problem**: Array position mapping to semantic meaning:
```python
# Position 0 = not_started, Position 1 = in_progress, Position 2 = complete
if len(dev_vals) >= 3:
    result['dev'] = {
        'not_started': dev_vals[0],
        'in_progress': dev_vals[1],
        'complete': dev_vals[2]
    }
```

**Risk**: If sense.md extracts values in different order (e.g., alphabetical), business logic breaks
**Impact**: Tasks marked "Complete" might be treated as "Not Started"

---

#### 3. **Manual Schema Generation** (Medium)
**Location**: `experiments/sense.md:183-261`

**Problem**: Phase 6 describes _what_ to extract but not _how_:
```markdown
- Read the first 200-500 lines of the tasks file to establish patterns
- Use regex matching to identify recurring patterns
- Extract unique status values by parsing all status lines
```

**Risk**: Different AI agents generate inconsistent schemas
**Impact**: Unreliable schema quality, manual fixes required

---

#### 4. **No Schema Validation** (Medium)
**Location**: All hook files

**Problem**: Hooks trust schema structure without validation:
```python
patterns = schema.get("patterns", {})
# No check if patterns are valid regex, have required keys, etc.
```

**Risk**: Malformed schema causes runtime errors deep in hook execution
**Impact**: Cryptic errors, difficult debugging

---

#### 5. **Untested Multi-Format Support** (Low)
**Location**: `experiments/config.json:96`

**Problem**: Only markdown-checklist format tested, despite claiming support for:
```json
"format_type": "markdown-checklist|numbered-list|custom"
```

**Risk**: Patterns may not generalize to other formats
**Impact**: False advertising, users expect broader support

---

#### 6. **Status Field Name Inconsistency** (Low)
**Location**: `experiments/pre-tool-use.py:238-243`

**Problem**: Parser handles both "Dev" and "Dev Status" formats ad-hoc:
```python
if status_type in ["Dev", "Dev Status"]:
    current_task.dev_status = status_value
```

**Question**: Why this inconsistency? Should schema normalize this?

---

## Proposed Improvements

### 1. Redesigned Schema Structure (v2.0)

**File**: `.synapse/config.json → third_party_workflows.detected[].task_format_schema`

```json
{
  "task_format_schema": {
    "schema_version": "2.0",
    "format_type": "markdown-checklist",

    "patterns": {
      "task_line": {
        "regex": "^\\s*-\\s*\\[([ xX])\\]\\s*-\\s*\\*\\*(?P<task_id>T\\d{3}):\\s*(?P<description>.+?)\\*\\*\\s*$",
        "groups": ["checkbox", "task_id", "description"],
        "example": "- [X] - **T001: Create database schema**"
      },
      "subtask_line": {
        "regex": "^\\s*-\\s*\\[([ xX])\\]\\s*-\\s*(?!\\*\\*)(?P<description>.+?)\\s*$",
        "groups": ["checkbox", "description"],
        "example": "- [X] - Add user table"
      },
      "status_line": {
        "regex": "^\\s*-\\s*\\[([ xX])\\]\\s*-\\s*(?P<field>[^:]+):\\s*\\[(?P<status>[^\\]]+)\\]\\s*$",
        "groups": ["checkbox", "field", "status"],
        "example": "- [X] - Dev Status: [Complete]"
      }
    },

    "status_semantics": {
      "fields": ["dev", "qa", "user_verification"],
      "field_mapping": {
        "dev": ["Dev Status", "Dev", "Development Status"],
        "qa": ["QA Status", "QA", "Quality Assurance Status"],
        "user_verification": ["User Verification Status", "User Verification", "UV Status"]
      },
      "states": {
        "dev": {
          "not_started": ["Not Started", "Pending", "Todo"],
          "in_progress": ["In Progress", "Working", "Active"],
          "complete": ["Complete", "Done", "Finished"]
        },
        "qa": {
          "not_started": ["Not Started", "Pending"],
          "in_progress": ["In Progress", "Testing"],
          "complete": ["Complete", "Passed", "Done"]
        },
        "user_verification": {
          "not_started": ["Not Started", "Pending"],
          "complete": ["Complete", "Verified", "Done"]
        }
      }
    },

    "task_id_format": {
      "prefix": "T",
      "digits": 3,
      "pattern": "T\\d{3}",
      "example": "T001"
    },

    "validation": {
      "valid_sample_size": 50,
      "pattern_match_rate": 0.95,
      "last_validated": "2025-10-21T10:30:00Z"
    },

    "metadata": {
      "analyzed_at": "2025-10-21T10:30:00Z",
      "sample_size": 200,
      "total_tasks_found": 96,
      "confidence": 1.0
    }
  }
}
```

**Key Improvements**:
- `schema_version` for evolution support
- Named groups documented in `groups` array
- `status_semantics` with bidirectional mapping (field names + status values)
- Multiple status variations per semantic state ("Complete", "Done", "Finished" all map to `complete`)
- `validation` section proving schema works
- Rich metadata for debugging

---

### 2. TaskSchemaParser Class

**File**: New file `src/synapse_cli/parsers/task_schema_parser.py`

```python
#!/usr/bin/env python3
"""Schema-driven task parser with validation and fallback"""
import re
from typing import Dict, Optional, List
from dataclasses import dataclass

@dataclass
class ParsedTask:
    """Parsed task with semantic states"""
    task_id: str
    description: str
    dev_state: str  # "not_started" | "in_progress" | "complete"
    qa_state: str
    uv_state: str
    keywords: List[str]
    line_number: int

class SchemaValidationError(Exception):
    """Raised when schema is invalid"""
    pass

class TaskSchemaParser:
    """Schema-driven task parser with validation and fallback"""

    SUPPORTED_VERSIONS = ["1.0", "2.0"]

    def __init__(self, schema: Optional[Dict] = None):
        self.schema = schema or self._get_default_schema()
        self.validate_schema()

    def validate_schema(self):
        """Validate schema structure and compatibility"""
        version = self.schema.get("schema_version", "0.0")

        if version not in self.SUPPORTED_VERSIONS:
            raise SchemaValidationError(
                f"Unsupported schema version: {version}. "
                f"Supported: {', '.join(self.SUPPORTED_VERSIONS)}"
            )

        required_keys = ["patterns", "status_semantics"]
        for key in required_keys:
            if key not in self.schema:
                raise SchemaValidationError(f"Schema missing required key: {key}")

        # Validate pattern structure
        required_patterns = ["task_line", "status_line"]
        patterns = self.schema["patterns"]
        for pattern_name in required_patterns:
            if pattern_name not in patterns:
                raise SchemaValidationError(f"Missing pattern: {pattern_name}")

            pattern = patterns[pattern_name]
            if not isinstance(pattern, dict) or "regex" not in pattern:
                raise SchemaValidationError(f"Invalid pattern structure: {pattern_name}")

            # Validate regex compiles
            try:
                re.compile(pattern["regex"])
            except re.error as e:
                raise SchemaValidationError(f"Invalid regex in {pattern_name}: {e}")

    def parse_task_line(self, line: str) -> Optional[Dict]:
        """Parse a task line using schema pattern"""
        pattern_obj = self.schema["patterns"]["task_line"]
        regex = pattern_obj["regex"]

        match = re.match(regex, line)
        if not match:
            return None

        # Use named groups from regex
        try:
            return {
                "task_id": match.group("task_id"),
                "description": match.group("description"),
                "checkbox": match.group("checkbox") if "checkbox" in match.groupdict() else None
            }
        except IndexError as e:
            print(f"⚠️ Pattern matched but groups missing: {e}", file=sys.stderr)
            return None

    def parse_status_line(self, line: str) -> Optional[Dict]:
        """Parse a status line and normalize to semantic value"""
        pattern_obj = self.schema["patterns"]["status_line"]
        regex = pattern_obj["regex"]

        match = re.match(regex, line)
        if not match:
            return None

        try:
            field_raw = match.group("field").strip()
            status_raw = match.group("status").strip()
        except IndexError:
            return None

        # Normalize field to semantic category
        semantic_field = self._normalize_field(field_raw)
        if not semantic_field:
            print(f"⚠️ Unknown status field: '{field_raw}' - ignoring", file=sys.stderr)
            return None

        # Normalize status value to semantic state
        semantic_state = self._normalize_status(semantic_field, status_raw)

        return {
            "field": semantic_field,  # "dev", "qa", "user_verification"
            "state": semantic_state,   # "not_started", "in_progress", "complete"
            "raw_field": field_raw,
            "raw_status": status_raw
        }

    def _normalize_field(self, field_raw: str) -> Optional[str]:
        """Map raw field name to semantic category"""
        field_mapping = self.schema["status_semantics"]["field_mapping"]

        for semantic, variations in field_mapping.items():
            if field_raw in variations:
                return semantic

        return None

    def _normalize_status(self, field: str, status_raw: str) -> str:
        """Map raw status value to semantic state"""
        states = self.schema["status_semantics"]["states"][field]

        for semantic_state, variations in states.items():
            if status_raw in variations:
                return semantic_state

        # Unknown status - default to not_started for safety
        print(
            f"⚠️ Unknown status '{status_raw}' for field '{field}' - "
            f"defaulting to not_started",
            file=sys.stderr
        )
        return "not_started"

    def get_canonical_status(self, field: str, semantic_state: str) -> str:
        """Get the canonical status string for a field/state combo"""
        states = self.schema["status_semantics"]["states"][field]
        variations = states.get(semantic_state, [])
        return variations[0] if variations else semantic_state

    def parse_tasks_file(self, file_path: str) -> List[ParsedTask]:
        """Parse entire tasks file and return structured tasks"""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        tasks = []
        current_task = None

        for i, line in enumerate(lines, 1):
            line = line.rstrip()

            # Try parsing as task line
            task_data = self.parse_task_line(line)
            if task_data:
                # Save previous task
                if current_task:
                    tasks.append(current_task)

                # Start new task
                current_task = ParsedTask(
                    task_id=task_data["task_id"],
                    description=task_data["description"],
                    dev_state="not_started",
                    qa_state="not_started",
                    uv_state="not_started",
                    keywords=self._extract_keywords(task_data["description"]),
                    line_number=i
                )
                continue

            # Try parsing as status line
            if current_task:
                status_data = self.parse_status_line(line)
                if status_data:
                    field = status_data["field"]
                    state = status_data["state"]

                    if field == "dev":
                        current_task.dev_state = state
                    elif field == "qa":
                        current_task.qa_state = state
                    elif field == "user_verification":
                        current_task.uv_state = state

        # Don't forget last task
        if current_task:
            tasks.append(current_task)

        return tasks

    def _extract_keywords(self, description: str) -> List[str]:
        """Extract searchable keywords from description"""
        clean_desc = re.sub(r'[\[\]\*#]', '', description)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', clean_desc.lower())

        stop_words = {
            'the', 'and', 'for', 'with', 'that', 'this', 'are',
            'will', 'can', 'should', 'must'
        }
        keywords = [word for word in words if word not in stop_words]

        return keywords[:10]

    @staticmethod
    def _get_default_schema() -> Dict:
        """Return default schema for fallback"""
        return {
            "schema_version": "2.0",
            "format_type": "markdown-checklist",
            "patterns": {
                "task_line": {
                    "regex": r'^(\[ \]|\[X\]|\[x\]) - \*\*(?P<task_id>T\d+):\s*(?P<description>.*?)\*\*',
                    "groups": ["checkbox", "task_id", "description"]
                },
                "status_line": {
                    "regex": r'^(\[ \]|\[X\]|\[x\]) - (?P<field>Dev|QA|User Verification) Status: \[(?P<status>.*?)\]',
                    "groups": ["checkbox", "field", "status"]
                }
            },
            "status_semantics": {
                "fields": ["dev", "qa", "user_verification"],
                "field_mapping": {
                    "dev": ["Dev Status", "Dev"],
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
                        "not_started": ["Not Started"],
                        "in_progress": ["In Progress"],
                        "complete": ["Complete"]
                    },
                    "user_verification": {
                        "not_started": ["Not Started"],
                        "complete": ["Complete"]
                    }
                }
            }
        }
```

**Key Features**:
- Schema validation on initialization
- Named group extraction with fallback
- Semantic status normalization
- Comprehensive error handling
- Default schema for graceful degradation
- Reusable, testable design

---

### 3. Enhanced sense.md - Phase 6 Implementation

**File**: `resources/workflows/feature-implementation/commands/synapse/sense.md`

Add new Phase 6 section with concrete extraction algorithm:

```markdown
## Phase 6: Task Format Schema Analysis

After detecting active tasks file, analyze its format and generate a schema.

### Step 1: Read and Sample Tasks File

```python
# Read first 500 lines or entire file if smaller
with open(active_tasks_file, 'r') as f:
    lines = [f.readline() for _ in range(500)]
    if not lines[-1]:  # File has fewer than 500 lines
        f.seek(0)
        lines = f.readlines()
```

### Step 2: Detect Format Type

Count format indicators to determine primary format:

```python
import re

checklist_count = sum(1 for line in lines if re.match(r'^\s*-\s*\[[xX ]\]', line))
numbered_count = sum(1 for line in lines if re.match(r'^\s*\d+\.', line))
other_count = len(lines) - checklist_count - numbered_count

if checklist_count > len(lines) * 0.3:
    format_type = "markdown-checklist"
elif numbered_count > len(lines) * 0.3:
    format_type = "numbered-list"
else:
    format_type = "custom"
```

### Step 3: Extract Task Line Pattern

Find lines that appear to be main tasks (have task IDs or are bold):

```python
# Look for task ID patterns
task_id_candidates = []
for line in lines:
    # Common patterns: T001, TASK-001, #001, etc.
    match = re.search(r'\b([A-Z]+[-_]?\d{1,4})\b', line)
    if match:
        task_id_candidates.append(match.group(1))

# Determine most common pattern
if task_id_candidates:
    # Analyze first candidate to extract pattern
    sample_id = task_id_candidates[0]
    prefix = re.match(r'^([A-Z]+)', sample_id).group(1)
    digits = len(re.search(r'\d+', sample_id).group(0))

    task_id_pattern = f"{prefix}\\d{{{digits}}}"
else:
    task_id_pattern = "T\\d{3}"  # Default

# Build task line regex
if format_type == "markdown-checklist":
    task_line_regex = (
        f"^\\s*-\\s*\\[([ xX])\\]\\s*-\\s*"
        f"\\*\\*(?P<task_id>{task_id_pattern}):\\s*(?P<description>.+?)\\*\\*\\s*$"
    )
elif format_type == "numbered-list":
    task_line_regex = (
        f"^\\s*\\d+\\.\\s*"
        f"\\*\\*(?P<task_id>{task_id_pattern}):\\s*(?P<description>.+?)\\*\\*\\s*$"
    )
else:
    # Best effort for custom format
    task_line_regex = f"(?P<task_id>{task_id_pattern}):\\s*(?P<description>.+)"
```

### Step 4: Extract Status Information

Find all status lines and extract field names + values:

```python
status_lines = []
for line in lines:
    # Look for pattern: "Field Name: [Status Value]"
    match = re.search(r'([^:]+):\s*\[([^\]]+)\]', line)
    if match:
        field_name = match.group(1).strip()
        status_value = match.group(2).strip()
        status_lines.append((field_name, status_value))

# Group by field name
from collections import defaultdict
status_by_field = defaultdict(set)
for field, status in status_lines:
    status_by_field[field].add(status)

# Convert to lists
status_values = {
    field: sorted(list(values))
    for field, values in status_by_field.items()
}
```

### Step 5: Normalize Status Values

Map field names and status values to semantic categories:

```python
# Field name normalization
field_mapping = {}
for raw_field in status_values.keys():
    raw_lower = raw_field.lower()

    if 'dev' in raw_lower:
        semantic = 'dev'
    elif 'qa' in raw_lower or 'quality' in raw_lower:
        semantic = 'qa'
    elif 'user' in raw_lower or 'verification' in raw_lower:
        semantic = 'user_verification'
    else:
        semantic = raw_field.lower().replace(' ', '_')

    if semantic not in field_mapping:
        field_mapping[semantic] = []
    field_mapping[semantic].append(raw_field)

# Status value normalization
state_mapping = {}
for semantic_field, raw_fields in field_mapping.items():
    # Get all status values for this field
    all_values = set()
    for raw_field in raw_fields:
        all_values.update(status_values.get(raw_field, []))

    # Categorize values
    states = {
        'not_started': [],
        'in_progress': [],
        'complete': []
    }

    for value in all_values:
        value_lower = value.lower()

        if any(kw in value_lower for kw in ['not start', 'pending', 'todo', 'waiting']):
            states['not_started'].append(value)
        elif any(kw in value_lower for kw in ['progress', 'working', 'active', 'ongoing']):
            states['in_progress'].append(value)
        elif any(kw in value_lower for kw in ['complete', 'done', 'finish', 'pass', 'verified']):
            states['complete'].append(value)
        else:
            # Unknown - default to not_started for safety
            states['not_started'].append(value)

    # Remove in_progress if field doesn't have that state
    if not states['in_progress'] and len(all_values) == 2:
        # Binary state field (e.g., user verification)
        del states['in_progress']

    state_mapping[semantic_field] = states
```

### Step 6: Build Schema Object

```python
schema = {
    "schema_version": "2.0",
    "format_type": format_type,
    "patterns": {
        "task_line": {
            "regex": task_line_regex,
            "groups": ["checkbox", "task_id", "description"] if format_type == "markdown-checklist" else ["task_id", "description"],
            "example": lines[0].strip() if lines else ""
        },
        "status_line": {
            "regex": "^\\s*-\\s*\\[([ xX])\\]\\s*-\\s*(?P<field>[^:]+):\\s*\\[(?P<status>[^\\]]+)\\]\\s*$" if format_type == "markdown-checklist" else "(?P<field>[^:]+):\\s*\\[(?P<status>[^\\]]+)\\]",
            "groups": ["checkbox", "field", "status"] if format_type == "markdown-checklist" else ["field", "status"],
            "example": status_lines[0] if status_lines else ""
        }
    },
    "status_semantics": {
        "fields": list(field_mapping.keys()),
        "field_mapping": field_mapping,
        "states": state_mapping
    },
    "task_id_format": {
        "prefix": prefix,
        "digits": digits,
        "pattern": task_id_pattern,
        "example": task_id_candidates[0] if task_id_candidates else "T001"
    },
    "metadata": {
        "analyzed_at": datetime.now().isoformat(),
        "sample_size": len(lines),
        "total_tasks_found": len(task_id_candidates),
        "confidence": 1.0 if len(task_id_candidates) > 10 else 0.8
    }
}
```

### Step 7: Validate Schema

Re-parse tasks using generated schema to ensure it works:

```python
# Use the generated schema to parse the first 50 tasks
validation_tasks = parse_tasks_with_schema(lines[:200], schema)

success_rate = len(validation_tasks) / len(task_id_candidates) if task_id_candidates else 0

if success_rate >= 0.95:
    schema["validation"] = {
        "valid_sample_size": len(validation_tasks),
        "pattern_match_rate": success_rate,
        "last_validated": datetime.now().isoformat()
    }
    print(f"✅ Schema validation passed: {success_rate*100:.1f}% match rate")
else:
    print(f"⚠️ Schema validation below threshold: {success_rate*100:.1f}%")
    print("Manual review recommended - using schema with low confidence")
    schema["metadata"]["confidence"] = 0.5
```

### Step 8: Add Schema to Config

Add the generated schema to the workflow detection object:

```python
workflow_entry["task_format_schema"] = schema
```

### Error Handling

- If pattern extraction fails → set `format_type` to "custom" and use best-effort patterns
- If no status lines found → create minimal schema with task patterns only
- If validation fails → report to user and continue with low confidence
- If file is too large (>10MB) → only sample first 1000 lines
```

---

### 4. Updated Hook Integration

**File**: `resources/workflows/feature-implementation/hooks/pre-tool-use.py`

Replace hardcoded parsing with TaskSchemaParser:

```python
#!/usr/bin/env python3
import json
import sys
import os
from typing import List, Optional, Tuple

# Import the new parser
from synapse_cli.parsers.task_schema_parser import (
    TaskSchemaParser,
    ParsedTask,
    SchemaValidationError
)

def load_synapse_config():
    """Load synapse configuration from .synapse/config.json"""
    config_path = ".synapse/config.json"

    if not os.path.exists(config_path):
        print(f"⚠️ Synapse config not found at {config_path}", file=sys.stderr)
        return None

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}", file=sys.stderr)
        return None

def find_active_tasks_file(config):
    """Extract active tasks file path and schema from synapse config"""
    if not config:
        return None, None

    workflows = config.get("third_party_workflows", {}).get("detected", [])

    for workflow in workflows:
        tasks_file = workflow.get("active_tasks_file")
        if tasks_file:
            schema = workflow.get("task_format_schema")
            return tasks_file, schema

    return None, None

def check_task_blocking(
    target_task: Optional[ParsedTask],
    all_tasks: List[ParsedTask]
) -> Tuple[bool, str]:
    """Check if work should be blocked - uses semantic states"""

    if not all_tasks:
        return False, ""

    if target_task:
        # Allow continued work on in-progress tasks
        if target_task.dev_state == "in_progress":
            print(f"✅ Allowing continued work on: {target_task.task_id}", file=sys.stderr)
            return False, ""

        # Allow new tasks that haven't started
        if (target_task.dev_state == "not_started" and
            target_task.qa_state == "not_started" and
            target_task.uv_state == "not_started"):

            # Check for blocking incomplete tasks
            blocking_in_progress = [
                t.task_id for t in all_tasks
                if t.task_id != target_task.task_id and t.dev_state == "in_progress"
            ]

            blocking_awaiting_qa = [
                t.task_id for t in all_tasks
                if t.task_id != target_task.task_id
                and t.dev_state == "complete"
                and (t.qa_state != "complete" or t.uv_state != "complete")
            ]

            if blocking_in_progress:
                return True, f"Cannot start new task - others in progress: {', '.join(blocking_in_progress)}"

            if blocking_awaiting_qa:
                return True, f"Cannot start new task - others awaiting QA: {', '.join(blocking_awaiting_qa)}"

            print(f"✅ Allowing work on new task: {target_task.task_id}", file=sys.stderr)
            return False, ""

        # Block work on completed tasks awaiting QA
        if (target_task.dev_state == "complete" and
            (target_task.qa_state != "complete" or target_task.uv_state != "complete")):
            return True, f"Task '{target_task.task_id}' needs QA/verification before re-implementation"

    else:
        # No clear target task - check for any incomplete work
        blocking = [
            t.task_id for t in all_tasks
            if t.dev_state == "in_progress"
            or (t.dev_state == "complete" and (t.qa_state != "complete" or t.uv_state != "complete"))
        ]

        if blocking:
            return True, f"Cannot start work - incomplete tasks: {', '.join(blocking)}"

    return False, ""

def find_matching_task(prompt: str, parsed_tasks: List[ParsedTask]) -> Optional[ParsedTask]:
    """Find which task the implementer is trying to work on"""
    if not parsed_tasks:
        return None

    prompt_lower = prompt.lower()

    # Try exact task ID matching first
    for task in parsed_tasks:
        if task.task_id.lower() in prompt_lower:
            print(f"✅ Found exact task ID match: {task.task_id}", file=sys.stderr)
            return task

    # Try keyword matching
    best_match = None
    best_score = 0

    for task in parsed_tasks:
        score = sum(1 for keyword in task.keywords if keyword in prompt_lower)
        if score > best_score:
            best_score = score
            best_match = task

    if best_match and best_score > 0:
        print(f"✅ Found keyword match: {best_match.task_id} (score: {best_score})", file=sys.stderr)
        return best_match

    print("❓ No clear task match found", file=sys.stderr)
    return None

def main():
    print("🔍 Running task implementer pre-tool gate hook...", file=sys.stderr)

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(2)

    # Only process Task tool calls for implementer subagent
    if input_data.get("tool_name") != "Task":
        sys.exit(1)

    tool_input = input_data.get("tool_input", {})
    if tool_input.get("subagent_type") != "implementer":
        sys.exit(1)

    print("🔍 Implementer task detected - analyzing...", file=sys.stderr)

    # Load config and find active tasks file
    config = load_synapse_config()
    if not config:
        print("ℹ️ No synapse config - allowing task", file=sys.stderr)
        sys.exit(1)

    tasks_file_path, schema = find_active_tasks_file(config)
    if not tasks_file_path:
        print("ℹ️ No task management system - allowing task", file=sys.stderr)
        sys.exit(1)

    # Parse tasks using schema
    try:
        parser = TaskSchemaParser(schema)
        parsed_tasks = parser.parse_tasks_file(tasks_file_path)

        if not parsed_tasks:
            print("ℹ️ No tasks found - allowing task", file=sys.stderr)
            sys.exit(1)

        print(f"📊 Parsed {len(parsed_tasks)} tasks", file=sys.stderr)

    except SchemaValidationError as e:
        print(f"❌ Schema validation failed: {e}", file=sys.stderr)
        print("ℹ️ Falling back to allow (run 'synapse sense' to fix)", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error parsing tasks: {e}", file=sys.stderr)
        sys.exit(1)

    # Find target task
    prompt = tool_input.get("prompt", "")
    target_task = find_matching_task(prompt, parsed_tasks)

    # Check blocking conditions
    should_block, reason = check_task_blocking(target_task, parsed_tasks)

    if should_block:
        print(f"❌ Blocking: {reason}", file=sys.stderr)
        output = {"decision": "block", "reason": reason}
        print(json.dumps(output))
        sys.exit(2)

    print("✅ Allowing implementer task", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
```

**Key Changes**:
- Uses `TaskSchemaParser` instead of raw regex
- Works with semantic states (`dev_state`, not `dev_status` strings)
- Comprehensive error handling
- Cleaner business logic

---

### 5. Schema Migration Support

**File**: `src/synapse_cli/parsers/schema_migrator.py`

```python
#!/usr/bin/env python3
"""Schema migration utilities for evolving task format schemas"""
from typing import Dict

def migrate_schema(schema: Dict) -> Dict:
    """Migrate old schemas to current version (2.0)"""
    version = schema.get("schema_version", "0.0")

    if version == "0.0":
        # Experimental format from experiments/
        return migrate_v0_to_v2(schema)
    elif version == "1.0":
        return migrate_v1_to_v2(schema)
    elif version == "2.0":
        return schema  # Already current
    else:
        raise ValueError(f"Unknown schema version: {version}")

def migrate_v0_to_v2(old_schema: Dict) -> Dict:
    """Migrate experimental schema to v2.0"""

    # Extract old patterns (used numeric groups)
    old_patterns = old_schema.get("patterns", {})

    # Convert to new named-group format
    new_patterns = {}

    if "task_line" in old_patterns:
        # Old: '^(\[ \]|\[X\]|\[x\]) - \*\*(T\d+):\s*(.*?)\*\*'
        # New: Add named groups
        new_patterns["task_line"] = {
            "regex": r'^(\[ \]|\[X\]|\[x\]) - \*\*(?P<task_id>T\d+):\s*(?P<description>.*?)\*\*',
            "groups": ["checkbox", "task_id", "description"],
            "example": "- [X] - **T001: Task description**"
        }

    if "status_line" in old_patterns:
        new_patterns["status_line"] = {
            "regex": r'^(\[ \]|\[X\]|\[x\]) - (?P<field>Dev|QA|User Verification) Status: \[(?P<status>.*?)\]',
            "groups": ["checkbox", "field", "status"],
            "example": "- [X] - Dev Status: [Complete]"
        }

    # Convert status_values array format to semantic dict format
    old_status_vals = old_schema.get("status_values", {})

    new_states = {}
    for field, values in old_status_vals.items():
        if isinstance(values, list):
            # Old format: ["Not Started", "In Progress", "Complete"]
            # Map to semantic states
            states_dict = {}
            if len(values) >= 1:
                states_dict["not_started"] = [values[0]]
            if len(values) >= 2:
                states_dict["in_progress"] = [values[1]]
            if len(values) >= 3:
                states_dict["complete"] = [values[2]]
            elif len(values) == 2:
                # Binary state (no in_progress)
                states_dict["complete"] = [values[1]]

            new_states[field] = states_dict

    # Build field mapping
    field_mapping = {
        "dev": ["Dev Status", "Dev"],
        "qa": ["QA Status", "QA"],
        "user_verification": ["User Verification Status", "User Verification"]
    }

    return {
        "schema_version": "2.0",
        "format_type": old_schema.get("format_type", "markdown-checklist"),
        "patterns": new_patterns,
        "status_semantics": {
            "fields": list(new_states.keys()),
            "field_mapping": field_mapping,
            "states": new_states
        },
        "task_id_format": {
            "prefix": old_schema.get("structure", {}).get("task_id_prefix", "T"),
            "digits": old_schema.get("structure", {}).get("task_id_digits", 3),
            "pattern": old_schema.get("task_id_format", "T\\d{3}"),
            "example": "T001"
        },
        "metadata": old_schema.get("metadata", {})
    }

def migrate_v1_to_v2(old_schema: Dict) -> Dict:
    """Migrate v1.0 to v2.0 (if needed in future)"""
    # Currently v1.0 and v2.0 are compatible
    old_schema["schema_version"] = "2.0"
    return old_schema
```

---

## Implementation Strategy

### Phase 1: Foundation (Week 1)
1. Create schema v2 structure document
2. Define validation rules and test cases
3. Design migration strategy

### Phase 2: Parser (Week 1-2)
1. Implement `TaskSchemaParser` class
2. Add comprehensive error handling
3. Write unit tests for parser
4. Test with experimental schema

### Phase 3: Sense Enhancement (Week 2-3)
1. Implement Phase 6 extraction algorithm
2. Add schema validation tests
3. Test with multiple format types
4. Enhance error reporting

### Phase 4: Hook Integration (Week 3)
1. Update all three hooks to use new parser
2. Simplify business logic
3. Add schema migration to handle old configs
4. Integration testing

### Phase 5: Testing (Week 4)
1. Test with OpenSpec format
2. Test with GitHub Spec Kit format
3. Test with benchmarks format (experimental)
4. Edge case testing
5. Performance testing

### Phase 6: Documentation (Week 4)
1. Document schema v2 format
2. Write migration guide
3. Update all command documentation
4. Create troubleshooting guide

### Phase 7: Deployment (Week 5)
1. Merge to main workflows
2. Add CLI validation commands
3. Update CHANGELOG
4. Release notes

---

## Testing Plan

### Unit Tests

**File**: `tests/test_task_schema_parser.py`

```python
def test_parse_valid_task_line():
    """Test parsing a valid task line"""

def test_parse_invalid_task_line():
    """Test graceful handling of invalid task line"""

def test_parse_status_line_with_variations():
    """Test parsing status lines with different value variations"""

def test_normalize_field_names():
    """Test field name normalization"""

def test_normalize_status_values():
    """Test status value normalization"""

def test_schema_validation():
    """Test schema validation catches errors"""

def test_default_schema_fallback():
    """Test fallback to default schema when none provided"""
```

### Integration Tests

**File**: `tests/test_workflow_integration.py`

```python
def test_sense_generates_valid_schema():
    """Test sense command generates valid v2 schema"""

def test_hooks_parse_with_generated_schema():
    """Test hooks can parse tasks using sense-generated schema"""

def test_task_blocking_logic():
    """Test task blocking works with semantic states"""

def test_multi_format_support():
    """Test with OpenSpec, Spec Kit, and custom formats"""
```

### End-to-End Tests

**File**: `tests/e2e/test_full_workflow.py`

```python
def test_openspec_workflow():
    """Test full workflow: sense → implementer → hooks with OpenSpec"""

def test_spec_kit_workflow():
    """Test full workflow with GitHub Spec Kit format"""

def test_custom_format_workflow():
    """Test full workflow with custom tasks.md format"""
```

---

## Migration Guide

### For Users with Experimental Schemas (v0.0)

1. **Backup your config**:
   ```bash
   cp .synapse/config.json .synapse/config.json.backup
   ```

2. **Run sense with migration**:
   ```bash
   synapse sense --migrate
   ```

3. **Verify migration**:
   ```bash
   synapse sense --validate
   ```

4. **If validation fails**, restore backup and report issue:
   ```bash
   cp .synapse/config.json.backup .synapse/config.json
   ```

### Breaking Changes

1. **Schema version field required** - All schemas must have `schema_version`
2. **Status values changed from arrays to dicts** - Old: `["Not Started", "In Progress"]`, New: `{"not_started": ["Not Started"], ...}`
3. **Pattern structure changed** - Must include `regex`, `groups`, and `example` keys

---

## Success Metrics

### Technical
- [ ] 100% of unit tests passing
- [ ] 95%+ pattern match rate on validation
- [ ] Zero schema-related runtime errors in production
- [ ] Support for 3+ task format types

### User Experience
- [ ] Sense command completes in <10 seconds
- [ ] Clear error messages for all failure modes
- [ ] Successful migration of 100% of experimental configs
- [ ] Zero manual schema fixes required

### Quality
- [ ] Code coverage >80%
- [ ] All linting/type checks passing
- [ ] Documentation complete and accurate
- [ ] Zero critical bugs in production

---

## Open Questions

1. **Multi-file support**: Should schema support projects with multiple tasks.md files?
2. **Schema updates**: How should hooks handle schema updates mid-session?
3. **Performance**: What's acceptable parse time for 1000+ task files?
4. **Custom extractors**: Should we allow users to provide custom parsing logic?
5. **Backward compatibility**: How long should we support v0.0 schemas?

---

## Appendix: Experimental Files Reference

The experimental implementation that informed this proposal:

- `experiments/sense.md` - Enhanced sense command with Phase 6
- `experiments/config.json` - Real schema from benchmarks project
- `experiments/pre-tool-use.py` - Hook with schema-driven parsing
- `experiments/post-tool-use.py` - Quality gate hook
- `experiments/verification-complete.py` - Verification hook
- `experiments/implementer.md` - Task-aware implementer agent
- `experiments/verifier.md` - QA verification agent

These files demonstrate the concept works but need the improvements outlined in this proposal for production readiness.
