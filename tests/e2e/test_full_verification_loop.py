"""End-to-end tests for complete verification workflow loop."""
import pytest
import tempfile
import os
import json
import sys
from pathlib import Path

# Add hooks directory to Python path
hooks_dir = Path(__file__).parent.parent.parent / "resources" / "workflows" / "feature-implementation" / "hooks"
sys.path.insert(0, str(hooks_dir))

import task_parser
from task_parser import Task

# Import verification functions by loading the module
import importlib.util
spec = importlib.util.spec_from_file_location(
    "verification_complete",
    hooks_dir / "verification-complete.py"
)
verification_complete = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verification_complete)


class TestImplementerVerifierPassFlow:
    """Test complete flow: implementer → verifier → PASS."""

    def test_successful_verification_flow(self, tmp_path):
        """Test complete flow where verification passes on first try (T055 part 1)."""
        # Step 1: Create tasks file with task in Dev Complete status
        tasks_file = tmp_path / "tasks.md"
        initial_content = """
[ ] - [[Task 1: Implement user login feature]]
  [x] - Dev Status: [Complete]
  [ ] - QA Status: [Not Started]
  [ ] - User Verification Status: [Not Started]
"""
        tasks_file.write_text(initial_content)

        # Step 2: Parse tasks (simulates pre-tool-use hook)
        tasks = task_parser.parse_tasks_with_structure(str(tasks_file))
        assert len(tasks) == 1
        assert tasks[0].dev_status == "Complete"
        assert tasks[0].qa_status == "Not Started"

        # Step 3: Verifier runs and updates QA Status (simulates verifier agent)
        updated_content = """
[ ] - [[Task 1: Implement user login feature]]
  [x] - Dev Status: [Complete]
  [x] - QA Status: [Complete]
  [ ] - User Verification Status: [Not Started]
"""
        tasks_file.write_text(updated_content)

        # Step 4: Parse updated tasks (simulates verification-complete hook)
        tasks = task_parser.parse_tasks_with_structure(str(tasks_file))
        assert len(tasks) == 1
        assert tasks[0].qa_status == "Complete"
        assert tasks[0].qa_status_checked == True

        # Step 5: Validate QA Status (simulates hook validation)
        verifier_response = "All tests passed. STATUS: PASS"
        is_valid, error = verification_complete.validate_qa_status_for_pass(tasks[0], verifier_response)

        assert is_valid == True
        assert error == ""

    def test_verification_with_alternate_status_values(self, tmp_path):
        """Test flow with alternate valid status values."""
        tasks_file = tmp_path / "tasks.md"

        # Test with "Done" status
        content = """
[ ] - [[Task 1: Test feature]]
  [x] - Dev Status: [Complete]
  [x] - QA Status: [Done]
  [ ] - User Verification Status: [Not Started]
"""
        tasks_file.write_text(content)

        tasks = task_parser.parse_tasks_with_structure(str(tasks_file))
        is_valid, error = verification_complete.validate_qa_status_for_pass(tasks[0], "STATUS: PASS")
        assert is_valid == True


class TestImplementerVerifierFailFixFlow:
    """Test complete flow: implementer → verifier → FAIL → implementer → verifier → PASS."""

    def test_verification_fail_then_fix_flow(self, tmp_path):
        """Test flow where verification fails, implementer fixes, then passes (T055 part 2)."""
        tasks_file = tmp_path / "tasks.md"

        # Step 1: Initial state - Dev Complete, QA Not Started
        tasks_file.write_text("""
[ ] - [[Task 1: Implement form validation]]
  [x] - Dev Status: [Complete]
  [ ] - QA Status: [Not Started]
  [ ] - User Verification Status: [Not Started]
""")

        tasks = task_parser.parse_tasks_with_structure(str(tasks_file))
        assert tasks[0].dev_status == "Complete"
        assert tasks[0].qa_status == "Not Started"

        # Step 2: Verifier finds issues and updates QA Status to Failed
        tasks_file.write_text("""
[ ] - [[Task 1: Implement form validation]]
  [x] - Dev Status: [Complete]
  [x] - QA Status: [Failed]
  [ ] - User Verification Status: [Not Started]
""")

        tasks = task_parser.parse_tasks_with_structure(str(tasks_file))
        assert tasks[0].qa_status == "Failed"
        assert tasks[0].qa_status_checked == True

        # Step 3: Validate FAIL status (hook should block and request implementer)
        verifier_response = "Found critical bug: email validation missing. STATUS: FAIL"
        is_valid, error = verification_complete.validate_qa_status_for_fail(tasks[0], verifier_response)

        assert is_valid == False
        assert "Re-invoke the \"implementer\"" in error
        assert "Do NOT make fixes yourself" in error
        assert "email validation missing" in error  # Report excerpt included

        # Step 4: Implementer fixes the issue, resets QA Status
        tasks_file.write_text("""
[ ] - [[Task 1: Implement form validation]]
  [x] - Dev Status: [Complete]
  [ ] - QA Status: [Not Started]
  [ ] - User Verification Status: [Not Started]
""")

        tasks = task_parser.parse_tasks_with_structure(str(tasks_file))
        assert tasks[0].qa_status == "Not Started"
        assert tasks[0].qa_status_checked == False

        # Step 5: Verifier re-runs and this time passes
        tasks_file.write_text("""
[ ] - [[Task 1: Implement form validation]]
  [x] - Dev Status: [Complete]
  [x] - QA Status: [Complete]
  [ ] - User Verification Status: [Not Started]
""")

        tasks = task_parser.parse_tasks_with_structure(str(tasks_file))
        assert tasks[0].qa_status == "Complete"
        assert tasks[0].qa_status_checked == True

        # Step 6: Validate PASS status (should succeed)
        is_valid, error = verification_complete.validate_qa_status_for_pass(tasks[0], "STATUS: PASS")
        assert is_valid == True


