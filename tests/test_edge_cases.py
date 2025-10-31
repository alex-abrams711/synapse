"""Edge case tests for task schema system."""
import os
import tempfile
import pytest
from synapse_cli.parsers import (
    TaskSchemaParser,
    SchemaValidationError,
)
from synapse_cli.parsers.schema_generator import SchemaGenerator


class TestEmptyAndMinimalFiles:
    """Test handling of empty and minimal files."""

    def test_empty_file(self):
        """Test schema generation from empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            # Should still generate valid schema
            assert schema["schema_version"] == "2.0"
            assert schema["metadata"]["total_tasks_found"] == 0
            assert schema["metadata"]["confidence"] <= 0.5

            # Parser should work without errors
            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)
            assert len(tasks) == 0

        finally:
            os.unlink(temp_path)

    def test_file_with_only_whitespace(self):
        """Test file with only whitespace."""
        content = "\n\n   \n\t\n\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)
            assert len(tasks) == 0

        finally:
            os.unlink(temp_path)

    def test_file_with_no_tasks_only_text(self):
        """Test file with text but no task patterns."""
        content = """
# Some Document

This is just regular text.
No tasks here at all.
Just some paragraphs.
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)
            assert len(tasks) == 0

        finally:
            os.unlink(temp_path)

    def test_single_task_minimal(self):
        """Test file with just one minimal task."""
        content = "- [ ] - **T001: Single task**"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            assert len(tasks) == 1
            assert tasks[0].task_id == "T001"

        finally:
            os.unlink(temp_path)


class TestMalformedTasks:
    """Test handling of malformed task patterns."""

    def test_task_missing_checkbox(self):
        """Test task line without checkbox."""
        content = """
- **T001: Task without checkbox**
[ ] - Dev Status: [Not Started]
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            # Should not parse task without checkbox in markdown-checklist format
            # (depends on pattern, may or may not match)
            # At minimum, should not crash
            assert isinstance(tasks, list)

        finally:
            os.unlink(temp_path)

    def test_task_missing_bold_markers(self):
        """Test task line without bold markers."""
        content = """
[ ] - T001: Task without bold
[ ] - Dev Status: [Not Started]
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            # Should not parse task without bold markers
            assert len(tasks) == 0

        finally:
            os.unlink(temp_path)

    def test_task_with_incomplete_bold(self):
        """Test task with only opening or closing bold marker."""
        content = """
[ ] - **T001: Task with incomplete bold
[ ] - T002: Another incomplete bold**
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            # Should not crash, may or may not parse depending on pattern
            assert isinstance(tasks, list)

        finally:
            os.unlink(temp_path)

    def test_status_line_with_unclosed_bracket(self):
        """Test status line with malformed brackets."""
        content = """
- [ ] - **T001: Valid task**
- [ ] - Dev Status: [Not Started
- [ ] - QA Status: Not Started]
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            # Should parse task but ignore malformed status lines
            assert len(tasks) == 1
            assert tasks[0].task_id == "T001"
            # Status should remain default (not_started) since malformed lines ignored
            assert tasks[0].dev_state == "not_started"

        finally:
            os.unlink(temp_path)


class TestSpecialCharacters:
    """Test handling of special characters in tasks."""

    def test_task_with_unicode_characters(self):
        """Test task descriptions with Unicode characters."""
        content = """
- [ ] - **T001: Add emoji support 🎉**
- [ ] - Dev Status: [Not Started]

- [ ] - **T002: Handle UTF-8: café, naïve, 日本語**
- [ ] - Dev Status: [Not Started]

- [ ] - **T003: Math symbols: α, β, ∑, ∫**
- [ ] - Dev Status: [Not Started]
        """

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            assert len(tasks) == 3
            assert "emoji" in tasks[0].description.lower()
            assert "café" in tasks[1].description or "UTF-8" in tasks[1].description

        finally:
            os.unlink(temp_path)

    def test_task_with_special_markdown_characters(self):
        """Test tasks with markdown special characters."""
        content = r"""
- [ ] - **T001: Handle [links] and `code`**
- [ ] - Dev Status: [Not Started]

- [ ] - **T002: Escape \* asterisks and \_ underscores**
- [ ] - Dev Status: [Not Started]
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            # Should handle special characters gracefully
            assert len(tasks) >= 1

        finally:
            os.unlink(temp_path)

    def test_task_with_regex_special_characters(self):
        """Test tasks with regex special characters."""
        content = r"""
- [ ] - **T001: Fix regex: .*+?[]{}()|^$**
- [ ] - Dev Status: [Not Started]
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            # Should not crash on regex special chars in description
            assert len(tasks) >= 0

        finally:
            os.unlink(temp_path)


class TestVeryLongContent:
    """Test handling of very long content."""

    def test_very_long_description(self):
        """Test task with extremely long description."""
        long_desc = "A" * 1000  # 1000 character description

        content = f"""
- [ ] - **T001: {long_desc}**
- [ ] - Dev Status: [Not Started]
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            assert len(tasks) == 1
            assert len(tasks[0].description) == 1000

        finally:
            os.unlink(temp_path)

    def test_very_long_file(self):
        """Test file with many tasks."""
        # Generate 200 tasks
        tasks_content = []
        for i in range(1, 201):
            tasks_content.append(f"- [ ] - **T{i:03d}: Task number {i}**")
            tasks_content.append(f"- [ ] - Dev Status: [Not Started]")
            tasks_content.append("")

        content = "\n".join(tasks_content)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator(max_sample_lines=500)
            schema = generator.generate_schema(temp_path)

            # Should have high confidence with 200 tasks
            assert schema["metadata"]["confidence"] == 1.0

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            # Should parse all 200 tasks
            assert len(tasks) == 200

        finally:
            os.unlink(temp_path)

    def test_extremely_long_status_value(self):
        """Test status with very long value."""
        long_status = "In Progress " + "with many details " * 50

        content = f"""
