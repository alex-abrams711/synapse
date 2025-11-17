"""
Unit tests for stop_qa_check.py hook

Test coverage:
1. Empty active_tasks returns exit 0
2. Task file missing returns exit 2
3. Task not found in file returns exit 2
4. Task missing QA Status returns exit 2 with warning
5. All tasks verified returns exit 0
6. Some tasks not verified returns exit 2
7. Malformed task file graceful handling
8. Invalid schema graceful handling
9. Exit 2 directive contains all required sections
10. Partial verification (some tasks already verified)
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


# Sample task format schema
SAMPLE_SCHEMA = {
    "version": "2.0",
    "patterns": {
        "task": r"^\[\s*\]\s*-\s*(?P<task_code>T\d{3,})\s+-\s+(?P<description>(?!.*:).*)",
        "subtask": r"^\s+\[\s*\]\s*-\s*(?P<subtask_code>T\d{3,}-ST\d{3,})\s*-\s*(?P<description>.*)",
        "status_field": r"^\s+\[\s*\]\s*-\s*T\d{3,}-(?P<field_code>[A-Z]{2,})\s*-\s*.*:\s*\[(?P<status_value>[^\]]+)\]"
    },
    "field_mapping": {
        "dev_status": "DS",
        "qa": "QA",
        "user_verification": "UV"
    },
    "status_semantics": {
        "states": {
            "dev": {
                "not_started": ["Not Started"],
                "in_progress": ["In Progress"],
                "complete": ["Complete"]
            },
            "qa": {
                "not_verified": ["Not Started"],
                "verified_success": ["Complete", "Passed"],
                "verified_failure_pattern": "^Failed - .*"
            },
            "user_verification": {
                "not_started": ["Not Started"],
                "verified": ["Verified"]
            }
        }
    }
}


# Sample quality config
SAMPLE_QUALITY_CONFIG = {
    "mode": "single",
    "projectType": "python",
    "commands": {
        "lint": "ruff check .",
        "test": "pytest",
        "typecheck": "mypy .",
        "coverage": "pytest --cov",
        "build": "python -m build"
    },
    "thresholds": {
        "coverage": {
            "statements": 80,
            "branches": 70,
            "functions": 80,
            "lines": 80
        }
    }
}


class TestStopQACheck:
    """Test suite for stop_qa_check.py hook"""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project structure"""
        # Create .synapse directory
        synapse_dir = tmp_path / ".synapse"
        synapse_dir.mkdir()

        # Store original directory
        original_dir = os.getcwd()

        # Change to temp directory
        os.chdir(tmp_path)

        yield tmp_path

        # Restore original directory
        os.chdir(original_dir)

    def create_config(self, project_dir, active_tasks=None, task_file="tasks.md", schema=None):
        """Helper to create config.json"""
        if schema is None:
            schema = SAMPLE_SCHEMA

        config = {
            "synapse_version": "1.0.0",
            "project": {
                "name": "test-project",
                "root_directory": str(project_dir)
            },
            "workflows": {
                "active_workflow": "feature-implementation"
            },
            "settings": {},
            "quality-config": SAMPLE_QUALITY_CONFIG,
            "third_party_workflow": {
                "type": "openspec",
                "active_tasks_file": task_file,
                "active_tasks": active_tasks or [],
                "task_format_schema": schema
            }
        }

        config_path = project_dir / ".synapse" / "config.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

    def create_task_file(self, project_dir, content, filename="tasks.md"):
        """Helper to create task file"""
        task_path = project_dir / filename
        with open(task_path, "w") as f:
            f.write(content)

    def run_hook(self, project_dir):
        """Run the stop_qa_check.py hook and return exit code and stderr"""
        hook_path = Path(__file__).parent.parent / "resources" / "workflows" / "feature-implementation" / "hooks" / "stop_qa_check.py"

        result = subprocess.run(
            ["python3", str(hook_path)],
            cwd=project_dir,
            capture_output=True,
            text=True
        )

        return result.returncode, result.stderr

    def test_empty_active_tasks(self, temp_project):
        """Test: Empty active_tasks returns exit 2 (blocks stop)"""
        self.create_config(temp_project, active_tasks=[])
        self.create_task_file(temp_project, "")

        exit_code, stderr = self.run_hook(temp_project)

        assert exit_code == 2, f"Expected exit 2 for empty active_tasks, got {exit_code}"
        assert "STOP BLOCKED - No Active Tasks Set" in stderr
        assert "must set active_tasks" in stderr

    def test_task_file_missing(self, temp_project):
        """Test: Task file missing returns exit 2"""
        self.create_config(temp_project, active_tasks=["T001"], task_file="nonexistent.md")

        exit_code, stderr = self.run_hook(temp_project)

        assert exit_code == 2, f"Expected exit 2 for missing task file, got {exit_code}"
        assert "Task File Not Found" in stderr
        assert "nonexistent.md" in stderr

    def test_task_not_found_in_file(self, temp_project):
        """Test: Task not found in file returns exit 2"""
        self.create_config(temp_project, active_tasks=["T001", "T002"])

        # Create task file with only T001
        task_content = """
[ ] - T001 - Task one
  [ ] - T001-QA - QA Status: [Not Started]
"""
        self.create_task_file(temp_project, task_content)

        exit_code, stderr = self.run_hook(temp_project)

        assert exit_code == 2, f"Expected exit 2 for task not found, got {exit_code}"
        assert "T002" in stderr
        assert "not found in task file" in stderr

    def test_task_missing_qa_status(self, temp_project):
        """Test: Task missing QA Status returns exit 2 with warning"""
        self.create_config(temp_project, active_tasks=["T001"])

        # Create task without QA Status field
        task_content = """
[ ] - T001 - Task one
  [ ] - T001-DS - Dev Status: [Complete]
"""
        self.create_task_file(temp_project, task_content)

        exit_code, stderr = self.run_hook(temp_project)

        assert exit_code == 2, f"Expected exit 2 for missing QA Status, got {exit_code}"
        assert "T001" in stderr
        assert "missing QA Status field" in stderr

    def test_all_tasks_verified_success(self, temp_project):
        """Test: All tasks verified with success returns exit 0"""
        self.create_config(temp_project, active_tasks=["T001", "T002"])

        task_content = """
[ ] - T001 - Task one
  [ ] - T001-QA - QA Status: [Passed]

[ ] - T002 - Task two
  [ ] - T002-QA - QA Status: [Complete]
"""
        self.create_task_file(temp_project, task_content)

        exit_code, stderr = self.run_hook(temp_project)

        assert exit_code == 0, f"Expected exit 0 for all verified, got {exit_code}"
        assert "QA VERIFICATION COMPLETE" in stderr

    def test_all_tasks_verified_with_failures(self, temp_project):
        """Test: All tasks verified (including failures) returns exit 0"""
        self.create_config(temp_project, active_tasks=["T001", "T002"])

        task_content = """
[ ] - T001 - Task one
  [ ] - T001-QA - QA Status: [Passed]

[ ] - T002 - Task two
  [ ] - T002-QA - QA Status: [Failed - lint errors on line 45]
"""
        self.create_task_file(temp_project, task_content)

        exit_code, stderr = self.run_hook(temp_project)

        assert exit_code == 0, f"Expected exit 0 for verified failures, got {exit_code}"
        assert "QA VERIFICATION COMPLETE" in stderr
        assert "verified failure - allows stop" in stderr

    def test_some_tasks_not_verified(self, temp_project):
        """Test: Some tasks not verified returns exit 2"""
        self.create_config(temp_project, active_tasks=["T001", "T002"])

        task_content = """
[ ] - T001 - Task one
  [ ] - T001-QA - QA Status: [Passed]

[ ] - T002 - Task two
  [ ] - T002-QA - QA Status: [Not Started]
"""
        self.create_task_file(temp_project, task_content)

        exit_code, stderr = self.run_hook(temp_project)

        assert exit_code == 2, f"Expected exit 2 for unverified tasks, got {exit_code}"
        assert "QA VERIFICATION REQUIRED" in stderr
        assert "T002" in stderr

    def test_malformed_task_file(self, temp_project):
        """Test: Malformed task file graceful handling"""
        self.create_config(temp_project, active_tasks=["T001"])

        # Create task file with some malformed lines
        task_content = """
This is a random line
[ ] - T001 - Task one
Some other random content
  [ ] - T001-QA - QA Status: [Passed]
More garbage
"""
        self.create_task_file(temp_project, task_content)

        exit_code, stderr = self.run_hook(temp_project)

        # Should still work - just ignore malformed lines
        assert exit_code == 0, f"Expected exit 0 despite malformed content, got {exit_code}"

    def test_invalid_schema_missing_patterns(self, temp_project):
        """Test: Invalid schema graceful handling"""
        # Schema without patterns
        invalid_schema = {
            "version": "2.0",
            "field_mapping": {},
            "status_semantics": {}
        }

        self.create_config(temp_project, active_tasks=["T001"], schema=invalid_schema)
        self.create_task_file(temp_project, "")

        exit_code, stderr = self.run_hook(temp_project)

        assert exit_code == 2, f"Expected exit 2 for invalid schema, got {exit_code}"
        assert "ERROR" in stderr

    def test_exit_2_directive_format(self, temp_project):
        """Test: Exit 2 directive contains all required sections"""
        self.create_config(temp_project, active_tasks=["T001"])

        task_content = """
[ ] - T001 - Task one
  [ ] - T001-QA - QA Status: [Not Started]
"""
        self.create_task_file(temp_project, task_content)

        exit_code, stderr = self.run_hook(temp_project)

        assert exit_code == 2

        # Check all required sections
        assert "QA VERIFICATION REQUIRED" in stderr
        assert "Active Tasks Needing Verification" in stderr
        assert "Quality Commands" in stderr
        assert "Verification Process" in stderr
        assert "Completion Report Format" in stderr

        # Check quality commands are listed
        assert "**lint**:" in stderr or "lint:" in stderr
        assert "**test**:" in stderr or "test:" in stderr
        assert "**typecheck**:" in stderr or "typecheck:" in stderr
        assert "**coverage**:" in stderr or "coverage:" in stderr
        assert "**build**:" in stderr or "build:" in stderr

    def test_partial_verification(self, temp_project):
        """Test: Partial verification (some tasks already verified)"""
        self.create_config(temp_project, active_tasks=["T001", "T002", "T003"])

        task_content = """
[ ] - T001 - Task one
  [ ] - T001-QA - QA Status: [Passed]

[ ] - T002 - Task two
  [ ] - T002-QA - QA Status: [Not Started]

[ ] - T003 - Task three
  [ ] - T003-QA - QA Status: [Failed - build error]
"""
        self.create_task_file(temp_project, task_content)

        exit_code, stderr = self.run_hook(temp_project)

        # Should block because T002 is not verified
        assert exit_code == 2

        # Should only mention T002 in directive (not T001 or T003)
        assert "T002" in stderr

        # Should show T001 and T003 as verified in logs
        assert "T001" in stderr and "verified success" in stderr
        assert "T003" in stderr and "verified failure" in stderr

    def test_monorepo_mode_directive(self, temp_project):
        """Test: Monorepo mode shows project-specific commands in directive"""
        # Create monorepo quality config
        monorepo_config = {
            "mode": "monorepo",
            "projects": {
                "frontend": {
                    "directory": "packages/frontend/",
                    "projectType": "node",
                    "commands": {
                        "lint": "npm run lint",
                        "test": "npm test",
                        "typecheck": "tsc",
                        "coverage": "npm run coverage",
                        "build": "npm run build"
                    },
                    "thresholds": {}
                },
                "backend": {
                    "directory": "packages/backend/",
                    "projectType": "python",
                    "commands": {
                        "lint": "ruff check .",
                        "test": "pytest",
                        "typecheck": "mypy .",
                        "coverage": "pytest --cov",
                        "build": "python -m build"
                    },
                    "thresholds": {}
                }
            }
        }

        config = {
            "synapse_version": "1.0.0",
            "project": {"name": "test", "root_directory": str(temp_project)},
            "workflows": {},
            "settings": {},
            "quality-config": monorepo_config,
            "third_party_workflow": {
                "type": "openspec",
                "active_tasks_file": "tasks.md",
                "active_tasks": ["T001"],
                "task_format_schema": SAMPLE_SCHEMA
            }
        }

        config_path = temp_project / ".synapse" / "config.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        task_content = """
