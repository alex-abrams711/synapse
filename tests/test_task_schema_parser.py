"""Unit tests for TaskSchemaParser."""
import pytest
import tempfile
import os
from synapse_cli.parsers import (
    TaskSchemaParser,
    SchemaValidationError,
)


class TestSchemaValidation:
    """Test schema validation."""

    def test_valid_v2_schema(self):
        """Test that a valid v2 schema passes validation."""
        schema = {
            "schema_version": "2.0",
            "format_type": "markdown-checklist",
            "patterns": {
                "task_line": {
                    "regex": r"^\[ \] - \*\*(?P<task_id>T\d+):\s*(?P<description>.*?)\*\*",
                    "groups": ["task_id", "description"],
                },
                "status_line": {
                    "regex": r"^\[ \] - (?P<field>Dev) Status: \[(?P<status>.*?)\]",
                    "groups": ["field", "status"],
                },
            },
            "status_semantics": {
                "fields": ["dev"],
                "field_mapping": {"dev": ["Dev Status"]},
                "states": {
                    "dev": {
                        "not_started": ["Not Started"],
                        "complete": ["Complete"],
                    }
                },
            },
        }

        # Should not raise
        parser = TaskSchemaParser(schema)
        assert parser.schema["schema_version"] == "2.0"

    def test_missing_schema_version(self):
        """Test that missing schema_version is rejected."""
        schema = {
            "patterns": {},
            "status_semantics": {},
        }

        with pytest.raises(SchemaValidationError, match="Unsupported schema version"):
            TaskSchemaParser(schema)

    def test_unsupported_schema_version(self):
        """Test that unsupported versions are rejected."""
        schema = {
            "schema_version": "3.0",
            "patterns": {},
            "status_semantics": {},
        }

        with pytest.raises(SchemaValidationError, match="Unsupported schema version"):
            TaskSchemaParser(schema)

    def test_missing_patterns(self):
        """Test that missing patterns object is rejected."""
        schema = {
            "schema_version": "2.0",
            "status_semantics": {},
        }

        with pytest.raises(
            SchemaValidationError, match="Schema missing required key: patterns"
        ):
            TaskSchemaParser(schema)

    def test_missing_status_semantics(self):
        """Test that missing status_semantics is rejected."""
        schema = {
            "schema_version": "2.0",
            "patterns": {
                "task_line": {"regex": ".*"},
                "status_line": {"regex": ".*"},
            },
        }

        with pytest.raises(
            SchemaValidationError, match="Schema missing required key: status_semantics"
        ):
            TaskSchemaParser(schema)

    def test_missing_required_pattern(self):
        """Test that missing required patterns are rejected."""
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

        with pytest.raises(SchemaValidationError, match="Missing pattern: status_line"):
            TaskSchemaParser(schema)

    def test_invalid_regex(self):
        """Test that invalid regex patterns are rejected."""
        schema = {
            "schema_version": "2.0",
            "patterns": {
                "task_line": {
                    "regex": r"(?P<invalid",  # Unclosed group
                },
                "status_line": {"regex": ".*"},
            },
            "status_semantics": {
                "field_mapping": {},
                "states": {},
            },
        }

        with pytest.raises(SchemaValidationError, match="Invalid regex"):
            TaskSchemaParser(schema)

    def test_pattern_not_dict(self):
        """Test that non-dict pattern values are rejected."""
        schema = {
            "schema_version": "2.0",
            "patterns": {
                "task_line": "not a dict",
                "status_line": {"regex": ".*"},
            },
            "status_semantics": {
                "field_mapping": {},
                "states": {},
            },
        }

        with pytest.raises(
            SchemaValidationError, match="Invalid pattern structure"
        ):
            TaskSchemaParser(schema)

    def test_missing_field_mapping(self):
        """Test that missing field_mapping is rejected."""
        schema = {
            "schema_version": "2.0",
            "patterns": {
                "task_line": {"regex": ".*"},
                "status_line": {"regex": ".*"},
            },
            "status_semantics": {
                "states": {},
            },
        }

        with pytest.raises(
            SchemaValidationError, match="status_semantics missing 'field_mapping'"
        ):
            TaskSchemaParser(schema)

    def test_missing_states(self):
        """Test that missing states is rejected."""
        schema = {
            "schema_version": "2.0",
            "patterns": {
                "task_line": {"regex": ".*"},
                "status_line": {"regex": ".*"},
            },
            "status_semantics": {
                "field_mapping": {},
            },
        }

        with pytest.raises(
            SchemaValidationError, match="status_semantics missing 'states'"
        ):
            TaskSchemaParser(schema)

    def test_default_schema_is_valid(self):
        """Test that the default schema passes validation."""
        parser = TaskSchemaParser()  # Uses default schema
        assert parser.schema["schema_version"] == "2.0"