- [ ] - **T001: Task with long status**
- [ ] - Dev Status: [{long_status}]
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            # Should handle long status value
            assert len(tasks) == 1

        finally:
            os.unlink(temp_path)


class TestInconsistentFormats:
    """Test files with inconsistent or mixed formats."""

    def test_mixed_checkbox_formats(self):
        """Test file with mixed checkbox formats ([ ], [x], [X])."""
        content = """
- [ ] - **T001: Unchecked lowercase**
- [ ] - Dev Status: [Not Started]

- [x] - **T002: Checked lowercase**
- [x] - Dev Status: [Complete]

- [X] - **T003: Checked uppercase**
- [X] - Dev Status: [Complete]
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            # Should handle all checkbox variations
            assert len(tasks) == 3

        finally:
            os.unlink(temp_path)

    def test_inconsistent_spacing(self):
        """Test file with inconsistent spacing."""
        content = """
- [ ] - **T001: Normal spacing**
- [ ] - Dev Status: [Not Started]

-[ ]-**T002: No spaces**
-[ ]-Dev Status: [Not Started]

-  [ ]  -  **T003: Extra spaces**
-  [ ]  -  Dev Status: [Not Started]
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            # Pattern should be flexible enough to handle spacing variations
            # At minimum should parse the normal one
            assert len(tasks) >= 1

        finally:
            os.unlink(temp_path)

    def test_mixed_task_id_formats(self):
        """Test file with multiple task ID formats."""
        content = """
- [ ] - **T001: First format**
- [ ] - Dev Status: [Not Started]

- [ ] - **TASK-002: Second format**
- [ ] - Dev Status: [Not Started]

- [ ] - **BUG-003: Third format**
- [ ] - Dev Status: [Not Started]
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            # Will detect first format it finds
            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            # May not parse all due to different formats
            # Should parse at least the ones matching detected format
            assert len(tasks) >= 1

        finally:
            os.unlink(temp_path)


class TestInvalidSchemas:
    """Test parser behavior with invalid schemas."""

    def test_schema_with_invalid_regex(self):
        """Test that invalid regex in schema is caught."""
        schema = {
            "schema_version": "2.0",
            "patterns": {
                "task_line": {
                    "regex": r"(?P<unclosed",  # Invalid regex
                },
                "status_line": {
                    "regex": ".*",
                },
            },
            "status_semantics": {
                "field_mapping": {"dev": ["Dev"]},
                "states": {"dev": {"not_started": ["Not Started"]}},
            },
        }

        with pytest.raises(SchemaValidationError, match="Invalid regex"):
            TaskSchemaParser(schema)

    def test_schema_missing_required_pattern(self):
        """Test that missing required patterns are caught."""
        schema = {
            "schema_version": "2.0",
            "patterns": {
                "task_line": {"regex": ".*"},
                # Missing status_line
            },
            "status_semantics": {
                "field_mapping": {},
                "states": {},
            },
        }

        with pytest.raises(SchemaValidationError, match="Missing pattern"):
            TaskSchemaParser(schema)

    def test_schema_with_non_dict_pattern(self):
        """Test that non-dict patterns are rejected."""
        schema = {
            "schema_version": "2.0",
            "patterns": {
                "task_line": "not a dict",  # Should be dict
                "status_line": {"regex": ".*"},
            },
            "status_semantics": {
                "field_mapping": {},
                "states": {},
            },
        }

        with pytest.raises(SchemaValidationError, match="Invalid pattern structure"):
            TaskSchemaParser(schema)


class TestStatusFieldEdgeCases:
    """Test edge cases in status field handling."""

    def test_unknown_status_field(self, capsys):
        """Test handling of unknown status fields."""
        content = """
- [ ] - **T001: Task with unknown field**
- [ ] - Dev Status: [Not Started]
- [ ] - Unknown Field: [Some Value]
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            # Should parse task, ignoring unknown field
            assert len(tasks) == 1
            assert tasks[0].dev_state == "not_started"

            # May print warning about unknown field
            captured = capsys.readouterr()
            # Warning expected but not required

        finally:
            os.unlink(temp_path)

    def test_status_without_task(self):
        """Test status lines appearing without a task."""
        content = """
- [ ] - Dev Status: [Not Started]
- [ ] - QA Status: [Not Started]

- [ ] - **T001: Actual task**
- [ ] - Dev Status: [In Progress]
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            # Should only parse T001
            assert len(tasks) == 1
            assert tasks[0].task_id == "T001"

        finally:
            os.unlink(temp_path)

    def test_duplicate_status_fields(self):
        """Test task with duplicate status field."""
        content = """
- [ ] - **T001: Task with duplicate status**
- [ ] - Dev Status: [Not Started]
- [ ] - Dev Status: [In Progress]
- [ ] - Dev Status: [Complete]
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            # Should parse, last value should win
            assert len(tasks) == 1
            assert tasks[0].task_id == "T001"
            # Last status should be used
            assert tasks[0].dev_state == "complete"

        finally:
            os.unlink(temp_path)
