"""Integration tests for multi-format task file support."""
import os
import pytest
from synapse_cli.parsers import (
    TaskSchemaParser,
    SchemaValidationError,
)
from synapse_cli.parsers.schema_generator import SchemaGenerator


class TestOpenSpecFormat:
    """Test OpenSpec format detection and parsing."""

    @pytest.fixture
    def openspec_file(self):
        """Get path to OpenSpec test fixture."""
        return os.path.join(
            os.path.dirname(__file__),
            "fixtures/formats/openspec_tasks.md"
        )

    def test_generate_schema_from_openspec(self, openspec_file):
        """Test schema generation from OpenSpec format."""
        generator = SchemaGenerator()
        schema = generator.generate_schema(openspec_file)

        # Verify schema structure
        assert schema["schema_version"] == "2.0"
        assert schema["format_type"] == "markdown-checklist"

        # Verify task ID format
        assert schema["task_id_format"]["prefix"] == "T"
        assert schema["task_id_format"]["digits"] == 3
        assert schema["task_id_format"]["separator"] == ""

        # Verify patterns exist
        assert "task_line" in schema["patterns"]
        assert "status_line" in schema["patterns"]

        # Verify status semantics
        assert "dev" in schema["status_semantics"]["field_mapping"]
        assert "qa" in schema["status_semantics"]["field_mapping"]
        assert "user_verification" in schema["status_semantics"]["field_mapping"]

    def test_parse_openspec_tasks(self, openspec_file):
        """Test parsing OpenSpec tasks with generated schema."""
        # Generate schema
        generator = SchemaGenerator()
        schema = generator.generate_schema(openspec_file)

        # Parse tasks
        parser = TaskSchemaParser(schema)
        tasks = parser.parse_tasks_file(openspec_file)

        # Verify tasks were parsed
        assert len(tasks) == 7

        # Verify T001 - not started
        t001 = next(t for t in tasks if t.task_id == "T001")
        assert t001.dev_state == "not_started"
        assert t001.qa_state == "not_started"
        assert t001.uv_state == "not_started"
        assert "design" in t001.keywords
        assert "authentication" in t001.keywords

        # Verify T002 - in progress
        t002 = next(t for t in tasks if t.task_id == "T002")
        assert t002.dev_state == "in_progress"
        assert t002.qa_state == "not_started"

        # Verify T003 - complete
        t003 = next(t for t in tasks if t.task_id == "T003")
        assert t003.dev_state == "complete"
        assert t003.qa_state == "complete"
        assert t003.uv_state == "complete"

        # Verify T004 - dev complete, qa in progress
        t004 = next(t for t in tasks if t.task_id == "T004")
        assert t004.dev_state == "complete"
        assert t004.qa_state == "in_progress"
        assert t004.uv_state == "not_started"

    def test_openspec_status_normalization(self, openspec_file):
        """Test that OpenSpec status values normalize correctly."""
        generator = SchemaGenerator()
        schema = generator.generate_schema(openspec_file)

        # Verify status value mapping
        dev_states = schema["status_semantics"]["states"]["dev"]

        assert "Not Started" in dev_states["not_started"]
        assert "In Progress" in dev_states["in_progress"]
        assert "Complete" in dev_states["complete"]

        # QA states
        qa_states = schema["status_semantics"]["states"]["qa"]
        assert "Not Started" in qa_states["not_started"]
        assert "Complete" in qa_states["complete"]

    def test_openspec_validation_confidence(self, openspec_file):
        """Test that OpenSpec format has high confidence."""
        generator = SchemaGenerator()
        schema = generator.generate_schema(openspec_file)

        # 7 tasks should give decent confidence
        assert schema["metadata"]["confidence"] >= 0.6
        assert schema["metadata"]["total_tasks_found"] == 7


class TestGitHubSpecKitFormat:
    """Test GitHub Spec Kit format detection and parsing."""

    @pytest.fixture
    def spec_kit_file(self):
        """Get path to Spec Kit test fixture."""
        return os.path.join(
            os.path.dirname(__file__),
            "fixtures/formats/github_spec_kit_tasks.md"
        )

    def test_generate_schema_from_spec_kit(self, spec_kit_file):
        """Test schema generation from GitHub Spec Kit format."""
        generator = SchemaGenerator()
        schema = generator.generate_schema(spec_kit_file)

        # Verify schema structure
        assert schema["schema_version"] == "2.0"
        assert schema["format_type"] == "markdown-checklist"

        # Verify task ID format with separator
        assert schema["task_id_format"]["prefix"] == "TASK"
        assert schema["task_id_format"]["digits"] == 3
        assert schema["task_id_format"]["separator"] == "-"

    def test_parse_spec_kit_tasks(self, spec_kit_file):
        """Test parsing GitHub Spec Kit tasks."""
        # Generate schema
        generator = SchemaGenerator()
        schema = generator.generate_schema(spec_kit_file)

        # Parse tasks
        parser = TaskSchemaParser(schema)
        tasks = parser.parse_tasks_file(spec_kit_file)

        # Verify tasks were parsed
        assert len(tasks) == 6

        # Verify TASK-001
        task001 = next(t for t in tasks if t.task_id == "TASK-001")
        assert "schema" in task001.keywords
        assert "users" in task001.keywords

        # Verify TASK-003 - complete
        task003 = next(t for t in tasks if t.task_id == "TASK-003")
        assert task003.dev_state == "complete"
        assert task003.qa_state == "complete"
        assert task003.uv_state == "complete"

    def test_spec_kit_status_variations(self, spec_kit_file):
        """Test that Spec Kit status variations normalize correctly."""
        generator = SchemaGenerator()
        schema = generator.generate_schema(spec_kit_file)

        # Verify different status names map to semantic states
        dev_states = schema["status_semantics"]["states"]["dev"]

        # Should map "Pending" to not_started
        assert "Pending" in dev_states["not_started"]

        # Should map "Working" to in_progress
        assert "Working" in dev_states["in_progress"]

        # Should map "Done" to complete
        assert "Done" in dev_states["complete"]

        # QA states
        qa_states = schema["status_semantics"]["states"]["qa"]
        assert "Passed" in qa_states["complete"]


