"""Unit tests for task_parser shared module."""
import pytest
import tempfile
import os
import json
import sys
from pathlib import Path

# Add hooks directory to Python path for importing task_parser
hooks_dir = Path(__file__).parent.parent / "resources" / "workflows" / "feature-implementation" / "hooks"
sys.path.insert(0, str(hooks_dir))

import task_parser
from task_parser import Task


class TestLoadSynapseConfig:
    """Test synapse config loading."""

    def test_load_valid_config(self, tmp_path):
        """Test loading a valid synapse config file."""
        config_dir = tmp_path / ".synapse"
        config_dir.mkdir()
        config_file = config_dir / "config.json"

        config_data = {
            "third_party_workflows": {
                "detected": [
                    {
                        "name": "test-workflow",
                        "active_tasks_file": "tasks.md"
                    }
                ]
            }
        }

        config_file.write_text(json.dumps(config_data))

        # Change to tmp directory
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            config = task_parser.load_synapse_config()
            assert config is not None
            assert config["third_party_workflows"]["detected"][0]["name"] == "test-workflow"
        finally:
            os.chdir(original_dir)

    def test_load_missing_config(self, tmp_path):
        """Test handling of missing config file."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            config = task_parser.load_synapse_config()
            assert config is None
        finally:
            os.chdir(original_dir)

    def test_load_invalid_json_config(self, tmp_path):
        """Test handling of invalid JSON in config file."""
        config_dir = tmp_path / ".synapse"
        config_dir.mkdir()
        config_file = config_dir / "config.json"

        config_file.write_text("{ invalid json }")

        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            config = task_parser.load_synapse_config()
            assert config is None
        finally:
            os.chdir(original_dir)


class TestFindActiveTasksFile:
    """Test finding active tasks file from config."""

    def test_find_tasks_file_in_config(self):
        """Test finding tasks file in valid config."""
        config = {
            "third_party_workflows": {
                "detected": [
                    {
                        "name": "workflow1",
                        "active_tasks_file": "tasks.md"
                    }
                ]
            }
        }

        tasks_file = task_parser.find_active_tasks_file(config)
        assert tasks_file == "tasks.md"

    def test_find_tasks_file_multiple_workflows(self):
        """Test finding tasks file with multiple workflows."""
        config = {
            "third_party_workflows": {
                "detected": [
                    {
                        "name": "workflow1",
                        "active_tasks_file": "tasks1.md"
                    },
                    {
                        "name": "workflow2",
                        "active_tasks_file": "tasks2.md"
                    }
                ]
            }
        }

        tasks_file = task_parser.find_active_tasks_file(config)
        # Should return first one
        assert tasks_file == "tasks1.md"

    def test_find_tasks_file_no_workflows(self):
        """Test handling of config with no workflows."""
        config = {
            "third_party_workflows": {
                "detected": []
            }
        }

        tasks_file = task_parser.find_active_tasks_file(config)
        assert tasks_file is None

    def test_find_tasks_file_none_config(self):
        """Test handling of None config."""
        tasks_file = task_parser.find_active_tasks_file(None)
        assert tasks_file is None


class TestExtractKeywords:
    """Test keyword extraction from descriptions."""

    def test_extract_keywords_basic(self):
        """Test extracting keywords from basic description."""
        description = "Task 1: Implement user authentication system"
        keywords = task_parser.extract_keywords_from_description(description)

        assert "implement" in keywords
        assert "user" in keywords
        assert "authentication" in keywords
        assert "system" in keywords

    def test_extract_keywords_with_markdown(self):
        """Test extracting keywords from description with markdown."""
        description = "[[Task 1: Add **API** endpoints]]"
        keywords = task_parser.extract_keywords_from_description(description)

        assert "add" in keywords
        assert "api" in keywords
        assert "endpoints" in keywords

    def test_extract_keywords_filters_stop_words(self):
        """Test that stop words are filtered out."""
        description = "The system will implement and create the authentication for users"
        keywords = task_parser.extract_keywords_from_description(description)

        # Stop words should be filtered
        assert "the" not in keywords
        assert "will" not in keywords
        assert "and" not in keywords
        assert "for" not in keywords

        # Real keywords should remain
        assert "system" in keywords
        assert "implement" in keywords
        assert "authentication" in keywords

    def test_extract_keywords_limits_to_10(self):
        """Test that keyword extraction is limited to 10 keywords."""
        description = "one two three four five six seven eight nine ten eleven twelve thirteen"
        keywords = task_parser.extract_keywords_from_description(description)

        assert len(keywords) <= 10


class TestParseTasksWithStructure:
    """Test parsing tasks file with structure."""

    def test_parse_basic_task(self, tmp_path):
        """Test parsing a basic task with status fields."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("""
