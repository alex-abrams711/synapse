"""Unit tests for SchemaGenerator."""
import pytest
import tempfile
import os
from synapse_cli.parsers import SchemaGenerator, SchemaValidator


class TestFormatDetection:
    """Test format type detection."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return SchemaGenerator()

    def test_detect_markdown_checklist(self, generator):
        """Test detection of markdown checklist format."""
        lines = [
            "# Tasks",
            "",
            "- [ ] - **T001: Task one**",
            "- [ ] - Dev Status: [Not Started]",
            "- [x] - **T002: Task two**",
            "- [x] - Dev Status: [Complete]",
        ]

        format_type = generator._detect_format_type(lines)
        assert format_type == "markdown-checklist"

    def test_detect_numbered_list(self, generator):
        """Test detection of numbered list format."""
        lines = [
            "# Tasks",
            "",
            "1. **T001: Task one**",
            "   - Dev Status: [Not Started]",
            "2. **T002: Task two**",
            "   - Dev Status: [Complete]",
        ]

        format_type = generator._detect_format_type(lines)
        assert format_type == "numbered-list"

    def test_detect_custom_format(self, generator):
        """Test detection of custom format."""
        lines = [
            "# Tasks",
            "",
            "T001: Task one",
            "Status: Not Started",
            "T002: Task two",
            "Status: Complete",
        ]

        format_type = generator._detect_format_type(lines)
        assert format_type == "custom"

    def test_empty_file_defaults_to_checklist(self, generator):
        """Test that empty files default to markdown-checklist."""
        lines = []
        format_type = generator._detect_format_type(lines)
        assert format_type == "markdown-checklist"


class TestTaskIdExtraction:
    """Test task ID extraction and analysis."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return SchemaGenerator()

    def test_extract_simple_task_ids(self, generator):
        """Test extracting simple T001 style IDs."""
        lines = [
            "- [ ] - **T001: First task**",
            "- [ ] - **T002: Second task**",
            "- [ ] - **T003: Third task**",
        ]

        task_ids = generator._extract_task_ids(lines)
        assert "T001" in task_ids
        assert "T002" in task_ids
        assert "T003" in task_ids

    def test_extract_task_ids_with_separator(self, generator):
        """Test extracting TASK-001 style IDs."""
        lines = [
            "- [ ] - **TASK-001: First task**",
            "- [ ] - **TASK-002: Second task**",
        ]

        task_ids = generator._extract_task_ids(lines)
        assert "TASK-001" in task_ids
        assert "TASK-002" in task_ids

    def test_extract_task_ids_from_headers(self, generator):
        """Test extracting IDs from markdown headers."""
        lines = [
            "# T001: First task",
            "## T002: Second task",
        ]

        task_ids = generator._extract_task_ids(lines)
        assert "T001" in task_ids
        assert "T002" in task_ids

    def test_analyze_task_id_format_simple(self, generator):
        """Test analyzing simple T001 format."""
        task_ids = ["T001", "T002", "T003"]
        fmt = generator._analyze_task_id_format(task_ids)

        assert fmt["prefix"] == "T"
        assert fmt["digits"] == 3
        assert fmt["pattern"] == r"T\d{3}"
        assert fmt["example"] == "T001"
        assert fmt["separator"] == ""

    def test_analyze_task_id_format_with_dash(self, generator):
        """Test analyzing TASK-001 format."""
        task_ids = ["TASK-001", "TASK-002"]
        fmt = generator._analyze_task_id_format(task_ids)

        assert fmt["prefix"] == "TASK"
        assert fmt["digits"] == 3
        assert fmt["pattern"] == r"TASK\-\d{3}"  # Properly escaped dash
        assert fmt["example"] == "TASK-001"
        assert fmt["separator"] == "-"

    def test_analyze_empty_task_ids(self, generator):
        """Test that empty task IDs return default format."""
        fmt = generator._analyze_task_id_format([])

        assert fmt["prefix"] == "T"
        assert fmt["digits"] == 3
        assert fmt["pattern"] == r"T\d{3}"


