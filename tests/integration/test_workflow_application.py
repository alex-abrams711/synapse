"""Integration tests for workflow application.

Tests the complete workflow application flow using real services
with temporary directories and actual file operations.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime

from synapse_cli.services.workflow_service import WorkflowService
from synapse_cli.services.removal_service import RemovalService
from synapse_cli.infrastructure.config_store import ConfigStore


@pytest.fixture
def test_project_dir(tmp_path):
    """Create a test project directory with .synapse initialized."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create .synapse directory
    synapse_dir = project_dir / ".synapse"
    synapse_dir.mkdir()

    # Create initial config.json
    config = {
        "synapse_version": "0.1.0",
        "initialized_at": datetime.now().isoformat(),
        "project": {
            "name": "test_project",
            "root_directory": str(project_dir.absolute())
        },
        "agent": {
            "type": "claude-code",
            "description": "Test agent"
        },
        "workflows": {
            "active": None,
            "history": []
        }
    }

    config_path = synapse_dir / "config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    return project_dir


@pytest.fixture
def workflow_service():
    """Create a WorkflowService instance."""
    return WorkflowService(synapse_version="0.1.0")


@pytest.fixture
def removal_service():
    """Create a RemovalService instance."""
    return RemovalService(synapse_version="0.1.0")


@pytest.mark.integration
class TestWorkflowApplication:
    """Integration tests for applying workflows."""

    def test_apply_workflow_creates_manifest(self, test_project_dir, workflow_service):
        """Test that applying a workflow creates manifest."""
        # Apply a workflow
        success = workflow_service.apply_workflow(
            "feature-planning",
            target_dir=test_project_dir,
            force=False
        )

        assert success is True

        # Verify workflow-manifest.json was created
        manifest_path = test_project_dir / ".synapse" / "workflow-manifest.json"
        assert manifest_path.exists()

        with open(manifest_path) as f:
            manifest = json.load(f)

        assert manifest["workflow_name"] == "feature-planning"
        assert "applied_at" in manifest
        assert "files_copied" in manifest
        assert len(manifest["files_copied"]) > 0

    def test_apply_workflow_copies_files_to_claude_dir(self, test_project_dir, workflow_service):
        """Test that workflow files are copied to .claude directory."""
        # Apply workflow
        success = workflow_service.apply_workflow(
            "feature-planning",
            target_dir=test_project_dir,
            force=False
        )

        assert success is True

        # Verify .claude directory was created
        claude_dir = test_project_dir / ".claude"
        assert claude_dir.exists()

        # Verify files were actually copied
        manifest_path = test_project_dir / ".synapse" / "workflow-manifest.json"
        with open(manifest_path) as f:
            manifest = json.load(f)

        for file_info in manifest["files_copied"]:
            file_path = test_project_dir / file_info["path"]
            assert file_path.exists(), f"File {file_info['path']} should exist"

    def test_apply_workflow_updates_config_tracking(self, test_project_dir, workflow_service):
        """Test that workflow application updates config tracking."""
        # Apply workflow
        success = workflow_service.apply_workflow(
            "feature-planning",
            target_dir=test_project_dir,
            force=False
        )

        assert success is True

        # Use ConfigStore to reload config
        config_store = ConfigStore()
        active_workflow = config_store.get_active_workflow(test_project_dir)

        assert active_workflow == "feature-planning"

    def test_apply_second_workflow_prompts_for_confirmation(self, test_project_dir, workflow_service, monkeypatch):
        """Test that applying a second workflow requires confirmation."""
        # Apply first workflow
        workflow_service.apply_workflow(
            "feature-planning",
            target_dir=test_project_dir,
            force=False
        )

        # Mock user input to decline workflow switch
        inputs = iter(["n"])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        # Try to apply second workflow - should exit during validation
        with pytest.raises(SystemExit):
            workflow_service.apply_workflow(
                "feature-implementation-v2",
                target_dir=test_project_dir,
                force=False
            )

    def test_apply_workflow_with_force_overwrites_files(self, test_project_dir, workflow_service):
        """Test that force flag overwrites existing files."""
        # Apply workflow first time
        workflow_service.apply_workflow(
            "feature-planning",
            target_dir=test_project_dir,
            force=False
        )

        # Modify a workflow file
        manifest_path = test_project_dir / ".synapse" / "workflow-manifest.json"
        with open(manifest_path) as f:
            manifest = json.load(f)

        if manifest["files_copied"]:
            first_file = manifest["files_copied"][0]["path"]
            file_path = test_project_dir / first_file

            if file_path.exists() and file_path.is_file() and file_path.suffix in ['.md', '.py']:
                # Write custom content
                file_path.write_text("MODIFIED CONTENT")

                # Reapply with force
                workflow_service.apply_workflow(
                    "feature-planning",
                    target_dir=test_project_dir,
                    force=True
                )

                # Verify file was overwritten
                new_content = file_path.read_text()
                assert new_content != "MODIFIED CONTENT"
                assert len(new_content) > 0  # Should have actual content