[ ] - [[Task 1: Implement user authentication]]
  [ ] - Dev Status: [Not Started]
  [ ] - QA Status: [Not Started]
  [ ] - User Verification Status: [Not Started]
""")

        tasks = task_parser.parse_tasks_with_structure(str(tasks_file))

        assert len(tasks) == 1
        assert tasks[0].task_id == "Task 1"
        assert tasks[0].task_description == "Implement user authentication"
        assert tasks[0].dev_status == "Not Started"
        assert tasks[0].qa_status == "Not Started"
        assert tasks[0].user_verification_status == "Not Started"
        assert tasks[0].dev_status_checked == False
        assert tasks[0].qa_status_checked == False
        assert tasks[0].user_verification_checked == False

    def test_parse_task_with_checked_statuses(self, tmp_path):
        """Test parsing tasks with checked status checkboxes."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("""
[x] - [[Task 1: Complete feature]]
  [x] - Dev Status: [Complete]
  [x] - QA Status: [Complete]
  [ ] - User Verification Status: [Not Started]
""")

        tasks = task_parser.parse_tasks_with_structure(str(tasks_file))

        assert len(tasks) == 1
        assert tasks[0].dev_status == "Complete"
        assert tasks[0].qa_status == "Complete"
        assert tasks[0].user_verification_status == "Not Started"
        assert tasks[0].dev_status_checked == True
        assert tasks[0].qa_status_checked == True
        assert tasks[0].user_verification_checked == False

    def test_parse_task_with_uppercase_x(self, tmp_path):
        """Test parsing tasks with uppercase X in checkboxes."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("""
[X] - [[Task 1: Test uppercase]]
  [X] - Dev Status: [Complete]
  [X] - QA Status: [Complete]
""")

        tasks = task_parser.parse_tasks_with_structure(str(tasks_file))

        assert len(tasks) == 1
        assert tasks[0].dev_status_checked == True
        assert tasks[0].qa_status_checked == True

    def test_parse_multiple_tasks(self, tmp_path):
        """Test parsing multiple tasks."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("""
[ ] - [[Task 1: First task]]
  [ ] - Dev Status: [Not Started]
  [ ] - QA Status: [Not Started]

[ ] - [[Task 2: Second task]]
  [x] - Dev Status: [In Progress]
  [ ] - QA Status: [Not Started]

[x] - [[Task 3: Third task]]
  [x] - Dev Status: [Complete]
  [x] - QA Status: [Complete]
""")

        tasks = task_parser.parse_tasks_with_structure(str(tasks_file))

        assert len(tasks) == 3
        assert tasks[0].task_id == "Task 1"
        assert tasks[1].task_id == "Task 2"
        assert tasks[2].task_id == "Task 3"
        assert tasks[1].dev_status == "In Progress"
        assert tasks[1].dev_status_checked == True

    def test_parse_task_stores_qa_line_number(self, tmp_path):
        """Test that QA Status line number is stored."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("""
[ ] - [[Task 1: Test task]]
  [ ] - Dev Status: [Not Started]
  [ ] - QA Status: [Not Started]
  [ ] - User Verification Status: [Not Started]
