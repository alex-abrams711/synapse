"""Integration tests for end-to-end sense → hook workflow."""
import json
import os
import tempfile
import pytest
from synapse_cli.parsers import TaskSchemaParser
from synapse_cli.parsers.schema_generator import SchemaGenerator


class TestSenseToParserWorkflow:
    """Test complete workflow from schema generation to parsing."""

    def test_generate_and_parse_workflow(self):
        """Test that generated schema can be used to parse the same file."""
        # Create test tasks file
        content = """
# Project Tasks

- [ ] - **T001: Implement user authentication**
- [ ] - Dev Status: [Not Started]
- [ ] - QA Status: [Not Started]

- [ ] - **T002: Create API endpoints**
- [ ] - Dev Status: [In Progress]
- [ ] - QA Status: [Not Started]

- [x] - **T003: Setup database schema**
- [x] - Dev Status: [Complete]
- [x] - QA Status: [Complete]
- [x] - User Verification Status: [Complete]
        """

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            # Step 1: Generate schema (simulates sense command)
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            # Verify schema is valid
            assert schema["schema_version"] == "2.0"
            assert "patterns" in schema
            assert "status_semantics" in schema

            # Step 2: Parse tasks using generated schema (simulates hooks)
            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            # Verify parsing succeeded
            assert len(tasks) == 3

            # Verify task states are correct
            t001 = next(t for t in tasks if t.task_id == "T001")
            assert t001.dev_state == "not_started"
            assert t001.qa_state == "not_started"

            t002 = next(t for t in tasks if t.task_id == "T002")
            assert t002.dev_state == "in_progress"

            t003 = next(t for t in tasks if t.task_id == "T003")
            assert t003.dev_state == "complete"
            assert t003.qa_state == "complete"
            assert t003.uv_state == "complete"

        finally:
            os.unlink(temp_path)

    def test_schema_reuse_across_sessions(self):
        """Test that saved schema can be loaded and reused."""
        # Create test tasks file
        content = """
- [ ] - **T001: Task one**
- [ ] - Dev Status: [Not Started]

- [ ] - **T002: Task two**
- [ ] - Dev Status: [In Progress]
        """

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(content)
            tasks_path = f.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            schema_path = f.name

        try:
            # Session 1: Generate and save schema
            generator = SchemaGenerator()
            schema = generator.generate_schema(tasks_path)

            with open(schema_path, "w", encoding="utf-8") as f:
                json.dump(schema, f)

            # Session 2: Load schema and parse
            with open(schema_path, encoding="utf-8") as f:
                loaded_schema = json.load(f)

            parser = TaskSchemaParser(loaded_schema)
            tasks = parser.parse_tasks_file(tasks_path)

            assert len(tasks) == 2

        finally:
            os.unlink(tasks_path)
            os.unlink(schema_path)

    def test_schema_validation_before_use(self):
        """Test that invalid schemas are rejected before parsing."""
        # Create malformed schema
        bad_schema = {
            "schema_version": "2.0",
            "patterns": {
                "task_line": {"regex": "(?P<unclosed"},  # Invalid regex
                "status_line": {"regex": ".*"},
            },
            "status_semantics": {
                "field_mapping": {},
                "states": {},
            },
        }

        # Should raise validation error
        from synapse_cli.parsers import SchemaValidationError

        with pytest.raises(SchemaValidationError):
            TaskSchemaParser(bad_schema)


class TestSchemaEvolution:
    """Test schema evolution and compatibility."""

    def test_schema_with_added_tasks(self):
        """Test that schema works when new tasks are added to file."""
        # Create initial tasks file
        initial_content = """
- [ ] - **T001: Task one**
- [ ] - Dev Status: [Not Started]

- [ ] - **T002: Task two**
- [ ] - Dev Status: [Not Started]
        """

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(initial_content)
            temp_path = f.name

        try:
            # Generate schema from initial file
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            # Add more tasks to file
            updated_content = initial_content + """
- [ ] - **T003: Task three**
- [ ] - Dev Status: [In Progress]

- [ ] - **T004: Task four**
- [ ] - Dev Status: [Complete]
            """

            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

            # Parse with original schema
            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            # Should parse all 4 tasks
            assert len(tasks) == 4

        finally:
            os.unlink(temp_path)

    def test_schema_with_new_status_values(self):
        """Test handling of new status values not in original schema."""
        content = """
- [ ] - **T001: Task with new status**
- [ ] - Dev Status: [Implementing]
        """

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            # New status "Implementing" should be normalized
            assert len(tasks) == 1
            # Should map to in_progress based on keyword "implementing"
            assert tasks[0].dev_state == "in_progress"

        finally:
            os.unlink(temp_path)


