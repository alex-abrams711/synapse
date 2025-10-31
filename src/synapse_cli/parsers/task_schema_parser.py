#!/usr/bin/env python3
"""Schema-driven task parser with validation and fallback."""
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ParsedTask:
    """Parsed task with semantic states."""

    task_id: str
    description: str
    dev_state: str  # "not_started" | "in_progress" | "complete"
    qa_state: str
    uv_state: str
    keywords: List[str]
    line_number: int


class SchemaValidationError(Exception):
    """Raised when schema is invalid."""

    pass


class TaskSchemaParser:
    """Schema-driven task parser with validation and fallback."""

    SUPPORTED_VERSIONS = ["2.0"]

    def __init__(self, schema: Optional[Dict] = None):
        self.schema = schema or self._get_default_schema()
        self.validate_schema()

    def validate_schema(self):
        """Validate schema structure and compatibility."""
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
            if not isinstance(pattern, dict):
                raise SchemaValidationError(
                    f"Invalid pattern structure: {pattern_name} (expected dict)"
                )

            if "regex" not in pattern:
                raise SchemaValidationError(
                    f"Pattern {pattern_name} missing 'regex' field"
                )

            # Validate regex compiles
            try:
                re.compile(pattern["regex"])
            except re.error as e:
                raise SchemaValidationError(
                    f"Invalid regex in {pattern_name}: {e}"
                ) from e

        # Validate status_semantics
        status_semantics = self.schema["status_semantics"]
        if "field_mapping" not in status_semantics:
            raise SchemaValidationError(
                "status_semantics missing 'field_mapping'"
            )
        if "states" not in status_semantics:
            raise SchemaValidationError("status_semantics missing 'states'")

    def parse_task_line(self, line: str) -> Optional[Dict]:
        """Parse a task line using schema pattern."""
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
                "checkbox": (
                    match.group("checkbox")
                    if "checkbox" in match.groupdict()
                    else None
                ),
            }
        except IndexError as e:
            print(
                f"⚠️  Pattern matched but groups missing: {e}",
                file=sys.stderr,
            )
            return None

    def parse_status_line(self, line: str) -> Optional[Dict]:
        """Parse a status line and normalize to semantic value."""
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
            print(
                f"⚠️  Unknown status field: '{field_raw}' - ignoring",
                file=sys.stderr,
            )
            return None

        # Normalize status value to semantic state
        semantic_state = self._normalize_status(semantic_field, status_raw)

        return {
            "field": semantic_field,  # "dev", "qa", "user_verification"
            "state": semantic_state,  # "not_started", "in_progress", "complete"
            "raw_field": field_raw,
            "raw_status": status_raw,
        }

    def _normalize_field(self, field_raw: str) -> Optional[str]:
        """Map raw field name to semantic category."""
        field_mapping = self.schema["status_semantics"]["field_mapping"]

        for semantic, variations in field_mapping.items():
            if field_raw in variations:
                return semantic

        return None

    def _normalize_status(self, field: str, status_raw: str) -> str:
        """Map raw status value to semantic state."""
        states = self.schema["status_semantics"]["states"][field]

        for semantic_state, variations in states.items():
            if status_raw in variations:
                return semantic_state

        # Unknown status - default to not_started for safety
        print(
            f"⚠️  Unknown status '{status_raw}' for field '{field}' - "
            f"defaulting to not_started",
            file=sys.stderr,
        )
        return "not_started"

    def get_canonical_status(self, field: str, semantic_state: str) -> str:
        """Get the canonical status string for a field/state combo."""
        states = self.schema["status_semantics"]["states"][field]
        variations = states.get(semantic_state, [])
        return variations[0] if variations else semantic_state

    def parse_tasks_file(self, file_path: str) -> List[ParsedTask]:
        """Parse entire tasks file and return structured tasks."""
        with open(file_path, encoding="utf-8") as f:
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
                    line_number=i,
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
        """Extract searchable keywords from description."""
        clean_desc = re.sub(r"[\[\]\*#]", "", description)
        words = re.findall(r"\b[a-zA-Z]{3,}\b", clean_desc.lower())

        stop_words = {
            "the",
            "and",
            "for",
            "with",
            "that",
            "this",
            "are",
            "will",
            "can",
            "should",
            "must",
        }
        keywords = [word for word in words if word not in stop_words]

        return keywords[:10]

    @staticmethod
    def _get_default_schema() -> Dict:
        """Return default schema for fallback."""
        return {
            "schema_version": "2.0",
            "format_type": "markdown-checklist",
            "patterns": {
                "task_line": {
                    "regex": r"^(\[ \]|\[X\]|\[x\]) - \*\*(?P<task_id>T\d+):\s*(?P<description>.*?)\*\*",
                    "groups": ["checkbox", "task_id", "description"],
                },
                "status_line": {
                    "regex": r"^(\[ \]|\[X\]|\[x\]) - (?P<field>Dev|QA|User Verification) Status: \[(?P<status>.*?)\]",
                    "groups": ["checkbox", "field", "status"],
                },
            },
            "status_semantics": {
                "fields": ["dev", "qa", "user_verification"],
                "field_mapping": {
                    "dev": ["Dev Status", "Dev"],
                    "qa": ["QA Status", "QA"],
                    "user_verification": [
                        "User Verification Status",
                        "User Verification",
                    ],
                },
                "states": {
                    "dev": {
                        "not_started": ["Not Started"],
                        "in_progress": ["In Progress"],
                        "complete": ["Complete"],
                    },
                    "qa": {
                        "not_started": ["Not Started"],
                        "in_progress": ["In Progress"],
                        "complete": ["Complete"],
                    },
                    "user_verification": {
                        "not_started": ["Not Started"],
                        "complete": ["Complete"],
                    },
                },
            },
        }