class TestStatusExtraction:
    """Test status field and value extraction."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return SchemaGenerator()

    def test_extract_status_lines(self, generator):
        """Test extracting status field/value pairs."""
        lines = [
            "- [ ] - Dev Status: [Not Started]",
            "- [ ] - QA Status: [Not Started]",
            "- [x] - Dev Status: [Complete]",
            "- [x] - User Verification Status: [Complete]",
        ]

        status_lines = generator._extract_status_lines(lines)

        assert ("Dev Status", "Not Started") in status_lines
        assert ("QA Status", "Not Started") in status_lines
        assert ("Dev Status", "Complete") in status_lines
        assert ("User Verification Status", "Complete") in status_lines

    def test_filter_non_status_fields(self, generator):
        """Test that non-status fields are filtered out."""
        lines = [
            "- [ ] - Priority: [High]",  # Not a status field
            "- [ ] - Dev Status: [Not Started]",  # Status field
        ]

        status_lines = generator._extract_status_lines(lines)

        # Priority should be filtered out
        assert not any(field == "Priority" for field, _ in status_lines)
        # Dev Status should be included
        assert any(field == "Dev Status" for field, _ in status_lines)

    def test_group_status_by_field(self, generator):
        """Test grouping status values by field."""
        status_lines = [
            ("Dev Status", "Not Started"),
            ("Dev Status", "In Progress"),
            ("Dev Status", "Complete"),
            ("QA Status", "Not Started"),
            ("QA Status", "Complete"),
        ]

        grouped = generator._group_status_by_field(status_lines)

        assert set(grouped["Dev Status"]) == {
            "Complete",
            "In Progress",
            "Not Started",
        }
        assert set(grouped["QA Status"]) == {"Complete", "Not Started"}


class TestFieldNormalization:
    """Test field name normalization."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return SchemaGenerator()

    def test_normalize_dev_fields(self, generator):
        """Test that dev field variations are normalized."""
        raw_fields = ["Dev Status", "Development Status", "Dev"]
        mapping = generator._normalize_field_mapping(raw_fields)

        assert "dev" in mapping
        assert "Dev Status" in mapping["dev"]
        assert "Development Status" in mapping["dev"]
        assert "Dev" in mapping["dev"]

    def test_normalize_qa_fields(self, generator):
        """Test that QA field variations are normalized."""
        raw_fields = ["QA Status", "Quality Assurance Status", "Testing Status"]
        mapping = generator._normalize_field_mapping(raw_fields)

        assert "qa" in mapping
        assert "QA Status" in mapping["qa"]
        assert "Quality Assurance Status" in mapping["qa"]

    def test_normalize_user_verification_fields(self, generator):
        """Test that user verification fields are normalized."""
        raw_fields = ["User Verification Status", "User Verification", "UV Status"]
        mapping = generator._normalize_field_mapping(raw_fields)

        assert "user_verification" in mapping
        assert "User Verification Status" in mapping["user_verification"]


class TestStateNormalization:
    """Test status value normalization."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return SchemaGenerator()

    def test_normalize_not_started_values(self, generator):
        """Test that not_started variations are recognized."""
        status_by_field = {
            "Dev Status": ["Not Started", "Pending", "Todo", "Waiting"]
        }
        field_mapping = {"dev": ["Dev Status"]}

        state_mapping = generator._normalize_state_mapping(
            status_by_field, field_mapping
        )

        assert "dev" in state_mapping
        assert set(state_mapping["dev"]["not_started"]) == {
            "Not Started",
            "Pending",
            "Todo",
            "Waiting",
        }

    def test_normalize_in_progress_values(self, generator):
        """Test that in_progress variations are recognized."""
        status_by_field = {
            "Dev Status": ["In Progress", "Working", "Active", "Ongoing"]
        }
        field_mapping = {"dev": ["Dev Status"]}

        state_mapping = generator._normalize_state_mapping(
            status_by_field, field_mapping
        )

        assert set(state_mapping["dev"]["in_progress"]) == {
            "In Progress",
            "Working",
            "Active",
            "Ongoing",
        }

    def test_normalize_complete_values(self, generator):
        """Test that complete variations are recognized."""
        status_by_field = {
            "Dev Status": ["Complete", "Done", "Finished", "Verified"]
        }
        field_mapping = {"dev": ["Dev Status"]}

        state_mapping = generator._normalize_state_mapping(
            status_by_field, field_mapping
        )

        assert set(state_mapping["dev"]["complete"]) == {
            "Complete",
            "Done",
            "Finished",
            "Verified",
        }

    def test_binary_field_no_in_progress(self, generator):
        """Test that binary fields don't have in_progress state."""
        status_by_field = {"User Verification Status": ["Not Started", "Complete"]}
        field_mapping = {"user_verification": ["User Verification Status"]}

        state_mapping = generator._normalize_state_mapping(
            status_by_field, field_mapping
        )

        assert "in_progress" not in state_mapping["user_verification"]
        assert "not_started" in state_mapping["user_verification"]
        assert "complete" in state_mapping["user_verification"]


