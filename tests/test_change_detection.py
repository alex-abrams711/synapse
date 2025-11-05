#!/usr/bin/env python3
"""Unit tests for change_detection module."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import subprocess

# Add the hooks directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'resources', 'workflows', 'feature-implementation', 'hooks'))

from change_detection import (
    get_changed_files_from_git,
    normalize_path,
    get_affected_projects,
    get_verbose_detection_info
)


class TestGetChangedFilesFromGit(unittest.TestCase):
    """Test get_changed_files_from_git function."""

    @patch('subprocess.run')
    def test_uncommitted_changes(self, mock_run):
        """Test detection of uncommitted changes."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "backend/main.py\nfrontend/index.js\n"
        mock_run.return_value = mock_result

        files = get_changed_files_from_git("uncommitted")

        self.assertEqual(files, ["backend/main.py", "frontend/index.js"])
        mock_run.assert_called_once()
        self.assertIn("git", mock_run.call_args[0][0])
        self.assertIn("diff", mock_run.call_args[0][0])

    @patch('subprocess.run')
    def test_since_main_changes(self, mock_run):
        """Test detection of changes since main branch."""
        # First call checks if origin/main exists
        mock_main_check = MagicMock()
        mock_main_check.returncode = 0

        # Second call gets the diff
        mock_diff_result = MagicMock()
        mock_diff_result.returncode = 0
        mock_diff_result.stdout = "backend/api.py\nshared-utils/utils.py\n"

        mock_run.side_effect = [mock_main_check, mock_diff_result]

        files = get_changed_files_from_git("since_main")

        self.assertEqual(files, ["backend/api.py", "shared-utils/utils.py"])
        self.assertEqual(mock_run.call_count, 2)

    @patch('subprocess.run')
    def test_no_changes(self, mock_run):
        """Test when there are no changes."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        files = get_changed_files_from_git("uncommitted")

        self.assertEqual(files, [])

    @patch('subprocess.run')
    def test_git_command_fails(self, mock_run):
        """Test when git command fails."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        files = get_changed_files_from_git("uncommitted")

        self.assertEqual(files, [])

    @patch('subprocess.run')
    def test_git_timeout(self, mock_run):
        """Test when git command times out."""
        mock_run.side_effect = subprocess.TimeoutExpired("git", 5)

        files = get_changed_files_from_git("uncommitted")

        self.assertEqual(files, [])

    @patch('subprocess.run')
    def test_git_not_installed(self, mock_run):
        """Test when git is not installed."""
        mock_run.side_effect = FileNotFoundError()

        files = get_changed_files_from_git("uncommitted")

        self.assertEqual(files, [])

    @patch('subprocess.run')
    def test_all_changes_method(self, mock_run):
        """Test detection with all_changes method (git status)."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        # Git status porcelain format: XY filename (2 status chars + space + filename)
        mock_result.stdout = " M backend/main.py\n?? frontend/new.js\nA  shared-utils/test.py\n"
        mock_run.return_value = mock_result

        files = get_changed_files_from_git("all_changes")

        # The implementation skips first 3 characters (status + space)
        self.assertEqual(files, ["backend/main.py", "frontend/new.js", "shared-utils/test.py"])

    @patch('subprocess.run')
    def test_renamed_files(self, mock_run):
        """Test detection of renamed files in all_changes mode."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "R  backend/old.py -> backend/new.py\n"
        mock_run.return_value = mock_result

        files = get_changed_files_from_git("all_changes")

        # Should extract the new filename
        self.assertEqual(files, ["backend/new.py"])


class TestNormalizePath(unittest.TestCase):
    """Test normalize_path function."""

    def test_forward_slashes(self):
        """Test path with forward slashes."""
        result = normalize_path("backend/src/main.py")
        self.assertEqual(result, "backend/src/main.py")

    def test_backslashes(self):
        """Test path with backslashes (Windows)."""
        result = normalize_path("backend\\src\\main.py")
        self.assertEqual(result, "backend/src/main.py")

    def test_mixed_slashes(self):
        """Test path with mixed slashes."""
        result = normalize_path("backend/src\\utils\\helper.py")
        self.assertEqual(result, "backend/src/utils/helper.py")

    def test_leading_dot_slash(self):
        """Test path with leading ./"""
        result = normalize_path("./backend/main.py")
        self.assertEqual(result, "backend/main.py")

    def test_empty_path(self):
        """Test empty path."""
        result = normalize_path("")
        self.assertEqual(result, "")