class TestMultipleFixIterations:
    """Test handling multiple rounds of fixes (T055 part 3)."""

    def test_multiple_fail_fix_cycles(self, tmp_path):
        """Test multiple rounds of fail → fix → verify."""
        tasks_file = tmp_path / "tasks.md"

        iterations = [
            {
                "status": "Failed",
                "response": "Issue 1: Missing input validation. STATUS: FAIL",
                "should_block": True
            },
            {
                "status": "Failed",
                "response": "Issue 2: Error handling incomplete. STATUS: FAIL",
                "should_block": True
            },
            {
                "status": "Complete",
                "response": "All issues resolved. STATUS: PASS",
                "should_block": False
            }
        ]

        for iteration in iterations:
            # Update tasks file with current status
            tasks_file.write_text(f"""
[ ] - [[Task 1: Complex feature]]
  [x] - Dev Status: [Complete]
  [x] - QA Status: [{iteration['status']}]
  [ ] - User Verification Status: [Not Started]
""")

            tasks = task_parser.parse_tasks_with_structure(str(tasks_file))

            if iteration['status'] == "Complete":
                is_valid, error = verification_complete.validate_qa_status_for_pass(
                    tasks[0], iteration['response']
                )
                assert is_valid == (not iteration['should_block'])
            else:
                is_valid, error = verification_complete.validate_qa_status_for_fail(
                    tasks[0], iteration['response']
                )
                assert is_valid == (not iteration['should_block'])
                assert "Re-invoke the \"implementer\"" in error


class TestVerifierMissesUpdate:
    """Test handling when verifier forgets to update QA Status."""

    def test_verifier_reports_pass_but_no_update(self, tmp_path):
        """Test when verifier reports PASS but doesn't update tasks file."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("""
[ ] - [[Task 1: Test task]]
  [x] - Dev Status: [Complete]
  [ ] - QA Status: [Not Started]
  [ ] - User Verification Status: [Not Started]
""")

        tasks = task_parser.parse_tasks_with_structure(str(tasks_file))

        # Verifier response says PASS but file not updated
        verifier_response = "All checks passed. STATUS: PASS"
        is_valid, error = verification_complete.validate_qa_status_for_pass(tasks[0], verifier_response)

        assert is_valid == False
        assert "not properly updated" in error
        assert "Re-invoke the \"verifier\"" in error
        assert "Both the status value AND checkbox must be updated" in error

    def test_verifier_reports_fail_but_no_update(self, tmp_path):
        """Test when verifier reports FAIL but doesn't update tasks file."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("""
[ ] - [[Task 1: Test task]]
  [x] - Dev Status: [Complete]
  [ ] - QA Status: [Not Started]
  [ ] - User Verification Status: [Not Started]
""")

        tasks = task_parser.parse_tasks_with_structure(str(tasks_file))

        # Verifier response says FAIL but file not updated
        verifier_response = "Found issues. STATUS: FAIL"
        is_valid, error = verification_complete.validate_qa_status_for_fail(tasks[0], verifier_response)

        assert is_valid == False
        assert "reported FAIL but QA Status not updated" in error
        assert "Re-invoke the \"verifier\"" in error


class TestPartialUpdatesInWorkflow:
    """Test partial update scenarios in workflow context."""

    def test_verifier_only_checks_checkbox(self, tmp_path):
        """Test when verifier only checks checkbox but doesn't update value."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("""
[ ] - [[Task 1: Test task]]
  [x] - Dev Status: [Complete]
  [x] - QA Status: [Not Started]
  [ ] - User Verification Status: [Not Started]
