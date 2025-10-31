"""Integration tests for verification workflow and hook logic."""
import pytest
import tempfile
import os
import json
import sys
from pathlib import Path

# Add hooks directory to Python path
hooks_dir = Path(__file__).parent.parent / "resources" / "workflows" / "feature-implementation" / "hooks"
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


class TestDetermineVerificationResult:
    """Test verification result extraction from agent responses."""

    def test_detect_pass_status(self):
        """Test detecting PASS verdict."""
        response = """
        Verification Report

        All tests passed successfully.

        STATUS: PASS
        """

        result = verification_complete.determine_verification_result(response)
        assert result == "PASS"

    def test_detect_fail_status(self):
        """Test detecting FAIL verdict."""
        response = """
        Verification Report

        Found issues during testing.

        STATUS: FAIL
        """

        result = verification_complete.determine_verification_result(response)
        assert result == "FAIL"

    def test_detect_fail_from_error_indicators(self):
        """Test detecting FAIL from error indicators."""
        response = """
        Found critical error during verification.
        The system failed to handle edge cases.
        """

        result = verification_complete.determine_verification_result(response)
        assert result == "FAIL"

    def test_unclear_verdict(self):
        """Test when verdict is unclear."""
        response = """
        Verification complete.
        Some observations noted.
        """

        result = verification_complete.determine_verification_result(response)
        assert result is None


class TestValidateQAStatusForPass:
    """Test QA Status validation for PASS verdicts."""

    def test_pass_with_correct_status_and_checkbox(self):
        """Test PASS with both status value and checkbox correct (T049)."""
        task = Task(
            task_id="Task 1",
            task_description="Test task",
            dev_status="Complete",
            qa_status="Complete",
            user_verification_status="Not Started",
            dev_status_checked=True,
            qa_status_checked=True,
            user_verification_checked=False,
            keywords=["test"],
            line_number=1,
            qa_status_line_number=3
        )

        is_valid, error = verification_complete.validate_qa_status_for_pass(task, "")
        assert is_valid == True
        assert error == ""

    def test_pass_with_alternate_status_values(self):
        """Test PASS with alternate valid status values."""
        for status in ["Complete", "complete", "Passed", "passed", "Done", "done"]:
            task = Task(
                task_id="Task 1",
                task_description="Test task",
                dev_status="Complete",
                qa_status=status,
                user_verification_status="Not Started",
                dev_status_checked=True,
                qa_status_checked=True,
                user_verification_checked=False,
                keywords=["test"],
                line_number=1,
                qa_status_line_number=3
            )

            is_valid, error = verification_complete.validate_qa_status_for_pass(task, "")
            assert is_valid == True, f"Status '{status}' should be valid"

    def test_pass_missing_both_updates(self):
        """Test PASS when neither checkbox nor status updated (T051 + T052)."""
        task = Task(
            task_id="Task 1",
            task_description="Test task",
            dev_status="Complete",
            qa_status="Not Started",
            user_verification_status="Not Started",
            dev_status_checked=True,
            qa_status_checked=False,
            user_verification_checked=False,
            keywords=["test"],
            line_number=1,
            qa_status_line_number=3
        )

        is_valid, error = verification_complete.validate_qa_status_for_pass(task, "")
        assert is_valid == False
        assert "not properly updated" in error
        assert "REQUIRED ACTION" in error
        assert "Re-invoke the \"verifier\"" in error
        assert "Both the status value AND checkbox must be updated" in error

    def test_pass_missing_status_value(self):
        """Test PASS when checkbox checked but status value wrong (T051)."""
        task = Task(
            task_id="Task 1",
            task_description="Test task",
            dev_status="Complete",
            qa_status="Not Started",
            user_verification_status="Not Started",
            dev_status_checked=True,
            qa_status_checked=True,
            user_verification_checked=False,
            keywords=["test"],
            line_number=1,
            qa_status_line_number=3
        )

        is_valid, error = verification_complete.validate_qa_status_for_pass(task, "")
        assert is_valid == False
        assert "checked the QA Status checkbox but didn't update status value" in error
        assert "Update the QA Status value to [Complete]" in error
        assert "checkbox is already checked" in error

    def test_pass_missing_checkbox(self):
        """Test PASS when status value correct but checkbox not checked (T052)."""
        task = Task(
            task_id="Task 1",
            task_description="Test task",
            dev_status="Complete",
            qa_status="Complete",
            user_verification_status="Not Started",
            dev_status_checked=True,
            qa_status_checked=False,
            user_verification_checked=False,
            keywords=["test"],
            line_number=1,
            qa_status_line_number=3
        )

        is_valid, error = verification_complete.validate_qa_status_for_pass(task, "")
        assert is_valid == False
        assert "forgot to check the checkbox" in error
        assert "Change the [ ] to [x]" in error
        assert "marks the QA step as visually complete" in error