class TestHookSimulation:
    """Simulate hook behavior with generated schemas."""

    def test_pre_tool_use_blocking_logic(self):
        """Test blocking logic that would run in pre-tool-use hook."""
        content = """
- [ ] - **T001: First task**
- [ ] - Dev Status: [In Progress]
- [ ] - QA Status: [Not Started]

- [ ] - **T002: Second task**
- [ ] - Dev Status: [Not Started]
- [ ] - QA Status: [Not Started]

- [x] - **T003: Third task**
- [x] - Dev Status: [Complete]
- [x] - QA Status: [In Progress]
        """

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            # Check for blocking conditions
            in_progress_tasks = [
                t.task_id for t in tasks if t.dev_state == "in_progress"
            ]
            awaiting_qa = [
                t.task_id
                for t in tasks
                if t.dev_state == "complete"
                and (t.qa_state != "complete" or t.uv_state != "complete")
            ]

            # Should block starting new work
            assert len(in_progress_tasks) > 0 or len(awaiting_qa) > 0

            # T001 is in progress
            assert "T001" in in_progress_tasks

            # T003 is awaiting QA completion
            assert "T003" in awaiting_qa

        finally:
            os.unlink(temp_path)

    def test_post_tool_use_quality_gates(self):
        """Test quality gate logic that would run in post-tool-use hook."""
        content = """
- [x] - **T001: Completed task**
- [x] - Dev Status: [Complete]
- [ ] - QA Status: [Not Started]
- [ ] - User Verification Status: [Not Started]
        """

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            t001 = tasks[0]

            # Quality gate: Dev complete but QA not started
            assert t001.dev_state == "complete"
            assert t001.qa_state == "not_started"
            assert t001.uv_state == "not_started"

            # Hook should block further work on this task
            needs_qa = t001.dev_state == "complete" and t001.qa_state != "complete"
            assert needs_qa

        finally:
            os.unlink(temp_path)


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_large_project_parsing(self):
        """Test parsing a large project with many tasks."""
        # Generate 100 tasks
        tasks_content = []
        for i in range(1, 101):
            state = "Not Started" if i % 3 == 0 else "In Progress" if i % 3 == 1 else "Complete"
            tasks_content.append(f"- [ ] - **T{i:03d}: Task number {i}**")
            tasks_content.append(f"- [ ] - Dev Status: [{state}]")
            tasks_content.append("")

        content = "\n".join(tasks_content)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            # Should parse all 100 tasks
            assert len(tasks) == 100

            # Check confidence is high
            assert schema["metadata"]["confidence"] >= 0.9

        finally:
            os.unlink(temp_path)

    def test_monorepo_multiple_features(self):
        """Test parsing tasks organized by features."""
        content = """
## Feature: Authentication

- [ ] - **T001: JWT implementation**
- [ ] - Dev Status: [Complete]
- [ ] - QA Status: [In Progress]

- [ ] - **T002: OAuth integration**
- [ ] - Dev Status: [Not Started]

## Feature: Database

- [ ] - **T003: Schema migrations**
- [ ] - Dev Status: [Complete]
- [ ] - QA Status: [Complete]

- [ ] - **T004: Query optimization**
- [ ] - Dev Status: [In Progress]

## Feature: API

- [ ] - **T005: REST endpoints**
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

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            # Should parse all 5 tasks across features
            assert len(tasks) == 5

            # Verify different states are captured
            states = {
                "not_started": [t for t in tasks if t.dev_state == "not_started"],
                "in_progress": [t for t in tasks if t.dev_state == "in_progress"],
                "complete": [t for t in tasks if t.dev_state == "complete"],
            }

            assert len(states["not_started"]) == 2
            assert len(states["in_progress"]) == 1
            assert len(states["complete"]) == 2

        finally:
            os.unlink(temp_path)

    def test_progressive_task_updates(self):
        """Test parsing as tasks progress through states."""
        # Create file with all possible status values so schema includes them
        initial_content = """
- [ ] - **T001: Progressive task**
- [ ] - Dev Status: [Not Started]
- [ ] - QA Status: [Not Started]

- [ ] - **T002: Example in progress**
- [ ] - Dev Status: [In Progress]
- [ ] - QA Status: [In Progress]

