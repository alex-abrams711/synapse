#!/usr/bin/env python3
"""Tests for strict lint level warning detection in post-tool-use hook"""
import sys
import os
import unittest
import importlib.util
from unittest.mock import Mock, patch
from subprocess import CompletedProcess

# Dynamically import post_tool_use from hooks directory
hooks_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'workflows', 'feature-implementation', 'hooks')
post_tool_use_path = os.path.join(hooks_path, 'post-tool-use.py')

spec = importlib.util.spec_from_file_location("post_tool_use", post_tool_use_path)
post_tool_use = importlib.util.module_from_spec(spec)
sys.modules['post_tool_use'] = post_tool_use
spec.loader.exec_module(post_tool_use)

run_quality_command = post_tool_use.run_quality_command


class TestStrictLintWarnings(unittest.TestCase):
    """Test that strict lint mode properly detects warnings"""

    def test_strict_mode_fails_on_warnings_exit_0(self):
        """Strict mode should fail when linter exits 0 but has warnings in output"""
        # Simulate linter output with warnings but exit code 0 (common with ESLint, Ruff)
        mock_result = CompletedProcess(
            args=['ruff', 'check'],
            returncode=0,
            stdout="file.py:10:5: Warning: Line too long (100 > 88 characters)\n2 warnings found\n",
            stderr=""
        )

        with patch('post_tool_use.subprocess.run', return_value=mock_result):
            status, output = run_quality_command("lint", "ruff check", lint_level="strict")

        # Should FAIL in strict mode because warnings were found
        assert status == "FAIL", f"Expected FAIL but got {status}"
        assert "warning" in output.lower()

    def test_strict_mode_fails_on_warnings_with_colon(self):
        """Strict mode should detect 'warning:' format"""
        mock_result = CompletedProcess(
            args=['eslint', '.'],
            returncode=0,
            stdout="/path/file.js\n  1:5  warning: Use const instead of var  no-var\n",
            stderr=""
        )

        with patch('post_tool_use.subprocess.run', return_value=mock_result):
            status, output = run_quality_command("lint", "eslint .", lint_level="strict")

        assert status == "FAIL"

    def test_strict_mode_fails_on_warnings_found_text(self):
        """Strict mode should detect 'warnings found' text"""
        mock_result = CompletedProcess(
            args=['pylint', 'src'],
            returncode=0,
            stdout="Your code has been rated at 9.5/10\n\n5 warnings found\n",
            stderr=""
        )

        with patch('post_tool_use.subprocess.run', return_value=mock_result):
            status, output = run_quality_command("lint", "pylint src", lint_level="strict")

        assert status == "FAIL"

    def test_strict_mode_passes_with_no_warnings(self):
        """Strict mode should pass when no warnings in output"""
        mock_result = CompletedProcess(
            args=['ruff', 'check'],
            returncode=0,
            stdout="All checks passed!\n",
            stderr=""
        )

        with patch('post_tool_use.subprocess.run', return_value=mock_result):
            status, output = run_quality_command("lint", "ruff check", lint_level="strict")

        # Should PASS - no warnings detected
        assert status == "PASS", f"Expected PASS but got {status}"

    def test_strict_mode_fails_on_nonzero_exit(self):
        """Strict mode should fail on non-zero exit code regardless of output"""
        mock_result = CompletedProcess(
            args=['ruff', 'check'],
            returncode=1,
            stdout="Error: Syntax error in file.py\n",
            stderr=""
        )

        with patch('post_tool_use.subprocess.run', return_value=mock_result):
            status, output = run_quality_command("lint", "ruff check", lint_level="strict")

        assert status == "FAIL"

    def test_flexible_mode_allows_warnings_exit_0(self):
        """Flexible mode should allow warnings with exit code 0"""
        mock_result = CompletedProcess(
            args=['ruff', 'check'],
            returncode=0,
            stdout="file.py:10:5: Warning: Line too long\n2 warnings found\n",
            stderr=""
        )

        with patch('post_tool_use.subprocess.run', return_value=mock_result):
            status, output = run_quality_command("lint", "ruff check", lint_level="flexible")

        # Should PASS in flexible mode even with warnings
        assert status == "PASS", f"Expected PASS in flexible mode but got {status}"

    def test_flexible_mode_allows_warnings_exit_1(self):
        """Flexible mode should allow warnings with exit code 1"""
        mock_result = CompletedProcess(
            args=['ruff', 'check'],
            returncode=1,
            stdout="file.py:10:5: Warning: Line too long\n",
            stderr=""
        )

        with patch('post_tool_use.subprocess.run', return_value=mock_result):
            status, output = run_quality_command("lint", "ruff check", lint_level="flexible")

        # Should PASS - flexible mode allows exit code 1 (warnings)
        assert status == "PASS", f"Expected PASS in flexible mode but got {status}"

    def test_flexible_mode_fails_on_exit_2(self):
        """Flexible mode should fail on exit code 2 (typically critical errors)"""
        mock_result = CompletedProcess(
            args=['ruff', 'check'],
            returncode=2,
            stdout="Fatal error: Configuration file not found\n",
            stderr=""
        )

        with patch('post_tool_use.subprocess.run', return_value=mock_result):
            status, output = run_quality_command("lint", "ruff check", lint_level="flexible")

        # Should FAIL on exit code 2 even in flexible mode
        assert status == "FAIL"

    def test_strict_mode_detects_warn_bracket_format(self):
        """Strict mode should detect [warn] format"""
        mock_result = CompletedProcess(
            args=['custom-linter', '.'],
            returncode=0,
            stdout="[WARN] Unused import at line 5\n",
            stderr=""
        )

        with patch('post_tool_use.subprocess.run', return_value=mock_result):
            status, output = run_quality_command("lint", "custom-linter .", lint_level="strict")

        assert status == "FAIL"

    def test_strict_mode_detects_warning_in_parentheses(self):
        """Strict mode should detect (warning) format"""
        mock_result = CompletedProcess(
            args=['linter', 'check'],
            returncode=0,
            stdout="file.js:10 (warning) Prefer const over let\n",
            stderr=""
        )

        with patch('post_tool_use.subprocess.run', return_value=mock_result):
            status, output = run_quality_command("lint", "linter check", lint_level="strict")

        assert status == "FAIL"

    def test_strict_mode_case_insensitive(self):
        """Strict mode warning detection should be case-insensitive"""
        mock_result = CompletedProcess(
            args=['linter', 'check'],
            returncode=0,
            stdout="File.py:10: WARNING: Unused variable\n",
            stderr=""
        )

        with patch('post_tool_use.subprocess.run', return_value=mock_result):
            status, output = run_quality_command("lint", "linter check", lint_level="strict")

        assert status == "FAIL"

    def test_strict_mode_checks_stderr_too(self):
        """Strict mode should check both stdout and stderr for warnings"""
        mock_result = CompletedProcess(
            args=['linter', 'check'],
            returncode=0,
            stdout="All checks completed\n",
            stderr="Warning: Deprecated API usage detected\n"
        )

        with patch('post_tool_use.subprocess.run', return_value=mock_result):
            status, output = run_quality_command("lint", "linter check", lint_level="strict")

        assert status == "FAIL"


if __name__ == '__main__':
    unittest.main()