[ ] - T001 - Task one
  [ ] - T001-QA - QA Status: [Not Started]
"""
        self.create_task_file(temp_project, task_content)

        exit_code, stderr = self.run_hook(temp_project)

        assert exit_code == 2

        # Check monorepo projects are listed
        assert "frontend:" in stderr
        assert "backend:" in stderr
        assert "npm run lint" in stderr
        assert "ruff check" in stderr

    def test_unknown_qa_status_treated_as_not_verified(self, temp_project):
        """Test: Unknown QA Status value treated as not verified"""
        self.create_config(temp_project, active_tasks=["T001"])

        task_content = """
[ ] - T001 - Task one
  [ ] - T001-QA - QA Status: [Some Unknown Status]
"""
        self.create_task_file(temp_project, task_content)

        exit_code, stderr = self.run_hook(temp_project)

        assert exit_code == 2
        assert "unknown status" in stderr.lower()
        assert "treating as not verified" in stderr.lower()

    def test_no_workflow_configured(self, temp_project):
        """Test: No third_party_workflow in config returns exit 2"""
        config = {
            "synapse_version": "1.0.0",
            "project": {"name": "test", "root_directory": str(temp_project)},
            "workflows": {},
            "settings": {},
            "quality-config": SAMPLE_QUALITY_CONFIG
        }

        config_path = temp_project / ".synapse" / "config.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        exit_code, stderr = self.run_hook(temp_project)

        assert exit_code == 2
        assert "No Workflow Configured" in stderr

    def test_missing_active_tasks_file_field(self, temp_project):
        """Test: Missing active_tasks_file in config returns exit 2"""
        config = {
            "synapse_version": "1.0.0",
            "project": {"name": "test", "root_directory": str(temp_project)},
            "workflows": {},
            "settings": {},
            "quality-config": SAMPLE_QUALITY_CONFIG,
            "third_party_workflow": {
                "type": "openspec",
                "active_tasks": ["T001"],
                "task_format_schema": SAMPLE_SCHEMA
            }
        }

        config_path = temp_project / ".synapse" / "config.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        exit_code, stderr = self.run_hook(temp_project)

        assert exit_code == 2
        assert "Missing Configuration" in stderr
        assert "active_tasks_file" in stderr
