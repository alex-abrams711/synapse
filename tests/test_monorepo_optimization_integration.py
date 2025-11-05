#!/usr/bin/env python3
"""Integration tests for monorepo optimization in hooks."""

import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Add the hooks directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'resources', 'workflows', 'feature-implementation', 'hooks'))

from change_detection import get_affected_projects, get_changed_files_from_git


class TestMonorepoOptimizationIntegration(unittest.TestCase):
    """Integration tests for monorepo optimization."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'monorepo-optimization')
        self.original_cwd = os.getcwd()

        # Load test config
        config_path = os.path.join(self.test_dir, '.synapse', 'config.json')
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.projects_config = self.config['quality-config']['projects']
        self.optimization_config = self.config['quality-config']['optimization']

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)

    @patch('change_detection.get_changed_files_from_git')
    def test_single_project_optimization(self, mock_get_files):
        """Test optimization with single project changed."""
        mock_get_files.return_value = ['backend/main.py', 'backend/test.py']

        affected, reason = get_affected_projects(
            self.projects_config,
            self.optimization_config
        )

        # Should only check backend
        self.assertEqual(affected, {'backend', 'shared-utils'})  # shared-utils is force-checked
        self.assertIn('git detection', reason)

        # Verify shared-utils is always included (force_check_projects)
        self.assertIn('shared-utils', affected)

    @patch('change_detection.get_changed_files_from_git')
    def test_multiple_projects_optimization(self, mock_get_files):
        """Test optimization with multiple projects changed."""
        mock_get_files.return_value = [
            'backend/main.py',
            'frontend/index.js',
            'shared-utils/utils.py'
        ]

        affected, reason = get_affected_projects(
            self.projects_config,
            self.optimization_config
        )

        # Should check all three projects
        self.assertEqual(affected, {'backend', 'frontend', 'shared-utils'})
        self.assertIn('git detection', reason)

    @patch('change_detection.get_changed_files_from_git')
    def test_no_changes_fallback(self, mock_get_files):
        """Test fallback to all projects when no changes."""
        mock_get_files.return_value = []

        affected, reason = get_affected_projects(
            self.projects_config,
            self.optimization_config
        )

        # Should check all projects (fallback)
        self.assertEqual(affected, {'backend', 'frontend', 'shared-utils'})
        self.assertIn('no changes', reason)
        self.assertIn('fallback', reason)

    @patch('change_detection.get_changed_files_from_git')
    def test_force_check_always_included(self, mock_get_files):
        """Test that force-check projects are always included."""
        # Only frontend changed
        mock_get_files.return_value = ['frontend/index.js']

        affected, reason = get_affected_projects(
            self.projects_config,
            self.optimization_config
        )

        # Should include frontend (changed) and shared-utils (forced)
        self.assertIn('frontend', affected)
        self.assertIn('shared-utils', affected)
        self.assertNotIn('backend', affected)

    @patch.dict(os.environ, {'SYNAPSE_CHECK_ALL_PROJECTS': '1'})
    @patch('change_detection.get_changed_files_from_git')
    def test_env_override_disables_optimization(self, mock_get_files):
        """Test that environment variable overrides optimization."""
        mock_get_files.return_value = ['backend/main.py']

        affected, reason = get_affected_projects(
            self.projects_config,
            self.optimization_config
        )

        # Should check all projects despite optimization being enabled
        self.assertEqual(affected, {'backend', 'frontend', 'shared-utils'})
        self.assertIn('SYNAPSE_CHECK_ALL_PROJECTS', reason)

    @patch('change_detection.get_changed_files_from_git')
    def test_root_level_changes_without_force_check(self, mock_get_files):
        """Test fallback when only root-level files changed (no force-check)."""
        mock_get_files.return_value = ['README.md', '.gitignore', 'LICENSE']

        # Use config without force-check
        optimization_config = {
            'check_affected_only': True,
            'detection_method': 'uncommitted',
            'fallback_to_all': True,
            'force_check_projects': []  # No force-check
        }

        affected, reason = get_affected_projects(
            self.projects_config,
            optimization_config
        )

        # Should fallback to all projects (safety)
        self.assertEqual(affected, {'backend', 'frontend', 'shared-utils'})
        self.assertIn('no projects matched', reason)

    @patch('change_detection.get_changed_files_from_git')
    def test_root_level_changes_with_force_check(self, mock_get_files):
        """Test behavior when only root-level files changed (with force-check)."""
        mock_get_files.return_value = ['README.md', '.gitignore', 'LICENSE']

        affected, reason = get_affected_projects(
            self.projects_config,
            self.optimization_config  # Has force_check_projects
        )

        # With force-check projects configured, they are included
        # This is current behavior - force-check happens after detection
        self.assertIn('shared-utils', affected)

    @patch('change_detection.get_changed_files_from_git')
    def test_nested_file_changes(self, mock_get_files):
        """Test detection with deeply nested files."""
        mock_get_files.return_value = [
            'backend/src/api/handlers/user.py',
            'backend/tests/unit/test_handlers.py'
        ]

        affected, reason = get_affected_projects(
            self.projects_config,
            self.optimization_config
        )

        # Should detect backend despite nested paths
        self.assertIn('backend', affected)
        self.assertIn('shared-utils', affected)  # force-checked
        self.assertEqual(len(affected), 2)

    @patch.dict(os.environ, {'SYNAPSE_DETECTION_METHOD': 'since_main'})
    @patch('change_detection.get_changed_files_from_git')
    def test_detection_method_override(self, mock_get_files):
        """Test detection method environment variable override."""
        mock_get_files.return_value = ['backend/main.py']

        affected, reason = get_affected_projects(
            self.projects_config,
            self.optimization_config
        )

        # Verify the overridden method was called
        mock_get_files.assert_called_once_with('since_main')
        self.assertIn('backend', affected)

    def test_config_without_optimization_section(self):
        """Test handling of config without optimization section."""
        projects_config = self.projects_config.copy()
        optimization_config = {}  # No optimization config

        with patch('change_detection.get_changed_files_from_git') as mock_get_files:
            mock_get_files.return_value = ['backend/main.py']

            affected, reason = get_affected_projects(
                projects_config,
                optimization_config
            )

            # Should still work with defaults
            self.assertIn('backend', affected)

    @patch('change_detection.get_changed_files_from_git')
    def test_optimization_disabled_in_config(self, mock_get_files):
        """Test when optimization is explicitly disabled."""
        mock_get_files.return_value = ['backend/main.py']

        optimization_config = self.optimization_config.copy()
        optimization_config['check_affected_only'] = False

        affected, reason = get_affected_projects(
            self.projects_config,
            optimization_config
        )

        # Should check all projects
        self.assertEqual(affected, {'backend', 'frontend', 'shared-utils'})
        self.assertIn('optimization disabled', reason)

    @patch('change_detection.get_changed_files_from_git')
    def test_mixed_path_separators(self, mock_get_files):
        """Test handling of mixed path separators (Windows/Unix)."""
        # Simulate Windows-style paths from git
        mock_get_files.return_value = [
            'backend\\main.py',
            'frontend/index.js'
        ]

        affected, reason = get_affected_projects(
            self.projects_config,
            self.optimization_config
        )

        # Should normalize and detect both projects
        self.assertIn('backend', affected)
        self.assertIn('frontend', affected)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def setUp(self):
        """Set up test environment."""
        self.projects_config = {
            "backend": {"directory": "backend/"},
            "frontend": {"directory": "frontend/"}
        }
        self.optimization_config = {
            "check_affected_only": True,
            "detection_method": "uncommitted",
            "fallback_to_all": True
        }

    @patch('change_detection.get_changed_files_from_git')
    def test_large_number_of_changes(self, mock_get_files):
        """Test handling of large number of changed files."""
        # Simulate 1000 changed files
        large_file_list = [f'backend/file_{i}.py' for i in range(1000)]
        mock_get_files.return_value = large_file_list

        affected, reason = get_affected_projects(
            self.projects_config,
            self.optimization_config
        )

        # Should still work correctly
        self.assertEqual(affected, {'backend'})

    @patch('change_detection.get_changed_files_from_git')
    def test_special_characters_in_filenames(self, mock_get_files):
        """Test handling of special characters in filenames."""
        mock_get_files.return_value = [
            'backend/file with spaces.py',
            'backend/file-with-dashes.py',
            'backend/file_with_underscores.py',
            'frontend/file.test.js'
        ]

        affected, reason = get_affected_projects(
            self.projects_config,
            self.optimization_config
        )

        # Should handle special characters
        self.assertEqual(affected, {'backend', 'frontend'})

    @patch('change_detection.get_changed_files_from_git')
    def test_unicode_filenames(self, mock_get_files):
        """Test handling of Unicode characters in filenames."""
        mock_get_files.return_value = [
            'backend/файл.py',  # Russian
            'frontend/文件.js'   # Chinese
        ]

        affected, reason = get_affected_projects(
            self.projects_config,
            self.optimization_config
        )

        # Should handle Unicode filenames
        self.assertEqual(affected, {'backend', 'frontend'})

    @patch('change_detection.get_changed_files_from_git')
    def test_empty_project_directory(self, mock_get_files):
        """Test handling of projects with empty directory field."""
        projects_config = {
            "backend": {"directory": ""},  # Empty directory
            "frontend": {"directory": "frontend/"}
        }
        mock_get_files.return_value = ['frontend/index.js']

        affected, reason = get_affected_projects(
            projects_config,
            self.optimization_config
        )

        # Should skip backend (empty dir) and detect frontend
        self.assertIn('frontend', affected)

    @patch('change_detection.get_changed_files_from_git')
    def test_invalid_force_check_project(self, mock_get_files):
        """Test handling of invalid project in force_check_projects."""
        mock_get_files.return_value = ['backend/main.py']

        optimization_config = self.optimization_config.copy()
        optimization_config['force_check_projects'] = ['backend', 'nonexistent-project']

        affected, reason = get_affected_projects(
            self.projects_config,
            optimization_config
        )

        # Should include backend (changed) but skip nonexistent project
        self.assertIn('backend', affected)
        self.assertNotIn('nonexistent-project', affected)

    @patch('change_detection.get_changed_files_from_git')
    def test_duplicate_files_in_change_list(self, mock_get_files):
        """Test handling of duplicate files in git output."""
        mock_get_files.return_value = [
            'backend/main.py',
            'backend/main.py',  # Duplicate
            'backend/test.py'
        ]

        affected, reason = get_affected_projects(
            self.projects_config,
            self.optimization_config
        )

        # Should handle duplicates gracefully
        self.assertEqual(affected, {'backend'})

    @patch('change_detection.get_changed_files_from_git')
    def test_trailing_slashes_in_paths(self, mock_get_files):
        """Test handling of trailing slashes in file paths."""
        mock_get_files.return_value = [
            'backend/main.py',
            'frontend/src/'  # Trailing slash (directory)
        ]

        affected, reason = get_affected_projects(
            self.projects_config,
            self.optimization_config
        )

        # Should handle trailing slashes
        self.assertIn('backend', affected)
        self.assertIn('frontend', affected)

    @patch.dict(os.environ, {'SYNAPSE_DETECTION_METHOD': 'invalid_method'})
    @patch('change_detection.get_changed_files_from_git')
    def test_invalid_detection_method_env(self, mock_get_files):
        """Test handling of invalid detection method in environment variable."""
        mock_get_files.return_value = ['backend/main.py']

        affected, reason = get_affected_projects(
            self.projects_config,
            self.optimization_config
        )

        # Should fall back to default method (uncommitted)
        mock_get_files.assert_called_once_with('uncommitted')

    @patch('change_detection.get_changed_files_from_git')
    def test_no_fallback_with_no_changes(self, mock_get_files):
        """Test behavior when fallback is disabled and no changes."""
        mock_get_files.return_value = []

        optimization_config = self.optimization_config.copy()
        optimization_config['fallback_to_all'] = False

        affected, reason = get_affected_projects(
            self.projects_config,
            optimization_config
        )

        # Should return empty set
        self.assertEqual(affected, set())
        self.assertIn('skip', reason)


if __name__ == '__main__':
    unittest.main()