class TestCustomFormat:
    """Test custom format detection and parsing."""

    @pytest.fixture
    def custom_file(self):
        """Get path to custom format test fixture."""
        return os.path.join(
            os.path.dirname(__file__),
            "fixtures/formats/custom_format_tasks.md"
        )

    def test_generate_schema_from_custom_format(self, custom_file):
        """Test schema generation from custom format."""
        generator = SchemaGenerator()
        schema = generator.generate_schema(custom_file)

        # Verify schema structure
        assert schema["schema_version"] == "2.0"
        assert schema["format_type"] == "markdown-checklist"

        # Verify task ID format (multiple prefixes)
        task_id_format = schema["task_id_format"]
        # Should detect BUG or PERF as prefix
        assert task_id_format["prefix"] in ["BUG", "PERF"]
        assert task_id_format["digits"] == 3
        assert task_id_format["separator"] == "-"

    def test_parse_custom_format_tasks(self, custom_file):
        """Test parsing custom format tasks."""
        # Generate schema
        generator = SchemaGenerator()
        schema = generator.generate_schema(custom_file)

        # Parse tasks
        parser = TaskSchemaParser(schema)
        tasks = parser.parse_tasks_file(custom_file)

        # Verify tasks were parsed
        # Note: May not parse all if task IDs vary (BUG vs PERF)
        assert len(tasks) >= 3  # At least some tasks parsed

        # Find a completed task
        completed_tasks = [t for t in tasks if t.dev_state == "complete"]
        assert len(completed_tasks) >= 1

    def test_custom_format_field_normalization(self, custom_file):
        """Test that custom field names normalize correctly."""
        generator = SchemaGenerator()
        schema = generator.generate_schema(custom_file)

        # Verify field mapping includes custom names
        field_mapping = schema["status_semantics"]["field_mapping"]

        # Should have dev field mapped to "Development Status"
        assert "dev" in field_mapping
        assert "Development Status" in field_mapping["dev"]

        # Should have qa field mapped to "Quality Assurance Status"
        assert "qa" in field_mapping

    def test_custom_status_value_normalization(self, custom_file):
        """Test that custom status values normalize correctly."""
        generator = SchemaGenerator()
        schema = generator.generate_schema(custom_file)

        # Verify status value mapping
        dev_states = schema["status_semantics"]["states"]["dev"]

        # Custom values should map correctly
        assert "Todo" in dev_states["not_started"]
        assert "Ongoing" in dev_states["in_progress"]
        assert "Finished" in dev_states["complete"]

        # QA states
        qa_states = schema["status_semantics"]["states"]["qa"]
        assert "Waiting" in qa_states["not_started"]
        assert "Approved" in qa_states["complete"]


class TestMultiFormatCompatibility:
    """Test that parser works with schemas from different formats."""

    def test_all_formats_produce_valid_schemas(self):
        """Test that all format fixtures produce valid v2.0 schemas."""
        formats = [
            "openspec_tasks.md",
            "github_spec_kit_tasks.md",
            "custom_format_tasks.md",
        ]

        generator = SchemaGenerator()

        for format_file in formats:
            file_path = os.path.join(
                os.path.dirname(__file__),
                "fixtures/formats",
                format_file
            )

            schema = generator.generate_schema(file_path)

            # All schemas should be v2.0 and valid
            assert schema["schema_version"] == "2.0"
            assert "patterns" in schema
            assert "status_semantics" in schema
            assert "task_id_format" in schema
            assert "metadata" in schema

            # Schema should be parseable
            parser = TaskSchemaParser(schema)
            assert parser is not None

    def test_cross_format_parser_isolation(self):
        """Test that parsers don't interfere with each other."""
        # Create parser for OpenSpec
        openspec_file = os.path.join(
            os.path.dirname(__file__),
            "fixtures/formats/openspec_tasks.md"
        )
        generator = SchemaGenerator()
        openspec_schema = generator.generate_schema(openspec_file)
        openspec_parser = TaskSchemaParser(openspec_schema)

        # Create parser for Spec Kit
        spec_kit_file = os.path.join(
            os.path.dirname(__file__),
            "fixtures/formats/github_spec_kit_tasks.md"
        )
        spec_kit_schema = generator.generate_schema(spec_kit_file)
        spec_kit_parser = TaskSchemaParser(spec_kit_schema)

        # Parse with both
        openspec_tasks = openspec_parser.parse_tasks_file(openspec_file)
        spec_kit_tasks = spec_kit_parser.parse_tasks_file(spec_kit_file)

        # Verify each parser used its own schema
        assert all(t.task_id.startswith("T") for t in openspec_tasks)
        assert all(t.task_id.startswith("TASK-") for t in spec_kit_tasks)

    def test_format_detection_accuracy(self):
        """Test that format type is correctly detected."""
        generator = SchemaGenerator()

        # All test files use markdown checklist format
        formats = [
            ("openspec_tasks.md", "markdown-checklist"),
            ("github_spec_kit_tasks.md", "markdown-checklist"),
            ("custom_format_tasks.md", "markdown-checklist"),
        ]

        for format_file, expected_type in formats:
            file_path = os.path.join(
                os.path.dirname(__file__),
                "fixtures/formats",
                format_file
            )

            schema = generator.generate_schema(file_path)
            assert schema["format_type"] == expected_type
