#!/usr/bin/env python3
"""Schema generator for detecting task format from tasks.md files."""
import re
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class SchemaGenerator:
    """Generate task format schema by analyzing tasks files."""

    def __init__(self, max_sample_lines: int = 500):
        """
        Initialize schema generator.

        Args:
            max_sample_lines: Maximum lines to read for analysis
        """
        self.max_sample_lines = max_sample_lines

    def generate_schema(
        self, file_path: str, source_file: Optional[str] = None
    ) -> Dict:
        """
        Generate schema by analyzing a tasks file.

        Args:
            file_path: Path to tasks file
            source_file: Optional source file path for metadata

        Returns:
            Complete v2.0 schema dict
        """
        # Step 1: Read and sample file
        lines = self._read_sample(file_path)

        # Step 2: Detect format type
        format_type = self._detect_format_type(lines)

        # Step 3: Extract task ID pattern
        task_id_candidates = self._extract_task_ids(lines)
        task_id_format = self._analyze_task_id_format(task_id_candidates)

        # Step 4: Build task line pattern
        task_line_pattern = self._build_task_line_pattern(
            format_type, task_id_format
        )

        # Step 5: Extract status information
        status_lines = self._extract_status_lines(lines)
        status_by_field = self._group_status_by_field(status_lines)

        # Step 6: Build status line pattern
        status_line_pattern = self._build_status_line_pattern(
            format_type, list(status_by_field.keys())
        )

        # Step 7: Normalize status semantics
        field_mapping = self._normalize_field_mapping(
            list(status_by_field.keys())
        )
        state_mapping = self._normalize_state_mapping(
            status_by_field, field_mapping
        )

        # Step 8: Build schema object
        schema = {
            "schema_version": "2.0",
            "format_type": format_type,
            "patterns": {
                "task_line": task_line_pattern,
                "status_line": status_line_pattern,
            },
            "status_semantics": {
                "fields": list(field_mapping.keys()),
                "field_mapping": field_mapping,
                "states": state_mapping,
            },
            "task_id_format": task_id_format,
            "metadata": {
                "analyzed_at": datetime.now().isoformat(),
                "sample_size": len(lines),
                "total_tasks_found": len(task_id_candidates),
                "confidence": self._calculate_confidence(
                    len(task_id_candidates), len(lines)
                ),
                "format_detected_by": "sense_command",
                "source_file": source_file or file_path,
            },
        }

        return schema

    def _read_sample(self, file_path: str) -> List[str]:
        """
        Read sample of lines from file.

        Args:
            file_path: Path to file

        Returns:
            List of lines (up to max_sample_lines)
        """
        with open(file_path, encoding="utf-8") as f:
            lines = []
            for i, line in enumerate(f):
                if i >= self.max_sample_lines:
                    break
                lines.append(line.rstrip())
            return lines

    def _detect_format_type(self, lines: List[str]) -> str:
        """
        Detect format type from line patterns.

        Args:
            lines: Sample lines from file

        Returns:
            Format type: "markdown-checklist", "numbered-list", or "custom"
        """
        checklist_count = sum(
            1 for line in lines if re.match(r"^\s*-?\s*\[[xX ]\]", line)
        )
        numbered_count = sum(
            1 for line in lines if re.match(r"^\s*\d+\.", line)
        )

        total_lines = len([line for line in lines if line.strip()])

        if total_lines == 0:
            return "markdown-checklist"  # Default

        checklist_ratio = checklist_count / total_lines
        numbered_ratio = numbered_count / total_lines

        if checklist_ratio > 0.3:
            return "markdown-checklist"
        elif numbered_ratio > 0.3:
            return "numbered-list"
        else:
            return "custom"

    def _extract_task_ids(self, lines: List[str]) -> List[str]:
        """
        Extract all task IDs from lines.

        Args:
            lines: Sample lines from file

        Returns:
            List of task ID strings
        """
        task_ids = []

        # Common patterns for task IDs
        patterns = [
            r"\b([A-Z]+[-_]?\d{1,4})\b",  # T001, TASK-001, BUG_123
            r"^#+\s*([A-Z]+[-_]?\d{1,4})\b",  # # T001
        ]

        for line in lines:
            # Look for bold markers which often indicate task lines
            if "**" in line or re.match(r"^#+\s", line):
                for pattern in patterns:
                    matches = re.findall(pattern, line)
                    task_ids.extend(matches)

        return task_ids

    def _analyze_task_id_format(
        self, task_ids: List[str]
    ) -> Dict[str, str]:
        """
        Analyze task ID format from samples.

        Args:
            task_ids: List of task IDs

        Returns:
            Task ID format dict
        """
        if not task_ids:
            # Default format
            return {
                "prefix": "T",
                "digits": 3,
                "pattern": r"T\d{3}",
                "example": "T001",
                "separator": "",
            }

        # Analyze first task ID
        sample_id = task_ids[0]

        # Extract prefix
        prefix_match = re.match(r"^([A-Z]+)", sample_id)
        prefix = prefix_match.group(1) if prefix_match else "T"

        # Extract separator
        separator = ""
        if "-" in sample_id:
            separator = "-"
        elif "_" in sample_id:
            separator = "_"

        # Extract number and count digits
        number_match = re.search(r"\d+", sample_id)
        if number_match:
            number = number_match.group(0)
            digits = len(number)
        else:
            digits = 3

        # Build pattern
        if separator:
            pattern = f"{prefix}{re.escape(separator)}\\d{{{digits}}}"
        else:
            pattern = f"{prefix}\\d{{{digits}}}"

        # Generate example
        example = f"{prefix}{separator}{str(1).zfill(digits)}"

        return {
            "prefix": prefix,
            "digits": digits,
            "pattern": pattern,
            "example": example,
            "separator": separator,
        }

    def _build_task_line_pattern(
        self, format_type: str, task_id_format: Dict
    ) -> Dict:
        """
        Build task line regex pattern.

        Args:
            format_type: Detected format type
            task_id_format: Task ID format dict

        Returns:
            Pattern dict with regex, groups, example
        """
        task_id_pattern = task_id_format["pattern"]

        if format_type == "markdown-checklist":
            regex = (
                rf"^\s*-\s*\[([ xX])\]\s*-?\s*"
                rf"\*\*(?P<task_id>{task_id_pattern}):\s*(?P<description>.+?)\*\*\s*$"
            )
            groups = ["checkbox", "task_id", "description"]
            example = f"- [X] - **{task_id_format['example']}: Create database schema**"

        elif format_type == "numbered-list":
            regex = (
                rf"^\s*\d+\.\s*"
                rf"\*\*(?P<task_id>{task_id_pattern}):\s*(?P<description>.+?)\*\*\s*$"
            )
            groups = ["task_id", "description"]
            example = f"1. **{task_id_format['example']}: Create database schema**"

        else:  # custom
            regex = (
                rf"(?P<task_id>{task_id_pattern}):\s*(?P<description>.+)"
            )
            groups = ["task_id", "description"]
            example = f"{task_id_format['example']}: Create database schema"

        return {
            "regex": regex,
            "groups": groups,
            "example": example,
            "required": True,
        }

    def _extract_status_lines(self, lines: List[str]) -> List[Tuple[str, str]]:
        """
        Extract status field and value pairs.

        Args:
            lines: Sample lines from file

        Returns:
            List of (field_name, status_value) tuples
        """
        status_lines = []

        # Pattern: Match field name and status value, handling markdown prefixes
        # Remove leading checkboxes, dashes, numbers, etc
        pattern = r"(?:^[\s\-\d\.\[\]xX]*)?([A-Za-z][^:]*?):\s*\[([^\]]+)\]"

        for line in lines:
            match = re.search(pattern, line)
            if match:
                field_name = match.group(1).strip()
                status_value = match.group(2).strip()

                # Filter out unlikely status fields
                if self._is_likely_status_field(field_name):
                    status_lines.append((field_name, status_value))

        return status_lines

    def _is_likely_status_field(self, field_name: str) -> bool:
        """
        Check if field name is likely a status field.

        Args:
            field_name: Field name to check

        Returns:
            True if likely a status field
        """
        field_lower = field_name.lower()

        # Status field indicators
        indicators = [
            "status",
            "state",
            "dev",
            "qa",
            "test",
            "verification",
            "review",
            "progress",
        ]

        return any(indicator in field_lower for indicator in indicators)

    def _group_status_by_field(
        self, status_lines: List[Tuple[str, str]]
    ) -> Dict[str, List[str]]:
        """
        Group status values by field name.

        Args:
            status_lines: List of (field, value) tuples

        Returns:
            Dict mapping field names to sorted list of unique values
        """
        status_by_field = defaultdict(set)

        for field, value in status_lines:
            status_by_field[field].add(value)

        # Convert to sorted lists
        return {
            field: sorted(list(values))
            for field, values in status_by_field.items()
        }

    def _build_status_line_pattern(
        self, format_type: str, field_names: List[str]
    ) -> Dict:
        """
        Build status line regex pattern.

        Args:
            format_type: Detected format type
            field_names: List of detected field names

        Returns:
            Pattern dict with regex, groups, example
        """
        if format_type == "markdown-checklist":
            regex = (
                r"^\s*-\s*\[([ xX])\]\s*-?\s*"
                r"(?P<field>[^:]+):\s*\[(?P<status>[^\]]+)\]\s*$"
            )
            groups = ["checkbox", "field", "status"]
            example_field = field_names[0] if field_names else "Dev Status"
            example = f"- [X] - {example_field}: [Complete]"

        elif format_type == "numbered-list":
            regex = r"^\s*-\s*(?P<field>[^:]+):\s*\[(?P<status>[^\]]+)\]\s*$"
            groups = ["field", "status"]
            example_field = field_names[0] if field_names else "Dev Status"
            example = f"  - {example_field}: [Complete]"

        else:  # custom
            regex = r"(?P<field>[^:]+):\s*\[(?P<status>[^\]]+)\]"
            groups = ["field", "status"]
            example_field = field_names[0] if field_names else "Status"
            example = f"{example_field}: [Complete]"

        return {
            "regex": regex,
            "groups": groups,
            "example": example,
            "required": True,
        }

    def _normalize_field_mapping(
        self, raw_fields: List[str]
    ) -> Dict[str, List[str]]:
        """
        Create semantic field mapping.

        Args:
            raw_fields: List of raw field names

        Returns:
            Dict mapping semantic names to raw field variations
        """
        mapping = defaultdict(list)

        for raw_field in raw_fields:
            raw_lower = raw_field.lower()

            # Determine semantic category
            if "dev" in raw_lower:
                semantic = "dev"
            elif "qa" in raw_lower or "quality" in raw_lower or "test" in raw_lower:
                semantic = "qa"
            elif "user" in raw_lower or "verification" in raw_lower or "uv" in raw_lower:
                semantic = "user_verification"
            else:
                # Create custom semantic field
                semantic = raw_field.lower().replace(" ", "_").replace("-", "_")

            mapping[semantic].append(raw_field)

        return dict(mapping)

    def _normalize_state_mapping(
        self,
        status_by_field: Dict[str, List[str]],
        field_mapping: Dict[str, List[str]],
    ) -> Dict[str, Dict[str, List[str]]]:
        """
        Create semantic state mapping.

        Args:
            status_by_field: Raw field → values mapping
            field_mapping: Semantic field → raw field mapping

        Returns:
            Semantic field → state → values mapping
        """
        state_mapping = {}

        for semantic_field, raw_fields in field_mapping.items():
            # Collect all values for this semantic field
            all_values = set()
            for raw_field in raw_fields:
                all_values.update(status_by_field.get(raw_field, []))

            # Categorize values into semantic states
            states = {
                "not_started": [],
                "in_progress": [],
                "complete": [],
            }

            for value in all_values:
                value_lower = value.lower()

                if any(
                    kw in value_lower
                    for kw in ["not start", "pending", "todo", "waiting"]
                ):
                    states["not_started"].append(value)
                elif any(
                    kw in value_lower
                    for kw in [
                        "progress",
                        "working",
                        "active",
                        "ongoing",
                        "implementing",
                    ]
                ):
                    states["in_progress"].append(value)
                elif any(
                    kw in value_lower
                    for kw in [
                        "complete",
                        "done",
                        "finish",
                        "pass",
                        "verified",
                        "approved",
                    ]
                ):
                    states["complete"].append(value)
                else:
                    # Unknown - default to not_started for safety
                    states["not_started"].append(value)

            # Remove in_progress if empty (binary field)
            if not states["in_progress"] and len(all_values) <= 2:
                del states["in_progress"]

            state_mapping[semantic_field] = states

        return state_mapping

    def _calculate_confidence(
        self, total_tasks: int, sample_size: int
    ) -> float:
        """
        Calculate confidence score for schema.

        Args:
            total_tasks: Number of tasks found
            sample_size: Number of lines analyzed

        Returns:
            Confidence score (0.0 - 1.0)
        """
        if total_tasks >= 50:
            return 1.0
        elif total_tasks >= 10:
            return 0.7 + (total_tasks - 10) / 40 * 0.3
        elif total_tasks >= 5:
            return 0.6
        else:
            return 0.5
