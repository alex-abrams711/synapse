"""
Integration test for full workflow

Tests the complete workflow from start to finish:
1. Agent starts work and sets active_tasks
2. Agent tries to stop - hook blocks
3. Agent runs verification
4. Agent updates QA Status
5. Hook allows stop
"""

import json
import os
import subprocess
from pathlib import Path

import pytest


class TestFullWorkflow:
    """Integration test for complete workflow"""

    @pytest.fixture
    def sample_project(self, tmp_path):
        """Create a realistic sample project"""
        # Create .synapse directory
        synapse_dir = tmp_path / ".synapse"
        synapse_dir.mkdir()

        # Create config.json
        config = {
            "synapse_version": "1.0.0",
            "initialized_at": "2025-01-15T10:00:00Z",
            "project": {
                "name": "sample-app",
                "description": "Sample application for testing",
                "root_directory": str(tmp_path)
            },
            "workflows": {
                "active_workflow": "feature-implementation"
            },
            "settings": {
                "auto_backup": True,
                "strict_validation": True,
                "uv_required": False
            },
            "quality-config": {
                "mode": "single",
                "projectType": "python",
                "commands": {
                    "lint": "ruff check .",
                    "test": "pytest",
                    "typecheck": "mypy .",
                    "coverage": "pytest --cov --cov-report=term-missing",
                    "build": "python -m build"
                },
                "thresholds": {
                    "coverage": {
                        "statements": 80,
                        "branches": 70,
                        "functions": 80,
                        "lines": 80
                    },
                    "lintLevel": "strict"
                }
            },
            "third_party_workflow": {
                "type": "openspec",
                "detection_method": "known_pattern",
                "root_directory": str(tmp_path),
                "active_feature_directory": "features/user-auth",
                "active_tasks_file": "tasks.md",
                "active_tasks": [],  # Start with no active tasks
                "confidence": 0.95,
                "detected_at": "2025-01-15T10:00:00Z",
                "task_format_schema": {
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
            }
        }

        config_path = synapse_dir / "config.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        # Create tasks.md
        tasks_content = """# Feature: User Authentication

[ ] - T001 - Implement user login endpoint
  [ ] - T001-ST001 - Create POST /api/auth/login route
  [ ] - T001-ST002 - Add JWT token generation
  [ ] - T001-ST003 - Add password hashing with bcrypt
  [ ] - T001-DS - Dev Status: [Not Started]
  [ ] - T001-QA - QA Status: [Not Started]
  [ ] - T001-UV - User Verification Status: [Not Started]

[ ] - T002 - Implement user registration endpoint
  [ ] - T002-ST001 - Create POST /api/auth/register route
  [ ] - T002-ST002 - Add email validation
  [ ] - T002-ST003 - Add password strength checking
  [ ] - T002-DS - Dev Status: [Not Started]
  [ ] - T002-QA - QA Status: [Not Started]
  [ ] - T002-UV - User Verification Status: [Not Started]

[ ] - T003 - Add authentication middleware
  [ ] - T003-ST001 - Create JWT verification middleware
  [ ] - T003-ST002 - Add role-based access control
  [ ] - T003-DS - Dev Status: [Not Started]
  [ ] - T003-QA - QA Status: [Not Started]
  [ ] - T003-UV - User Verification Status: [Not Started]
"""
        tasks_path = tmp_path / "tasks.md"
        with open(tasks_path, "w") as f:
            f.write(tasks_content)

        # Store original directory
        original_dir = os.getcwd()

        # Change to temp directory
        os.chdir(tmp_path)

        yield tmp_path

        # Restore original directory
        os.chdir(original_dir)

    def run_hook(self, project_dir):
        """Run the stop_qa_check.py hook"""
        hook_path = Path(__file__).parent.parent.parent / "resources" / "workflows" / "feature-implementation" / "hooks" / "stop_qa_check.py"

        result = subprocess.run(
            ["python3", str(hook_path)],
            cwd=project_dir,
            capture_output=True,
            text=True
        )

        return result.returncode, result.stderr

    def update_config(self, project_dir, active_tasks):
        """Update active_tasks in config.json"""
        config_path = project_dir / ".synapse" / "config.json"

        with open(config_path, "r") as f:
            config = json.load(f)

        config["third_party_workflow"]["active_tasks"] = active_tasks

        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

    def update_task_qa_status(self, project_dir, task_code, qa_status):
        """Update QA Status for a specific task in tasks.md"""
        tasks_path = project_dir / "tasks.md"

        with open(tasks_path, "r") as f:
            content = f.read()

        # Replace the QA Status line for this task
        import re
        pattern = rf"(\[\s*\]\s*-\s*{task_code}-QA\s*-\s*QA Status:\s*\[)[^\]]+(\])"
        replacement = rf"\g<1>{qa_status}\g<2>"
        content = re.sub(pattern, replacement, content)

        with open(tasks_path, "w") as f:
            f.write(content)

    def test_full_workflow_all_pass(self, sample_project):
        """
        Test complete workflow where all tasks pass verification
        """
        # Step 1: Agent starts work on T001 and T002
        print("\n=== Step 1: Agent sets active_tasks ===")
        self.update_config(sample_project, ["T001", "T002"])

        # Step 2: Agent tries to stop - hook should block
        print("\n=== Step 2: Agent tries to stop - should be blocked ===")
        exit_code, stderr = self.run_hook(sample_project)
        assert exit_code == 2, "Hook should block - tasks not verified"
        assert "QA VERIFICATION REQUIRED" in stderr
        assert "T001" in stderr
        assert "T002" in stderr

        # Step 3: Agent runs verification and all tasks pass
        print("\n=== Step 3: Agent verifies tasks - all pass ===")
        self.update_task_qa_status(sample_project, "T001", "Passed")
        self.update_task_qa_status(sample_project, "T002", "Passed")

        # Step 4: Agent tries to stop - hook should allow
        print("\n=== Step 4: Agent tries to stop - should be allowed ===")
        exit_code, stderr = self.run_hook(sample_project)
        if exit_code != 0:
            print(f"DEBUG: Exit code: {exit_code}")
            print(f"DEBUG: stderr:\n{stderr}")
            # Also print the tasks.md content
            with open(sample_project / "tasks.md") as f:
                print(f"DEBUG: tasks.md content:\n{f.read()}")
        assert exit_code == 0, "Hook should allow - all tasks verified"
        assert "All active tasks verified" in stderr

        # Step 5: Agent clears active_tasks
        print("\n=== Step 5: Agent clears active_tasks ===")
        self.update_config(sample_project, [])

        # Step 6: Agent stops successfully
        print("\n=== Step 6: Agent stops - no active tasks ===")
        exit_code, stderr = self.run_hook(sample_project)
        assert exit_code == 0, "Hook should allow - no active tasks"

    def test_full_workflow_with_failures(self, sample_project):
        """
        Test workflow where some tasks fail verification
        """
        # Step 1: Agent starts work on T001, T002, T003
        print("\n=== Step 1: Agent sets active_tasks ===")
        self.update_config(sample_project, ["T001", "T002", "T003"])

        # Step 2: Agent verifies - T001 passes, T002 fails, T003 passes
        print("\n=== Step 2: Agent verifies - mixed results ===")
        self.update_task_qa_status(sample_project, "T001", "Passed")
        self.update_task_qa_status(sample_project, "T002", "Failed - lint errors on line 45, 67")
        self.update_task_qa_status(sample_project, "T003", "Passed")

        # Step 3: Agent tries to stop - hook should ALLOW (all verified)
        print("\n=== Step 3: Agent tries to stop - should be allowed (all verified) ===")
        exit_code, stderr = self.run_hook(sample_project)
        assert exit_code == 0, "Hook should allow - all tasks verified (including failures)"
        assert "verified failure - allows stop" in stderr

        # Step 4: Agent asks user, user says "no" to fixes
        # Agent removes passed tasks, keeps failed tasks
        print("\n=== Step 4: User declines fixes - keep failed tasks ===")
        self.update_config(sample_project, ["T002"])

        # Step 5: Agent stops successfully
        print("\n=== Step 5: Agent stops - failed task stays tracked ===")
        exit_code, stderr = self.run_hook(sample_project)
        assert exit_code == 0, "Hook should allow - T002 verified as failed"

    def test_workflow_fix_and_reverify(self, sample_project):
        """
        Test workflow where agent fixes failures and re-verifies
        """
        # Step 1: Start with failed task from previous session
        print("\n=== Step 1: Continuing with failed task ===")
        self.update_config(sample_project, ["T002"])
        self.update_task_qa_status(sample_project, "T002", "Failed - lint errors")

        # Verify hook allows stop with failed status
        exit_code, stderr = self.run_hook(sample_project)
        assert exit_code == 0, "Hook should allow - task verified as failed"

        # Step 2: Agent fixes issues and resets QA Status
        print("\n=== Step 2: Agent fixes issues, resets QA Status ===")
        self.update_task_qa_status(sample_project, "T002", "Not Started")

        # Step 3: Hook should now block - needs re-verification
        print("\n=== Step 3: Hook blocks - needs re-verification ===")
        exit_code, stderr = self.run_hook(sample_project)
        assert exit_code == 2, "Hook should block - T002 not verified"
        assert "T002" in stderr
        assert "QA VERIFICATION REQUIRED" in stderr

        # Step 4: Agent re-verifies, task passes this time
        print("\n=== Step 4: Agent re-verifies - task passes ===")
        self.update_task_qa_status(sample_project, "T002", "Passed")

        # Step 5: Hook allows stop
        print("\n=== Step 5: Hook allows stop ===")
        exit_code, stderr = self.run_hook(sample_project)
        assert exit_code == 0, "Hook should allow - task verified"

        # Step 6: Agent clears active_tasks
        print("\n=== Step 6: Agent clears active_tasks ===")
        self.update_config(sample_project, [])

        exit_code, stderr = self.run_hook(sample_project)
        assert exit_code == 0, "Hook should allow - no active tasks"

    def test_edge_case_task_not_in_file(self, sample_project):
        """
        Test edge case where active task is not found in task file
        """
        # Set active_tasks to task that doesn't exist
        self.update_config(sample_project, ["T999"])

        exit_code, stderr = self.run_hook(sample_project)
        assert exit_code == 2, "Hook should block - task not found"
        assert "T999" in stderr
        assert "not found in task file" in stderr

    def test_edge_case_missing_qa_field(self, sample_project):
        """
        Test edge case where task is missing QA Status field
        """
        # Add a task without QA Status field
        tasks_path = sample_project / "tasks.md"
        with open(tasks_path, "a") as f:
            f.write("""
[ ] - T999 - Task without QA field
  [ ] - T999-DS - Dev Status: [Complete]
""")

        self.update_config(sample_project, ["T999"])

        exit_code, stderr = self.run_hook(sample_project)
        assert exit_code == 2, "Hook should block - missing QA field"
        assert "T999" in stderr
        assert "missing QA Status field" in stderr

    def test_partial_verification_incremental(self, sample_project):
        """
        Test incremental verification of multiple tasks
        """
        # Start with 3 tasks
        self.update_config(sample_project, ["T001", "T002", "T003"])

        # Verify T001 first
        print("\n=== Verify T001 ===")
        self.update_task_qa_status(sample_project, "T001", "Passed")

        # Hook should still block - T002 and T003 not verified
        exit_code, stderr = self.run_hook(sample_project)
        assert exit_code == 2, "Hook should block - T002, T003 not verified"
        assert "T002" in stderr
        assert "T003" in stderr

        # Verify T002
        print("\n=== Verify T002 ===")
        self.update_task_qa_status(sample_project, "T002", "Passed")

        # Hook should still block - T003 not verified
        exit_code, stderr = self.run_hook(sample_project)
        assert exit_code == 2, "Hook should block - T003 not verified"
        assert "T003" in stderr

        # Verify T003
        print("\n=== Verify T003 ===")
        self.update_task_qa_status(sample_project, "T003", "Passed")

        # Hook should now allow
        exit_code, stderr = self.run_hook(sample_project)
        assert exit_code == 0, "Hook should allow - all verified"