""")

        tasks = task_parser.parse_tasks_with_structure(str(tasks_file))

        assert len(tasks) == 1
        assert tasks[0].qa_status_line_number is not None
        assert tasks[0].qa_status_line_number == 4  # QA Status is on line 4

    def test_parse_missing_file(self):
        """Test handling of missing tasks file."""
        tasks = task_parser.parse_tasks_with_structure("/nonexistent/file.md")
        assert tasks == []

    def test_parse_task_with_different_id_format(self, tmp_path):
        """Test parsing task with T-001 style ID."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("""
[ ] - [[T-001: Implement feature]]
  [ ] - Dev Status: [Not Started]
""")

        tasks = task_parser.parse_tasks_with_structure(str(tasks_file))

        assert len(tasks) == 1
        assert tasks[0].task_id == "T-001"
        assert tasks[0].task_description == "Implement feature"

    def test_parse_task_without_id_pattern(self, tmp_path):
        """Test parsing task without clear ID pattern."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("""
[ ] - [[Implement user authentication system]]
  [ ] - Dev Status: [Not Started]
""")

        tasks = task_parser.parse_tasks_with_structure(str(tasks_file))

        assert len(tasks) == 1
        # Should use first 3 words as ID
        assert tasks[0].task_id == "Implement user authentication"


class TestFindMatchingTask:
    """Test finding matching tasks from prompts."""

    def test_exact_task_id_match(self):
        """Test exact task ID matching."""
        tasks = [
            Task("Task 1", "First task", "Not Started", "Not Started", "Not Started",
                 False, False, False, ["first", "task"], 1),
            Task("Task 2", "Second task", "Not Started", "Not Started", "Not Started",
                 False, False, False, ["second", "task"], 5)
        ]

        prompt = "Please work on Task 2 implementation"
        match = task_parser.find_matching_task(prompt, tasks)

        assert match is not None
        assert match.task_id == "Task 2"

    def test_keyword_matching(self):
        """Test keyword-based matching."""
        tasks = [
            Task("Task 1", "Implement authentication", "Not Started", "Not Started", "Not Started",
                 False, False, False, ["implement", "authentication"], 1),
            Task("Task 2", "Create database schema", "Not Started", "Not Started", "Not Started",
                 False, False, False, ["create", "database", "schema"], 5)
        ]

        prompt = "I need to work on the database schema creation"
        match = task_parser.find_matching_task(prompt, tasks)

        assert match is not None
        assert match.task_id == "Task 2"

    def test_best_keyword_match(self):
        """Test that best keyword match is selected."""
        tasks = [
            Task("Task 1", "Implement feature", "Not Started", "Not Started", "Not Started",
                 False, False, False, ["implement", "feature"], 1),
            Task("Task 2", "Implement authentication system", "Not Started", "Not Started", "Not Started",
                 False, False, False, ["implement", "authentication", "system"], 5)
        ]

        prompt = "Work on implementing the authentication system"
        match = task_parser.find_matching_task(prompt, tasks)

        assert match is not None
        # Task 2 should match better (more keywords)
        assert match.task_id == "Task 2"

    def test_no_match_found(self):
        """Test when no match is found."""
        tasks = [
            Task("Task 1", "Implement feature", "Not Started", "Not Started", "Not Started",
                 False, False, False, ["implement", "feature"], 1)
        ]

        prompt = "Work on something completely unrelated"
        match = task_parser.find_matching_task(prompt, tasks)

        assert match is None

    def test_empty_tasks_list(self):
        """Test with empty tasks list."""
        match = task_parser.find_matching_task("any prompt", [])
        assert match is None

    def test_case_insensitive_matching(self):
        """Test that matching is case insensitive."""
        tasks = [
            Task("TASK 1", "Test Task", "Not Started", "Not Started", "Not Started",
                 False, False, False, ["test", "task"], 1)
        ]

        prompt = "work on task 1"
        match = task_parser.find_matching_task(prompt, tasks)

        assert match is not None
        assert match.task_id == "TASK 1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
