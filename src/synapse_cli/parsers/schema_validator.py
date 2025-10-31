#!/usr/bin/env python3
"""Schema validator for testing generated schemas."""
from datetime import datetime
from typing import Dict, List, Tuple
from .task_schema_parser import TaskSchemaParser, SchemaValidationError


class ValidationResult:
    """Result of schema validation."""

    def __init__(
        self,
        passed: bool,
        match_rate: float,
        tasks_matched: int,
        tasks_expected: int,
        errors: List[str],
    ):
        """
        Initialize validation result.

        Args:
            passed: Whether validation passed threshold
            match_rate: Percentage of tasks matched (0.0-1.0)
            tasks_matched: Number of tasks successfully parsed
            tasks_expected: Expected number of tasks
            errors: List of error messages
        """
        self.passed = passed
        self.match_rate = match_rate
        self.tasks_matched = tasks_matched
        self.tasks_expected = tasks_expected
        self.errors = errors

    def __str__(self) -> str:
        """String representation."""
        status = "✅ PASSED" if self.passed else "❌ FAILED"
        return (
            f"{status}: {self.match_rate:.1%} match rate "
            f"({self.tasks_matched}/{self.tasks_expected} tasks)"
        )


class SchemaValidator:
    """Validate generated schemas by re-parsing tasks."""

    DEFAULT_THRESHOLD = 0.95  # 95% match rate required
    MIN_SAMPLE_SIZE = 10  # Minimum tasks for meaningful validation

    def __init__(self, match_threshold: float = DEFAULT_THRESHOLD):
        """
        Initialize validator.

        Args:
            match_threshold: Minimum match rate to pass (0.0-1.0)
        """
        self.match_threshold = match_threshold

    def validate_schema(
        self, schema: Dict, tasks_file: str, expected_task_count: int = None
    ) -> ValidationResult:
        """
        Validate schema by parsing tasks file.

        Args:
            schema: Schema to validate
            tasks_file: Path to tasks file
            expected_task_count: Expected number of tasks (auto-detect if None)

        Returns:
            ValidationResult with pass/fail and metrics
        """
        errors = []

        # Step 1: Validate schema structure
        try:
            parser = TaskSchemaParser(schema)
        except SchemaValidationError as e:
            return ValidationResult(
                passed=False,
                match_rate=0.0,
                tasks_matched=0,
                tasks_expected=0,
                errors=[f"Schema validation failed: {e}"],
            )

        # Step 2: Parse tasks file
        try:
            parsed_tasks = parser.parse_tasks_file(tasks_file)
        except Exception as e:
            return ValidationResult(
                passed=False,
                match_rate=0.0,
                tasks_matched=0,
                tasks_expected=0,
                errors=[f"Failed to parse tasks file: {e}"],
            )

        # Step 3: Calculate match rate
        tasks_matched = len(parsed_tasks)

        if expected_task_count is None:
            # Auto-detect expected count from file
            expected_task_count = self._count_expected_tasks(
                tasks_file, schema
            )

        if expected_task_count == 0:
            return ValidationResult(
                passed=False,
                match_rate=0.0,
                tasks_matched=0,
                tasks_expected=0,
                errors=["No tasks found in file"],
            )

        match_rate = tasks_matched / expected_task_count

        # Step 4: Check thresholds
        passed = True

        if match_rate < self.match_threshold:
            passed = False
            errors.append(
                f"Match rate {match_rate:.1%} below threshold {self.match_threshold:.1%}"
            )

        if tasks_matched < self.MIN_SAMPLE_SIZE:
            passed = False
            errors.append(
                f"Only {tasks_matched} tasks matched (min {self.MIN_SAMPLE_SIZE} required)"
            )

        return ValidationResult(
            passed=passed,
            match_rate=match_rate,
            tasks_matched=tasks_matched,
            tasks_expected=expected_task_count,
            errors=errors,
        )

    def add_validation_metadata(
        self, schema: Dict, validation_result: ValidationResult
    ) -> Dict:
        """
        Add validation metadata to schema.

        Args:
            schema: Schema to update
            validation_result: Validation result

        Returns:
            Updated schema with validation section
        """
        schema["validation"] = {
            "valid_sample_size": validation_result.tasks_matched,
            "pattern_match_rate": validation_result.match_rate,
            "last_validated": datetime.now().isoformat(),
            "validation_passed": validation_result.passed,
        }

        # Update confidence based on validation
        if "metadata" in schema:
            if validation_result.passed:
                # Boost confidence if validation passed
                current_confidence = schema["metadata"].get("confidence", 0.5)
                schema["metadata"]["confidence"] = min(
                    1.0, current_confidence * 1.1
                )
            else:
                # Lower confidence if validation failed
                schema["metadata"]["confidence"] = 0.5

        return schema

    def _count_expected_tasks(self, tasks_file: str, schema: Dict) -> int:
        """
        Count expected tasks by looking for task ID pattern.

        Args:
            tasks_file: Path to tasks file
            schema: Schema with task_id_format

        Returns:
            Expected number of tasks
        """
        import re

        task_id_pattern = schema.get("task_id_format", {}).get(
            "pattern", r"T\d{3}"
        )

        count = 0
        with open(tasks_file, encoding="utf-8") as f:
            for line in f:
                if re.search(task_id_pattern, line):
                    count += 1

        return count
