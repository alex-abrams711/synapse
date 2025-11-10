"""Integration tests for schema-aware task blocking logic."""
import pytest
import tempfile
import os
import json
import sys
from pathlib import Path

# Add hooks directory to Python path
hooks_dir = Path(__file__).parent.parent.parent / "legacy" / "resources" / "workflows" / "feature-implementation" / "hooks"
sys.path.insert(0, str(hooks_dir))

import task_parser
from task_parser import Task, normalize_status_to_semantic, get_canonical_status_value

# Import pre-tool-use.py for blocking logic tests (filename has hyphens, so use importlib)
import importlib.util
pre_tool_use_file = hooks_dir / "pre-tool-use.py"
spec = importlib.util.spec_from_file_location("pre_tool_use", pre_tool_use_file)
pre_tool_use = importlib.util.module_from_spec(spec)
sys.modules["pre_tool_use"] = pre_tool_use
spec.loader.exec_module(pre_tool_use)
check_task_specific_blocking = pre_tool_use.check_task_specific_blocking


class TestStatusNormalization:
    """Test status normalization with different value conventions."""

    def test_normalize_without_schema_fallback(self):
        """Test normalization falls back to keyword matching when no schema."""
        # Test "not_started" variations
        assert normalize_status_to_semantic("Not Started", "dev", None) == "not_started"
        assert normalize_status_to_semantic("Pending", "dev", None) == "not_started"
        assert normalize_status_to_semantic("Todo", "dev", None) == "not_started"
        assert normalize_status_to_semantic("Waiting", "dev", None) == "not_started"

        # Test "in_progress" variations
        assert normalize_status_to_semantic("In Progress", "dev", None) == "in_progress"
        assert normalize_status_to_semantic("Working", "dev", None) == "in_progress"
        assert normalize_status_to_semantic("Active", "dev", None) == "in_progress"

        # Test "complete" variations
        assert normalize_status_to_semantic("Complete", "qa", None) == "complete"
        assert normalize_status_to_semantic("Done", "qa", None) == "complete"
        assert normalize_status_to_semantic("Finished", "qa", None) == "complete"
        assert normalize_status_to_semantic("Passed", "qa", None) == "complete"
        assert normalize_status_to_semantic("Verified", "user_verification", None) == "complete"

    def test_normalize_with_schema(self):
        """Test normalization uses schema when available."""
        config = {
            "third_party_workflows": {
                "detected": [{
                    "task_format_schema": {
                        "status_semantics": {
                            "states": {
                                "dev": {
                                    "not_started": ["Not Started", "Todo"],
                                    "in_progress": ["In Progress", "Working"],
                                    "complete": ["Complete", "Done"]
                                },
                                "qa": {
                                    "not_started": ["Not Started"],
                                    "in_progress": ["In Progress", "Testing"],
                                    "complete": ["Passed", "Approved"]
                                }
                            }
                        }
                    }
                }]
            }
        }

        # Test schema-defined mappings
        assert normalize_status_to_semantic("Todo", "dev", config) == "not_started"
        assert normalize_status_to_semantic("Working", "dev", config) == "in_progress"
        assert normalize_status_to_semantic("Done", "dev", config) == "complete"
        assert normalize_status_to_semantic("Passed", "qa", config) == "complete"
        assert normalize_status_to_semantic("Approved", "qa", config) == "complete"
        assert normalize_status_to_semantic("Testing", "qa", config) == "in_progress"

    def test_get_canonical_status_without_schema(self):
        """Test getting canonical status uses fallback without schema."""
        assert get_canonical_status_value("not_started", "dev", None) == "Not Started"
        assert get_canonical_status_value("in_progress", "dev", None) == "In Progress"
        assert get_canonical_status_value("complete", "dev", None) == "Complete"

    def test_get_canonical_status_with_schema(self):
        """Test getting canonical status uses schema when available."""
        config = {
            "third_party_workflows": {
                "detected": [{
                    "task_format_schema": {
                        "status_semantics": {
                            "states": {
                                "qa": {
                                    "not_started": ["Not Started"],
                                    "complete": ["Passed", "QA Complete"]
                                }
                            }
                        }
                    }
                }]
            }
        }

        # Should return first value in list
        assert get_canonical_status_value("complete", "qa", config) == "Passed"
        assert get_canonical_status_value("not_started", "qa", config) == "Not Started"