""")

        tasks = task_parser.parse_tasks_with_structure(str(tasks_file))

        # QA checkbox is checked but status still "Not Started"
        assert tasks[0].qa_status_checked == True
        assert tasks[0].qa_status == "Not Started"

        verifier_response = "STATUS: PASS"
        is_valid, error = verification_complete.validate_qa_status_for_pass(tasks[0], verifier_response)

        assert is_valid == False
        assert "checked the QA Status checkbox but didn't update status value" in error
        assert "Update the QA Status value to [Complete]" in error

    def test_verifier_only_updates_value(self, tmp_path):
        """Test when verifier only updates value but doesn't check checkbox."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("""
[ ] - [[Task 1: Test task]]
  [x] - Dev Status: [Complete]
  [ ] - QA Status: [Complete]
  [ ] - User Verification Status: [Not Started]
""")

        tasks = task_parser.parse_tasks_with_structure(str(tasks_file))

        # QA status is "Complete" but checkbox not checked
        assert tasks[0].qa_status_checked == False
        assert tasks[0].qa_status == "Complete"

        verifier_response = "STATUS: PASS"
        is_valid, error = verification_complete.validate_qa_status_for_pass(tasks[0], verifier_response)

        assert is_valid == False
        assert "forgot to check the checkbox" in error
        assert "Change the [ ] to [x]" in error


class TestTaskMatching:
    """Test task matching in workflow context."""

    def test_verify_correct_task_in_multi_task_file(self, tmp_path):
        """Test that correct task is identified in file with multiple tasks."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("""
[ ] - [[Task 1: First feature]]
  [x] - Dev Status: [Complete]
  [ ] - QA Status: [Not Started]

[ ] - [[Task 2: Second feature]]
  [x] - Dev Status: [Complete]
  [x] - QA Status: [Complete]

[ ] - [[Task 3: Third feature]]
  [ ] - Dev Status: [Not Started]
  [ ] - QA Status: [Not Started]
""")

        tasks = task_parser.parse_tasks_with_structure(str(tasks_file))
        assert len(tasks) == 3

        # Find Task 2 (the one that was verified)
        prompt = "Verify Task 2 implementation"
        matched_task = task_parser.find_matching_task(prompt, tasks)

        assert matched_task is not None
        assert matched_task.task_id == "Task 2"
        assert matched_task.qa_status == "Complete"
        assert matched_task.qa_status_checked == True

        # Validate Task 2's QA Status
        is_valid, error = verification_complete.validate_qa_status_for_pass(matched_task, "STATUS: PASS")
        assert is_valid == True


class TestErrorRecovery:
    """Test error recovery scenarios."""

    def test_unclear_verification_verdict(self, tmp_path):
        """Test when verifier doesn't provide clear PASS/FAIL."""
        verifier_response = "I checked the implementation and noted some observations."

        result = verification_complete.determine_verification_result(verifier_response)
        assert result is None

    def test_mismatched_verdict_and_status(self, tmp_path):
        """Test when verdict doesn't match QA Status (T053)."""
        tasks_file = tmp_path / "tasks.md"

        # Verifier said PASS but marked status as Failed
        tasks_file.write_text("""
[ ] - [[Task 1: Test task]]
  [x] - Dev Status: [Complete]
  [x] - QA Status: [Failed]
  [ ] - User Verification Status: [Not Started]
""")

        tasks = task_parser.parse_tasks_with_structure(str(tasks_file))

        verifier_response = "All tests passed. STATUS: PASS"
        is_valid, error = verification_complete.validate_qa_status_for_pass(tasks[0], verifier_response)

        # Should fail because status is "Failed" but verdict is PASS
        assert is_valid == False


class TestCheckboxStateTracking:
    """Test checkbox state tracking throughout workflow."""

    def test_checkbox_states_tracked_correctly(self, tmp_path):
        """Test that checkbox states are accurately tracked."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("""
[ ] - [[Task 1: Test all checkbox combinations]]
  [x] - Dev Status: [Complete]
  [X] - QA Status: [Complete]
  [ ] - User Verification Status: [Not Started]
""")

        tasks = task_parser.parse_tasks_with_structure(str(tasks_file))

        assert len(tasks) == 1
        assert tasks[0].dev_status_checked == True
        assert tasks[0].qa_status_checked == True  # Uppercase X should work
        assert tasks[0].user_verification_checked == False

    def test_checkbox_required_for_complete_status(self, tmp_path):
        """Test that checkbox must be checked when marking status Complete."""
        tasks_file = tmp_path / "tasks.md"

        # Status is Complete but checkbox not checked - visually inconsistent
        tasks_file.write_text("""
[ ] - [[Task 1: Test task]]
  [x] - Dev Status: [Complete]
  [ ] - QA Status: [Complete]
  [ ] - User Verification Status: [Not Started]
""")

        tasks = task_parser.parse_tasks_with_structure(str(tasks_file))

        # This should be caught by validation
        is_valid, error = verification_complete.validate_qa_status_for_pass(tasks[0], "STATUS: PASS")
        assert is_valid == False
        assert "forgot to check the checkbox" in error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