- [ ] - **T003: Example complete**
- [ ] - Dev Status: [Complete]
- [ ] - QA Status: [Complete]
        """

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(initial_content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)
            parser = TaskSchemaParser(schema)

            # State 1: Parse initial file
            tasks = parser.parse_tasks_file(temp_path)
            t001 = next(t for t in tasks if t.task_id == "T001")
            assert t001.dev_state == "not_started"

            # State 2: Update T001 to in progress
            content_in_progress = """
- [ ] - **T001: Progressive task**
- [ ] - Dev Status: [In Progress]
- [ ] - QA Status: [Not Started]

- [ ] - **T002: Example in progress**
- [ ] - Dev Status: [In Progress]
- [ ] - QA Status: [In Progress]

- [ ] - **T003: Example complete**
- [ ] - Dev Status: [Complete]
- [ ] - QA Status: [Complete]
            """
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content_in_progress)

            tasks = parser.parse_tasks_file(temp_path)
            t001 = next(t for t in tasks if t.task_id == "T001")
            assert t001.dev_state == "in_progress"

            # State 3: Dev complete, awaiting QA
            content_dev_complete = """
- [ ] - **T001: Progressive task**
- [ ] - Dev Status: [Complete]
- [ ] - QA Status: [In Progress]

- [ ] - **T002: Example in progress**
- [ ] - Dev Status: [In Progress]
- [ ] - QA Status: [In Progress]

- [ ] - **T003: Example complete**
- [ ] - Dev Status: [Complete]
- [ ] - QA Status: [Complete]
            """
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content_dev_complete)

            tasks = parser.parse_tasks_file(temp_path)
            t001 = next(t for t in tasks if t.task_id == "T001")
            assert t001.dev_state == "complete"
            assert t001.qa_state == "in_progress"

            # State 4: Fully complete
            content_complete = """
- [x] - **T001: Progressive task**
- [x] - Dev Status: [Complete]
- [x] - QA Status: [Complete]

- [ ] - **T002: Example in progress**
- [ ] - Dev Status: [In Progress]
- [ ] - QA Status: [In Progress]

- [ ] - **T003: Example complete**
- [ ] - Dev Status: [Complete]
- [ ] - QA Status: [Complete]
            """
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content_complete)

            tasks = parser.parse_tasks_file(temp_path)
            t001 = next(t for t in tasks if t.task_id == "T001")
            assert t001.dev_state == "complete"
            assert t001.qa_state == "complete"

        finally:
            os.unlink(temp_path)


class TestErrorRecovery:
    """Test error handling and recovery."""

    def test_partially_malformed_file(self):
        """Test that parser continues despite some malformed lines."""
        content = """
- [ ] - **T001: Valid task**
- [ ] - Dev Status: [Not Started]

This is invalid text

- [ ] - **T002: Another valid task**
- [ ] - Dev Status: [In Progress]

Invalid task line without format

- [ ] - **T003: Third valid task**
- [ ] - Dev Status: [Complete]
        """

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            generator = SchemaGenerator()
            schema = generator.generate_schema(temp_path)

            parser = TaskSchemaParser(schema)
            tasks = parser.parse_tasks_file(temp_path)

            # Should parse 3 valid tasks despite invalid lines
            assert len(tasks) == 3

        finally:
            os.unlink(temp_path)

    def test_schema_regeneration_after_format_change(self):
        """Test that schema can be regenerated if format changes."""
        # Original format
        original_content = """
- [ ] - **T001: Task one**
- [ ] - Dev Status: [Not Started]
        """

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(original_content)
            temp_path = f.name

        try:
            # Generate initial schema
            generator = SchemaGenerator()
            schema_v1 = generator.generate_schema(temp_path)

            # Change format (add more status fields)
            updated_content = """
- [ ] - **T001: Task one**
- [ ] - Development Status: [Not Started]
- [ ] - Quality Assurance Status: [Not Started]
- [ ] - User Verification: [Not Started]
            """

            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

            # Regenerate schema
            schema_v2 = generator.generate_schema(temp_path)

            # New schema should have more fields
            fields_v1 = len(schema_v1["status_semantics"]["field_mapping"])
            fields_v2 = len(schema_v2["status_semantics"]["field_mapping"])

            assert fields_v2 >= fields_v1

            # Both schemas should be valid
            parser1 = TaskSchemaParser(schema_v1)
            parser2 = TaskSchemaParser(schema_v2)

            assert parser1 is not None
            assert parser2 is not None

        finally:
            os.unlink(temp_path)