class TestValidateQAStatusForFail:
    """Test QA Status validation for FAIL verdicts."""

    def test_fail_with_correct_status_and_checkbox(self):
        """Test FAIL with both status value and checkbox correct (T050)."""
        task = Task(
            task_id="Task 1",
            task_description="Test task",
            dev_status="Complete",
            qa_status="Failed",
            user_verification_status="Not Started",
            dev_status_checked=True,
            qa_status_checked=True,
            user_verification_checked=False,
            keywords=["test"],
            line_number=1,
            qa_status_line_number=3
        )

        agent_response = "Verification found issues in the implementation."
        is_valid, error = verification_complete.validate_qa_status_for_fail(task, agent_response)

        # Should be invalid because we need to block and re-invoke implementer
        assert is_valid == False
        assert "Verification FAILED" in error
        assert "Re-invoke the \"implementer\"" in error
        assert "Do NOT make fixes yourself" in error

    def test_fail_with_alternate_status_values(self):
        """Test FAIL with alternate valid status values."""
        for status in ["Failed", "failed", "In Progress", "in progress", "Needs Work", "needs work"]:
            task = Task(
                task_id="Task 1",
                task_description="Test task",
                dev_status="Complete",
                qa_status=status,
                user_verification_status="Not Started",
                dev_status_checked=True,
                qa_status_checked=True,
                user_verification_checked=False,
                keywords=["test"],
                line_number=1,
                qa_status_line_number=3
            )

            is_valid, error = verification_complete.validate_qa_status_for_fail(task, "Issues found")
            assert is_valid == False  # Always false for FAIL to trigger implementer
            assert "Re-invoke the \"implementer\"" in error

    def test_fail_missing_both_updates(self):
        """Test FAIL when neither checkbox nor status updated."""
        task = Task(
            task_id="Task 1",
            task_description="Test task",
            dev_status="Complete",
            qa_status="Not Started",
            user_verification_status="Not Started",
            dev_status_checked=True,
            qa_status_checked=False,
            user_verification_checked=False,
            keywords=["test"],
            line_number=1,
            qa_status_line_number=3
        )

        is_valid, error = verification_complete.validate_qa_status_for_fail(task, "")
        assert is_valid == False
        assert "reported FAIL but QA Status not updated" in error
        assert "Update the task's QA Status field to [Failed]" in error
        assert "Check the checkbox on the QA Status line" in error

    def test_fail_missing_status_value(self):
        """Test FAIL when checkbox checked but status value wrong (T053)."""
        task = Task(
            task_id="Task 1",
            task_description="Test task",
            dev_status="Complete",
            qa_status="Not Started",
            user_verification_status="Not Started",
            dev_status_checked=True,
            qa_status_checked=True,
            user_verification_checked=False,
            keywords=["test"],
            line_number=1,
            qa_status_line_number=3
        )

        is_valid, error = verification_complete.validate_qa_status_for_fail(task, "")
        assert is_valid == False
        assert "checked the QA Status checkbox but didn't update status value" in error
        assert "Update the QA Status value to [Failed]" in error

    def test_fail_missing_checkbox(self):
        """Test FAIL when status value correct but checkbox not checked (T054)."""
        task = Task(
            task_id="Task 1",
            task_description="Test task",
            dev_status="Complete",
            qa_status="Failed",
            user_verification_status="Not Started",
            dev_status_checked=True,
            qa_status_checked=False,
            user_verification_checked=False,
            keywords=["test"],
            line_number=1,
            qa_status_line_number=3
        )

        is_valid, error = verification_complete.validate_qa_status_for_fail(task, "")
        assert is_valid == False
        assert "forgot to check the checkbox" in error
        assert "Change the [ ] to [x]" in error

    def test_fail_includes_verification_report_excerpt(self):
        """Test that FAIL error includes verification report excerpt."""
        task = Task(
            task_id="Task 1",
            task_description="Test task",
            dev_status="Complete",
            qa_status="Failed",
            user_verification_status="Not Started",
            dev_status_checked=True,
            qa_status_checked=True,
            user_verification_checked=False,
            keywords=["test"],
            line_number=1,
            qa_status_line_number=3
        )

        agent_response = "Found critical bug in the implementation: the login form doesn't validate email format"
        is_valid, error = verification_complete.validate_qa_status_for_fail(task, agent_response)

        assert is_valid == False
        assert "VERIFICATION REPORT EXCERPT:" in error
        assert "login form doesn't validate email format" in error