class TestTaskLineParsing:
    """Test task line parsing."""

    @pytest.fixture
    def parser(self):
        """Create parser with default schema."""
        return TaskSchemaParser()

    def test_parse_valid_task_line(self, parser):
        """Test parsing a valid task line."""
        line = "[ ] - **T001: Create database schema**"
        result = parser.parse_task_line(line)

        assert result is not None
        assert result["task_id"] == "T001"
        assert result["description"] == "Create database schema"

    def test_parse_task_line_with_checkbox_x(self, parser):
        """Test parsing task line with checked checkbox."""
        line = "[X] - **T002: Add API endpoints**"
        result = parser.parse_task_line(line)

        assert result is not None
        assert result["task_id"] == "T002"
        assert result["description"] == "Add API endpoints"

    def test_parse_task_line_lowercase_x(self, parser):
        """Test parsing task line with lowercase x."""
        line = "[x] - **T003: Write tests**"
        result = parser.parse_task_line(line)

        assert result is not None
        assert result["task_id"] == "T003"

    def test_parse_invalid_task_line(self, parser):
        """Test that invalid lines return None."""
        line = "This is not a task line"
        result = parser.parse_task_line(line)

        assert result is None

    def test_parse_task_line_missing_bold(self, parser):
        """Test that lines without bold markers are not matched."""
        line = "[ ] - T004: No bold markers"
        result = parser.parse_task_line(line)

        assert result is None

    def test_parse_task_line_complex_description(self, parser):
        """Test parsing task with complex description."""
        line = "[ ] - **T005: Implement user authentication & authorization**"
        result = parser.parse_task_line(line)

        assert result is not None
        assert result["task_id"] == "T005"
        assert "authentication" in result["description"]


class TestStatusLineParsing:
    """Test status line parsing."""

    @pytest.fixture
    def parser(self):
        """Create parser with default schema."""
        return TaskSchemaParser()

    def test_parse_valid_status_line(self, parser):
        """Test parsing a valid status line."""
        line = "[ ] - Dev Status: [Not Started]"
        result = parser.parse_status_line(line)

        assert result is not None
        assert result["field"] == "dev"
        assert result["state"] == "not_started"
        assert result["raw_field"] == "Dev"  # Default regex captures "Dev" not "Dev Status"
        assert result["raw_status"] == "Not Started"

    def test_parse_status_line_in_progress(self, parser):
        """Test parsing in progress status."""
        line = "[ ] - Dev Status: [In Progress]"
        result = parser.parse_status_line(line)

        assert result is not None
        assert result["state"] == "in_progress"

    def test_parse_status_line_complete(self, parser):
        """Test parsing complete status."""
        line = "[X] - Dev Status: [Complete]"
        result = parser.parse_status_line(line)

        assert result is not None
        assert result["state"] == "complete"

    def test_parse_qa_status_line(self, parser):
        """Test parsing QA status line."""
        line = "[ ] - QA Status: [Not Started]"
        result = parser.parse_status_line(line)

        assert result is not None
        assert result["field"] == "qa"

    def test_parse_user_verification_status(self, parser):
        """Test parsing user verification status."""
        line = "[ ] - User Verification Status: [Not Started]"
        result = parser.parse_status_line(line)

        assert result is not None
        assert result["field"] == "user_verification"

    def test_parse_invalid_status_line(self, parser):
        """Test that invalid lines return None."""
        line = "This is not a status line"
        result = parser.parse_status_line(line)

        assert result is None


class TestStatusNormalization:
    """Test status value normalization."""

    @pytest.fixture
    def parser(self):
        """Create parser with extended schema."""
        schema = {
            "schema_version": "2.0",
            "patterns": {
                "task_line": {"regex": ".*"},
                "status_line": {
                    "regex": r"(?P<field>.*?): \[(?P<status>.*?)\]",
                },
            },
            "status_semantics": {
                "field_mapping": {
                    "dev": ["Dev Status", "Dev", "Development Status"],
                },
                "states": {
                    "dev": {
                        "not_started": ["Not Started", "Pending", "Todo"],
                        "in_progress": ["In Progress", "Working", "Active"],
                        "complete": ["Complete", "Done", "Finished"],
                    },
                },
            },
        }
        return TaskSchemaParser(schema)

    def test_normalize_field_variations(self, parser):
        """Test that field name variations are normalized."""
        assert parser._normalize_field("Dev Status") == "dev"
        assert parser._normalize_field("Dev") == "dev"
        assert parser._normalize_field("Development Status") == "dev"

    def test_normalize_unknown_field(self, parser):
        """Test that unknown fields return None."""
        assert parser._normalize_field("Unknown Status") is None

    def test_normalize_status_variations(self, parser):
        """Test that status value variations are normalized."""
        assert parser._normalize_status("dev", "Not Started") == "not_started"
        assert parser._normalize_status("dev", "Pending") == "not_started"
        assert parser._normalize_status("dev", "Todo") == "not_started"

        assert parser._normalize_status("dev", "In Progress") == "in_progress"
        assert parser._normalize_status("dev", "Working") == "in_progress"

        assert parser._normalize_status("dev", "Complete") == "complete"
        assert parser._normalize_status("dev", "Done") == "complete"
        assert parser._normalize_status("dev", "Finished") == "complete"

    def test_normalize_unknown_status(self, parser, capsys):
        """Test that unknown status values default to not_started."""
        result = parser._normalize_status("dev", "Unknown")
        assert result == "not_started"

        # Check warning was printed
        captured = capsys.readouterr()
        assert "Unknown status 'Unknown'" in captured.err


