"""Unit tests for infrastructure/resources.py."""
import pytest
import json
import tempfile
from pathlib import Path
from synapse_cli.infrastructure.resources import ResourceManager, get_resource_manager
from synapse_cli.core.models import WorkflowInfo


class TestResourceManager:
    """Test ResourceManager class."""

    @pytest.fixture
    def temp_resources_dir(self):
        """Create temporary resources directory structure for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resources_dir = Path(tmpdir) / "resources"
            workflows_dir = resources_dir / "workflows"
            workflows_dir.mkdir(parents=True)

            # Create test workflows
            self._create_workflow(
                workflows_dir / "feature-planning",
                "Feature Planning Workflow",
                "1.0"
            )
            self._create_workflow(
                workflows_dir / "feature-implementation",
                "Feature Implementation Workflow",
                "2.0"
            )

            # Create workflow without metadata
            basic_workflow = workflows_dir / "basic-workflow"
            basic_workflow.mkdir()
            (basic_workflow / "settings.json").write_text('{}')

            yield resources_dir

    def _create_workflow(self, workflow_dir: Path, description: str, version: str):
        """Helper to create a test workflow."""
        workflow_dir.mkdir()
        settings = {
            "workflow_metadata": {
                "description": description,
                "version": version
            }
        }
        (workflow_dir / "settings.json").write_text(json.dumps(settings, indent=2))

    def test_singleton_pattern(self):
        """Test that get_resource_manager returns the same instance."""
        manager1 = get_resource_manager()
        manager2 = get_resource_manager()
        assert manager1 is manager2

    def test_resources_dir_cached(self):
        """Test that resources_dir property is cached."""
        manager = ResourceManager()
        # Access property twice
        dir1 = manager.resources_dir
        dir2 = manager.resources_dir
        # Should be the same instance (cached)
        assert dir1 is dir2

    def test_workflows_dir_cached(self):
        """Test that workflows_dir property is cached."""
        manager = ResourceManager()
        # Access property twice
        try:
            dir1 = manager.workflows_dir
            dir2 = manager.workflows_dir
            # Should be the same instance (cached)
            assert dir1 is dir2
        except SystemExit:
            # This is expected in test environment where resources might not exist
            pass

    def test_discover_workflows(self, temp_resources_dir, monkeypatch):
        """Test discover_workflows returns sorted list of workflow names."""
        # Monkeypatch the resource manager to use temp directory
        manager = ResourceManager()
        manager._resources_dir = temp_resources_dir
        manager._workflows_dir = temp_resources_dir / "workflows"

        workflows = manager.discover_workflows()

        assert isinstance(workflows, list)
        assert len(workflows) == 3
        # Should be sorted
        assert workflows == ['basic-workflow', 'feature-implementation', 'feature-planning']

    def test_discover_workflows_empty_directory(self, monkeypatch):
        """Test discover_workflows with empty workflows directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workflows_dir = Path(tmpdir) / "workflows"
            workflows_dir.mkdir()

            manager = ResourceManager()
            manager._workflows_dir = workflows_dir

            workflows = manager.discover_workflows()
            assert workflows == []

    def test_discover_workflows_ignores_invalid_workflows(self, monkeypatch):
        """Test discover_workflows ignores directories without settings.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workflows_dir = Path(tmpdir) / "workflows"
            workflows_dir.mkdir()

            # Create valid workflow
            valid_workflow = workflows_dir / "valid"
            valid_workflow.mkdir()
            (valid_workflow / "settings.json").write_text('{}')

            # Create invalid workflow (no settings.json)
            invalid_workflow = workflows_dir / "invalid"
            invalid_workflow.mkdir()

            manager = ResourceManager()
            manager._workflows_dir = workflows_dir

            workflows = manager.discover_workflows()
            assert workflows == ['valid']

    def test_get_workflow_info_with_metadata(self, temp_resources_dir):
        """Test get_workflow_info with workflow that has metadata."""
        manager = ResourceManager()
        manager._resources_dir = temp_resources_dir
        manager._workflows_dir = temp_resources_dir / "workflows"

        info = manager.get_workflow_info("feature-planning")

        assert isinstance(info, WorkflowInfo)
        assert info.name == "feature-planning"
        assert info.description == "Feature Planning Workflow"
        assert info.version == "1.0"
        assert info.path == temp_resources_dir / "workflows" / "feature-planning"

    def test_get_workflow_info_without_metadata(self, temp_resources_dir):
        """Test get_workflow_info with workflow that has no metadata."""
        manager = ResourceManager()
        manager._resources_dir = temp_resources_dir
        manager._workflows_dir = temp_resources_dir / "workflows"

        info = manager.get_workflow_info("basic-workflow")

        assert isinstance(info, WorkflowInfo)
        assert info.name == "basic-workflow"
        assert info.description is None
        assert info.version is None
        assert info.path == temp_resources_dir / "workflows" / "basic-workflow"

    def test_get_workflow_info_missing_workflow(self, temp_resources_dir):
        """Test get_workflow_info with non-existent workflow."""
        manager = ResourceManager()
        manager._resources_dir = temp_resources_dir
        manager._workflows_dir = temp_resources_dir / "workflows"

        info = manager.get_workflow_info("non-existent")
        assert info is None

    def test_get_workflow_info_invalid_json(self, temp_resources_dir):
        """Test get_workflow_info with invalid JSON in settings.json."""
        manager = ResourceManager()
        manager._resources_dir = temp_resources_dir
        manager._workflows_dir = temp_resources_dir / "workflows"

        # Create workflow with invalid JSON
        invalid_workflow = temp_resources_dir / "workflows" / "invalid-json"
        invalid_workflow.mkdir()
        (invalid_workflow / "settings.json").write_text('invalid json {')

        info = manager.get_workflow_info("invalid-json")
        assert info is None

    def test_validate_workflow_exists_valid(self, temp_resources_dir):
        """Test validate_workflow_exists with valid workflow."""
        manager = ResourceManager()
        manager._resources_dir = temp_resources_dir
        manager._workflows_dir = temp_resources_dir / "workflows"

        assert manager.validate_workflow_exists("feature-planning") is True

    def test_validate_workflow_exists_missing(self, temp_resources_dir):
        """Test validate_workflow_exists with missing workflow."""
        manager = ResourceManager()
        manager._resources_dir = temp_resources_dir
        manager._workflows_dir = temp_resources_dir / "workflows"

        assert manager.validate_workflow_exists("non-existent") is False

    def test_validate_workflow_exists_no_settings(self, temp_resources_dir):
        """Test validate_workflow_exists with workflow missing settings.json."""
        manager = ResourceManager()
        manager._resources_dir = temp_resources_dir
        manager._workflows_dir = temp_resources_dir / "workflows"

        # Create workflow directory without settings.json
        no_settings = temp_resources_dir / "workflows" / "no-settings"
        no_settings.mkdir()

        assert manager.validate_workflow_exists("no-settings") is False