class TestSchemaGeneration:
    """Test complete schema generation."""

    def test_generate_schema_from_simple_file(self):
        """Test generating schema from a simple tasks file."""
        content = """# Tasks

- [ ] - **T001: Create database schema**
- [ ] - Dev Status: [Not Started]
- [ ] - QA Status: [Not Started]

- [ ] - **T002: Add API endpoints**
- [ ] - Dev Status: [In Progress]
- [ ] - QA Status: [Not Started]

- [X] - **T003: Write tests**
- [X] - Dev Status: [Complete]
- [X] - QA Status: [Complete]
- [X] - User Verification Status: [Complete]
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            # Verify schema structure
            assert schema["schema_version"] == "2.0"
            assert schema["format_type"] == "markdown-checklist"

            # Verify patterns exist
            assert "task_line" in schema["patterns"]
            assert "status_line" in schema["patterns"]

            # Verify task ID format
            assert schema["task_id_format"]["prefix"] == "T"
            assert schema["task_id_format"]["digits"] == 3

            # Verify status semantics
            assert "dev" in schema["status_semantics"]["fields"]
            assert "qa" in schema["status_semantics"]["fields"]
            assert "user_verification" in schema["status_semantics"]["fields"]

            # Verify metadata
            assert schema["metadata"]["total_tasks_found"] == 3
            assert schema["metadata"]["confidence"] >= 0.5

        finally:
            os.unlink(temp_path)


class TestSchemaValidation:
    """Test schema validation."""

    def test_validate_good_schema(self):
        """Test validating a schema that works well."""
        content = """# Tasks

- [ ] - **T001: Create database schema**
- [ ] - Dev Status: [Not Started]

- [ ] - **T002: Add API endpoints**
- [ ] - Dev Status: [In Progress]

- [X] - **T003: Write tests**
- [X] - Dev Status: [Complete]
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            # Generate schema
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            # Validate schema (use lower threshold for testing)
            validator = SchemaValidator()
            validator.MIN_SAMPLE_SIZE = 3  # Lower threshold for testing
            result = validator.validate_schema(schema, temp_path, expected_task_count=3)

            assert result.passed
            assert result.match_rate >= 0.95
            assert result.tasks_matched == 3

        finally:
            os.unlink(temp_path)

    def test_validate_adds_metadata(self):
        """Test that validation adds metadata to schema."""
        content = """# Tasks

- [ ] - **T001: Task one**
- [ ] - Dev Status: [Not Started]

- [ ] - **T002: Task two**
- [ ] - Dev Status: [Not Started]
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            validator = SchemaValidator()
            result = validator.validate_schema(schema, temp_path)

            # Add validation metadata
            updated_schema = validator.add_validation_metadata(schema, result)

            assert "validation" in updated_schema
            assert "pattern_match_rate" in updated_schema["validation"]
            assert "validation_passed" in updated_schema["validation"]

        finally:
            os.unlink(temp_path)


class TestConfidenceCalculation:
    """Test confidence score calculation."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return SchemaGenerator()

    def test_high_confidence_many_tasks(self, generator):
        """Test that many tasks give high confidence."""
        confidence = generator._calculate_confidence(50, 200)
        assert confidence == 1.0

    def test_medium_confidence_some_tasks(self, generator):
        """Test that some tasks give medium confidence."""
        confidence = generator._calculate_confidence(20, 100)
        assert 0.7 <= confidence < 1.0

    def test_low_confidence_few_tasks(self, generator):
        """Test that few tasks give low confidence."""
        confidence = generator._calculate_confidence(3, 50)
        assert confidence <= 0.6