class TestGetCanonicalStatus:
    """Test getting canonical status strings."""

    @pytest.fixture
    def parser(self):
        """Create parser with default schema."""
        return TaskSchemaParser()

    def test_get_canonical_status(self, parser):
        """Test getting canonical status for each state."""
        assert parser.get_canonical_status("dev", "not_started") == "Not Started"
        assert parser.get_canonical_status("dev", "in_progress") == "In Progress"
        assert parser.get_canonical_status("dev", "complete") == "Complete"


class TestKeywordExtraction:
    """Test keyword extraction from descriptions."""

    @pytest.fixture
    def parser(self):
        """Create parser with default schema."""
        return TaskSchemaParser()

    def test_extract_keywords_basic(self, parser):
        """Test basic keyword extraction."""
        keywords = parser._extract_keywords("Create database schema")
        assert "create" in keywords
        assert "database" in keywords
        assert "schema" in keywords

    def test_extract_keywords_removes_stop_words(self, parser):
        """Test that stop words are removed."""
        keywords = parser._extract_keywords("Add the user authentication for the app")
        assert "the" not in keywords
        assert "for" not in keywords
        assert "user" in keywords
        assert "authentication" in keywords

    def test_extract_keywords_removes_short_words(self, parser):
        """Test that short words (<3 chars) are removed."""
        keywords = parser._extract_keywords("Add UI to app")
        assert "ui" not in keywords
        assert "to" not in keywords
        assert "add" in keywords
        assert "app" in keywords

    def test_extract_keywords_limits_to_ten(self, parser):
        """Test that keyword list is limited to 10."""
        long_desc = " ".join([f"word{i}" for i in range(20)])
        keywords = parser._extract_keywords(long_desc)
        assert len(keywords) <= 10


class TestFullFileParsing:
    """Test parsing complete task files."""

    @pytest.fixture
    def parser(self):
        """Create parser with default schema."""
        return TaskSchemaParser()

    def test_parse_simple_tasks_file(self, parser):
        """Test parsing a simple tasks file."""
        content = """
# Tasks

[ ] - **T001: Create database schema**
[ ] - Dev Status: [Not Started]
[ ] - QA Status: [Not Started]

[ ] - **T002: Add API endpoints**
[ ] - Dev Status: [In Progress]
[ ] - QA Status: [Not Started]

[X] - **T003: Write tests**
[X] - Dev Status: [Complete]
[X] - QA Status: [Complete]
[X] - User Verification Status: [Complete]
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            tasks = parser.parse_tasks_file(temp_path)

            assert len(tasks) == 3

            # Task 1
            assert tasks[0].task_id == "T001"
            assert tasks[0].dev_state == "not_started"
            assert tasks[0].qa_state == "not_started"
            assert tasks[0].uv_state == "not_started"

            # Task 2
            assert tasks[1].task_id == "T002"
            assert tasks[1].dev_state == "in_progress"
            assert tasks[1].qa_state == "not_started"

            # Task 3
            assert tasks[2].task_id == "T003"
            assert tasks[2].dev_state == "complete"
            assert tasks[2].qa_state == "complete"
            assert tasks[2].uv_state == "complete"

        finally:
            os.unlink(temp_path)

    def test_parse_file_with_no_tasks(self, parser):
        """Test parsing file with no tasks."""
        content = """
# Just a markdown file

Some text without tasks.
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            tasks = parser.parse_tasks_file(temp_path)
            assert len(tasks) == 0

        finally:
            os.unlink(temp_path)

    def test_parse_file_preserves_line_numbers(self, parser):
        """Test that line numbers are correctly recorded."""
        content = """# Tasks

Some intro text

[ ] - **T001: First task**
[ ] - Dev Status: [Not Started]

More text

[ ] - **T002: Second task**
[ ] - Dev Status: [Not Started]
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            tasks = parser.parse_tasks_file(temp_path)

            assert len(tasks) == 2
            assert tasks[0].line_number == 5  # T001 on line 5
            assert tasks[1].line_number == 10  # T002 on line 10

        finally:
            os.unlink(temp_path)

    def test_parse_file_extracts_keywords(self, parser):
        """Test that keywords are extracted from descriptions."""
        content = """
[ ] - **T001: Create user authentication system**
[ ] - Dev Status: [Not Started]
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            tasks = parser.parse_tasks_file(temp_path)

            assert len(tasks) == 1
            keywords = tasks[0].keywords
            assert "create" in keywords
            assert "user" in keywords
            assert "authentication" in keywords
            assert "system" in keywords

        finally:
            os.unlink(temp_path)