class TestBlockingWithDifferentStatusConventions:
    """Test blocking logic works with different status value conventions."""

    def test_blocking_with_standard_values(self, tmp_path):
        """Test blocking with standard status values (Not Started/In Progress/Complete)."""
        # Create tasks file with standard values
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("""
[ ] - [[Task 1: First task]]
  [x] - Dev Status: [Complete]
  [x] - QA Status: [Complete]
  [ ] - User Verification Status: [Not Started]

[ ] - [[Task 2: Second task]]
  [ ] - Dev Status: [Not Started]
  [ ] - QA Status: [Not Started]
  [ ] - User Verification Status: [Not Started]
""")

        # Parse without schema (uses fallback)
        tasks = task_parser.parse_tasks_with_structure(str(tasks_file), None)

        assert len(tasks) == 2
        assert tasks[0].dev_state == "complete"
        assert tasks[0].qa_state == "complete"
        assert tasks[0].uv_state == "not_started"

        # Task 1 should block Task 2 (QA Complete but UV not done)
        # Simulate blocking check
        should_block, reason = check_task_specific_blocking(tasks[1], tasks)
        assert should_block == True
        assert "awaiting" in reason.lower() and "verification" in reason.lower()

    def test_blocking_with_alternate_values(self, tmp_path):
        """Test blocking with alternate status values (Pending/Working/Done)."""
        # Create config with alternate status mapping
        config = {
            "third_party_workflows": {
                "detected": [{
                    "task_format_schema": {
                        "status_semantics": {
                            "states": {
                                "dev": {
                                    "not_started": ["Pending"],
                                    "in_progress": ["Working"],
                                    "complete": ["Done"]
                                },
                                "qa": {
                                    "not_started": ["Pending"],
                                    "complete": ["Approved"]
                                },
                                "user_verification": {
                                    "not_started": ["Pending"],
                                    "complete": ["Verified"]
                                }
                            }
                        }
                    }
                }]
            }
        }

        # Create tasks file with alternate values
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("""
[ ] - [[Task 1: First task]]
  [x] - Dev Status: [Done]
  [x] - QA Status: [Approved]
  [ ] - User Verification Status: [Pending]

[ ] - [[Task 2: Second task]]
  [ ] - Dev Status: [Pending]
  [ ] - QA Status: [Pending]
  [ ] - User Verification Status: [Pending]
""")

        # Parse with schema
        tasks = task_parser.parse_tasks_with_structure(str(tasks_file), config)

        assert len(tasks) == 2
        # Schema should normalize "Done" → "complete"
        assert tasks[0].dev_state == "complete"
        assert tasks[0].qa_state == "complete"
        assert tasks[0].uv_state == "not_started"  # "Pending" → "not_started"

        # Same blocking logic should work
        should_block, reason = check_task_specific_blocking(tasks[1], tasks)
        assert should_block == True

    def test_blocking_with_project_specific_values(self, tmp_path):
        """Test blocking with project-specific status values."""
        # Simulate a project that uses "QA Passed" instead of "Complete"
        config = {
            "third_party_workflows": {
                "detected": [{
                    "task_format_schema": {
                        "status_semantics": {
                            "states": {
                                "dev": {
                                    "not_started": ["Not Started"],
                                    "in_progress": ["In Progress"],
                                    "complete": ["Complete"]
                                },
                                "qa": {
                                    "not_started": ["Not Started"],
                                    "complete": ["QA Passed"]  # Project-specific value
                                },
                                "user_verification": {
                                    "not_started": ["Not Started"],
                                    "complete": ["User Verified"]  # Project-specific value
                                }
                            }
                        }
                    }
                }]
            }
        }

        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("""
[ ] - [[Task 1: First task]]
  [x] - Dev Status: [Complete]
  [x] - QA Status: [QA Passed]
  [ ] - User Verification Status: [Not Started]
""")

        tasks = task_parser.parse_tasks_with_structure(str(tasks_file), config)

        assert len(tasks) == 1
        # Schema should normalize "QA Passed" → "complete"
        assert tasks[0].qa_state == "complete"

    def test_no_blocking_when_all_complete(self, tmp_path):
        """Test no blocking when previous task is fully complete."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("""
[ ] - [[Task 1: First task]]
  [x] - Dev Status: [Complete]
  [x] - QA Status: [Complete]
  [x] - User Verification Status: [Complete]

[ ] - [[Task 2: Second task]]
  [ ] - Dev Status: [Not Started]
  [ ] - QA Status: [Not Started]
  [ ] - User Verification Status: [Not Started]
""")

        tasks = task_parser.parse_tasks_with_structure(str(tasks_file), None)

        should_block, reason = check_task_specific_blocking(tasks[1], tasks)
        assert should_block == False  # Should allow work on Task 2

    def test_allow_in_progress_task_continuation(self, tmp_path):
        """Test that work on in-progress task is always allowed."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("""
[ ] - [[Task 1: First task]]
  [x] - Dev Status: [In Progress]
  [ ] - QA Status: [Not Started]
  [ ] - User Verification Status: [Not Started]
""")

        tasks = task_parser.parse_tasks_with_structure(str(tasks_file), None)

        should_block, reason = check_task_specific_blocking(tasks[0], tasks)
        assert should_block == False  # Should allow continued work


class TestCrossProjectPortability:
    """Test that workflows are portable across projects with different conventions."""

    def test_project_a_uses_complete_project_b_uses_passed(self):
        """Test same workflow works for projects using different QA status names."""
        # Project A uses "Complete" for QA
        config_a = {
            "third_party_workflows": {
                "detected": [{
                    "task_format_schema": {
                        "status_semantics": {
                            "states": {
                                "qa": {
                                    "not_started": ["Not Started"],
                                    "complete": ["Complete"]
                                },
                                "dev": {
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
                }]
            }
        }

        # Project B uses "Passed" for QA
        config_b = {
            "third_party_workflows": {
                "detected": [{
                    "task_format_schema": {
                        "status_semantics": {
                            "states": {
                                "qa": {
                                    "not_started": ["Not Started"],
                                    "complete": ["Passed"]
                                },
                                "dev": {
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
                }]
            }
        }

        # Both should normalize to same semantic state
        assert normalize_status_to_semantic("Complete", "qa", config_a) == "complete"
        assert normalize_status_to_semantic("Passed", "qa", config_b) == "complete"

        # Both should use same blocking logic
        # (This proves workflow portability)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