class TestPartialUpdates:
    """Test handling of partial updates (T054)."""

    def test_pass_only_checkbox_updated(self):
        """Test PASS with only checkbox updated."""
        task = Task(
            task_id="Task 1",
            task_description="Test task",
            dev_status="Complete",
            qa_status="Not Started",
            user_verification_status="Not Started",
            dev_status_checked=True,
            qa_status_checked=True,
            user_verification_checked=False,
            keywords=["test"],
            line_number=1,
            qa_status_line_number=3
        )

        is_valid, error = verification_complete.validate_qa_status_for_pass(task, "")
        assert is_valid == False
        assert "checked the QA Status checkbox but didn't update status value" in error

    def test_pass_only_value_updated(self):
        """Test PASS with only status value updated."""
        task = Task(
            task_id="Task 1",
            task_description="Test task",
            dev_status="Complete",
            qa_status="Complete",
            user_verification_status="Not Started",
            dev_status_checked=True,
            qa_status_checked=False,
            user_verification_checked=False,
            keywords=["test"],
            line_number=1,
            qa_status_line_number=3
        )

        is_valid, error = verification_complete.validate_qa_status_for_pass(task, "")
        assert is_valid == False
        assert "forgot to check the checkbox" in error

    def test_fail_only_checkbox_updated(self):
        """Test FAIL with only checkbox updated."""
        task = Task(
            task_id="Task 1",
            task_description="Test task",
            dev_status="Complete",
            qa_status="Not Started",
            user_verification_status="Not Started",
            dev_status_checked=True,
            qa_status_checked=True,
            user_verification_checked=False,
            keywords=["test"],
            line_number=1,
            qa_status_line_number=3
        )

        is_valid, error = verification_complete.validate_qa_status_for_fail(task, "")
        assert is_valid == False
        assert "checked the QA Status checkbox but didn't update status value" in error

    def test_fail_only_value_updated(self):
        """Test FAIL with only status value updated."""
        task = Task(
            task_id="Task 1",
            task_description="Test task",
            dev_status="Complete",
            qa_status="Failed",
            user_verification_status="Not Started",
            dev_status_checked=True,
            qa_status_checked=False,
            user_verification_checked=False,
            keywords=["test"],
            line_number=1,
            qa_status_line_number=3
        )

        is_valid, error = verification_complete.validate_qa_status_for_fail(task, "")
        assert is_valid == False
        assert "forgot to check the checkbox" in error


class TestErrorMessages:
    """Test that error messages contain helpful information."""

    def test_error_includes_task_id(self):
        """Test that errors include task ID for context."""
        task = Task(
            task_id="T-042",
            task_description="Test task",
            dev_status="Complete",
            qa_status="Not Started",
            user_verification_status="Not Started",
            dev_status_checked=True,
            qa_status_checked=False,
            user_verification_checked=False,
            keywords=["test"],
            line_number=10,
            qa_status_line_number=12
        )

        is_valid, error = verification_complete.validate_qa_status_for_pass(task, "")
        assert "T-042" in error

    def test_error_includes_line_number(self):
        """Test that errors include line numbers."""
        task = Task(
            task_id="Task 1",
            task_description="Test task",
            dev_status="Complete",
            qa_status="Not Started",
            user_verification_status="Not Started",
            dev_status_checked=True,
            qa_status_checked=False,
            user_verification_checked=False,
            keywords=["test"],
            line_number=10,
            qa_status_line_number=12
        )

        is_valid, error = verification_complete.validate_qa_status_for_pass(task, "")
        assert "line 12" in error or "line 10" in error

    def test_error_includes_current_and_expected_status(self):
        """Test that errors show current and expected status."""
        task = Task(
            task_id="Task 1",
            task_description="Test task",
            dev_status="Complete",
            qa_status="Not Started",
            user_verification_status="Not Started",
            dev_status_checked=True,
            qa_status_checked=False,
            user_verification_checked=False,
            keywords=["test"],
            line_number=1,
            qa_status_line_number=3
        )

        is_valid, error = verification_complete.validate_qa_status_for_pass(task, "")
        assert "Not Started" in error  # Current status
        assert "Complete" in error  # Expected status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