class TestGetAffectedProjects(unittest.TestCase):
    """Test get_affected_projects function."""

    def setUp(self):
        """Set up test fixtures."""
        self.projects_config = {
            "backend": {
                "directory": "backend/",
                "commands": {}
            },
            "frontend": {
                "directory": "frontend/",
                "commands": {}
            },
            "shared-utils": {
                "directory": "shared-utils/",
                "commands": {}
            }
        }

    @patch('change_detection.get_changed_files_from_git')
    def test_single_project_change(self, mock_get_files):
        """Test when only one project has changes."""
        mock_get_files.return_value = ["backend/main.py", "backend/test.py"]
        optimization_config = {
            "check_affected_only": True,
            "detection_method": "uncommitted"
        }

        affected, reason = get_affected_projects(self.projects_config, optimization_config)

        self.assertEqual(affected, {"backend"})
        self.assertIn("git detection", reason)

    @patch('change_detection.get_changed_files_from_git')
    def test_multiple_project_changes(self, mock_get_files):
        """Test when multiple projects have changes."""
        mock_get_files.return_value = [
            "backend/main.py",
            "frontend/index.js",
            "shared-utils/utils.py"
        ]
        optimization_config = {
            "check_affected_only": True,
            "detection_method": "uncommitted"
        }

        affected, reason = get_affected_projects(self.projects_config, optimization_config)

        self.assertEqual(affected, {"backend", "frontend", "shared-utils"})
        self.assertIn("git detection", reason)

    @patch('change_detection.get_changed_files_from_git')
    def test_no_changes_fallback(self, mock_get_files):
        """Test fallback to all projects when no changes detected."""
        mock_get_files.return_value = []
        optimization_config = {
            "check_affected_only": True,
            "detection_method": "uncommitted",
            "fallback_to_all": True
        }

        affected, reason = get_affected_projects(self.projects_config, optimization_config)

        self.assertEqual(affected, {"backend", "frontend", "shared-utils"})
        self.assertIn("no changes detected", reason)
        self.assertIn("fallback", reason)

    @patch('change_detection.get_changed_files_from_git')
    def test_no_changes_no_fallback(self, mock_get_files):
        """Test skipping when no changes and fallback disabled."""
        mock_get_files.return_value = []
        optimization_config = {
            "check_affected_only": True,
            "detection_method": "uncommitted",
            "fallback_to_all": False
        }

        affected, reason = get_affected_projects(self.projects_config, optimization_config)

        self.assertEqual(affected, set())
        self.assertIn("no changes detected", reason)
        self.assertIn("skip", reason)

    def test_optimization_disabled(self):
        """Test when optimization is disabled."""
        optimization_config = {
            "check_affected_only": False
        }

        affected, reason = get_affected_projects(self.projects_config, optimization_config)

        self.assertEqual(affected, {"backend", "frontend", "shared-utils"})
        self.assertIn("optimization disabled", reason)

    @patch.dict(os.environ, {'SYNAPSE_CHECK_ALL_PROJECTS': '1'})
    def test_env_var_override(self):
        """Test environment variable override."""
        optimization_config = {
            "check_affected_only": True
        }

        affected, reason = get_affected_projects(self.projects_config, optimization_config)

        self.assertEqual(affected, {"backend", "frontend", "shared-utils"})
        self.assertIn("SYNAPSE_CHECK_ALL_PROJECTS", reason)

    @patch('change_detection.get_changed_files_from_git')
    def test_force_check_projects(self, mock_get_files):
        """Test force-check projects are always included."""
        mock_get_files.return_value = ["backend/main.py"]
        optimization_config = {
            "check_affected_only": True,
            "detection_method": "uncommitted",
            "force_check_projects": ["shared-utils"]
        }

        affected, reason = get_affected_projects(self.projects_config, optimization_config)

        # Should include both backend (changed) and shared-utils (forced)
        self.assertEqual(affected, {"backend", "shared-utils"})
        self.assertIn("force-check", reason)

    @patch('change_detection.get_changed_files_from_git')
    def test_changes_outside_projects(self, mock_get_files):
        """Test when changes are outside any project directory."""
        mock_get_files.return_value = ["README.md", ".gitignore"]
        optimization_config = {
            "check_affected_only": True,
            "detection_method": "uncommitted",
            "fallback_to_all": True
        }

        affected, reason = get_affected_projects(self.projects_config, optimization_config)

        # Should fallback to all projects
        self.assertEqual(affected, {"backend", "frontend", "shared-utils"})
        self.assertIn("no projects matched", reason)

    @patch.dict(os.environ, {'SYNAPSE_DETECTION_METHOD': 'all_changes'})
    @patch('change_detection.get_changed_files_from_git')
    def test_detection_method_env_override(self, mock_get_files):
        """Test detection method can be overridden by environment variable."""
        mock_get_files.return_value = ["backend/main.py"]
        optimization_config = {
            "check_affected_only": True,
            "detection_method": "uncommitted"  # Should be overridden
        }

        affected, reason = get_affected_projects(self.projects_config, optimization_config)

        # Verify the env var method was used
        mock_get_files.assert_called_with("all_changes")

    @patch('change_detection.get_changed_files_from_git')
    def test_path_with_subdirectories(self, mock_get_files):
        """Test matching files in subdirectories."""
        mock_get_files.return_value = [
            "backend/src/api/handlers.py",
            "backend/tests/test_api.py"
        ]
        optimization_config = {
            "check_affected_only": True,
            "detection_method": "uncommitted"
        }

        affected, reason = get_affected_projects(self.projects_config, optimization_config)

        self.assertEqual(affected, {"backend"})


class TestGetVerboseDetectionInfo(unittest.TestCase):
    """Test get_verbose_detection_info function."""

    def setUp(self):
        """Set up test fixtures."""
        self.projects_config = {
            "backend": {"directory": "backend/"},
            "frontend": {"directory": "frontend/"}
        }

    def test_verbose_info_format(self):
        """Test verbose detection info formatting."""
        changed_files = ["backend/main.py", "backend/test.py", "frontend/index.js"]
        affected_projects = {"backend", "frontend"}

        info = get_verbose_detection_info(changed_files, self.projects_config, affected_projects)

        # Check that key information is included
        self.assertIn("Changed files: 3", info)
        self.assertIn("Affected projects: 2/2", info)
        self.assertIn("backend/main.py", info)
        self.assertIn("backend (backend/): 2 file(s)", info)
        self.assertIn("frontend (frontend/): 1 file(s)", info)

    def test_verbose_info_with_many_files(self):
        """Test verbose info truncates long file lists."""
        changed_files = [f"backend/file{i}.py" for i in range(15)]
        affected_projects = {"backend"}

        info = get_verbose_detection_info(changed_files, self.projects_config, affected_projects)

        # Should show first 10 and indicate more
        self.assertIn("... and 5 more", info)


if __name__ == '__main__':
    unittest.main()