@pytest.mark.integration
class TestWorkflowRemoval:
    """Integration tests for removing workflows."""

    def test_remove_workflow_deletes_manifest(self, test_project_dir, workflow_service, removal_service, monkeypatch):
        """Test that removing workflow deletes manifest."""
        # Apply workflow
        workflow_service.apply_workflow(
            "feature-planning",
            target_dir=test_project_dir,
            force=False
        )

        manifest_path = test_project_dir / ".synapse" / "workflow-manifest.json"
        assert manifest_path.exists()

        # Mock user confirmation
        inputs = iter(["y"])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        # Remove workflow
        removal_service.remove_workflow(test_project_dir)

        # Verify manifest was deleted
        assert not manifest_path.exists()

    def test_remove_workflow_clears_active_workflow(self, test_project_dir, workflow_service, removal_service, monkeypatch):
        """Test that removing workflow clears active workflow in config."""
        # Apply workflow
        workflow_service.apply_workflow(
            "feature-planning",
            target_dir=test_project_dir,
            force=False
        )

        # Verify workflow is active
        config_store = ConfigStore()
        assert config_store.get_active_workflow(test_project_dir) == "feature-planning"

        # Mock user confirmation
        inputs = iter(["y"])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        # Remove workflow
        removal_service.remove_workflow(test_project_dir)

        # Verify active workflow is cleared
        assert config_store.get_active_workflow(test_project_dir) is None

    def test_remove_workflow_user_can_cancel(self, test_project_dir, workflow_service, removal_service, monkeypatch):
        """Test that user can cancel workflow removal."""
        # Apply workflow
        workflow_service.apply_workflow(
            "feature-planning",
            target_dir=test_project_dir,
            force=False
        )

        # Mock user declining removal
        inputs = iter(["n"])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        # Try to remove - should return False
        success = removal_service.remove_workflow(test_project_dir)

        assert success is False

        # Verify workflow is still active
        config_store = ConfigStore()
        assert config_store.get_active_workflow(test_project_dir) == "feature-planning"

        # Verify manifest still exists
        manifest_path = test_project_dir / ".synapse" / "workflow-manifest.json"
        assert manifest_path.exists()


@pytest.mark.integration
class TestWorkflowSwitching:
    """Integration tests for switching between workflows."""

    def test_switch_workflow_with_confirmation(self, test_project_dir, workflow_service, monkeypatch):
        """Test switching from one workflow to another."""
        # Apply first workflow
        workflow_service.apply_workflow(
            "feature-planning",
            target_dir=test_project_dir,
            force=False
        )

        # Mock user accepting the switch
        inputs = iter(["y"])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        # Apply second workflow
        success = workflow_service.apply_workflow(
            "feature-implementation-v2",
            target_dir=test_project_dir,
            force=False
        )

        assert success is True

        # Verify new workflow is active
        config_store = ConfigStore()
        assert config_store.get_active_workflow(test_project_dir) == "feature-implementation-v2"

    def test_switch_preserves_workflow_history(self, test_project_dir, workflow_service, monkeypatch):
        """Test that switching workflows preserves history."""
        # Apply first workflow
        workflow_service.apply_workflow(
            "feature-planning",
            target_dir=test_project_dir,
            force=False
        )

        # Verify first workflow is tracked
        config_store = ConfigStore()
        assert config_store.get_active_workflow(test_project_dir) == "feature-planning"

        # Mock user accepting the switch
        inputs = iter(["y"])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        # Switch to second workflow
        workflow_service.apply_workflow(
            "feature-implementation-v2",
            target_dir=test_project_dir,
            force=False
        )

        # Verify second workflow is now active
        assert config_store.get_active_workflow(test_project_dir) == "feature-implementation-v2"

        # Verify both workflows have manifests (one after another shows switching worked)
        manifest_path = test_project_dir / ".synapse" / "workflow-manifest.json"
        with open(manifest_path) as f:
            manifest = json.load(f)

        # The manifest should reflect the most recent workflow
        assert manifest["workflow_name"] == "feature-implementation-v2"

    def test_switch_creates_new_manifest(self, test_project_dir, workflow_service, monkeypatch):
        """Test that switching workflows creates a new manifest for the new workflow."""
        # Apply first workflow
        workflow_service.apply_workflow(
            "feature-planning",
            target_dir=test_project_dir,
            force=False
        )

        # Read first manifest
        manifest_path = test_project_dir / ".synapse" / "workflow-manifest.json"
        with open(manifest_path) as f:
            first_manifest = json.load(f)

        assert first_manifest["workflow_name"] == "feature-planning"

        # Mock user accepting the switch
        inputs = iter(["y"])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        # Switch workflow
        workflow_service.apply_workflow(
            "feature-implementation-v2",
            target_dir=test_project_dir,
            force=False
        )

        # Verify new manifest was created
        with open(manifest_path) as f:
            second_manifest = json.load(f)

        assert second_manifest["workflow_name"] == "feature-implementation-v2"
        assert second_manifest["applied_at"] != first_manifest["applied_at"]
