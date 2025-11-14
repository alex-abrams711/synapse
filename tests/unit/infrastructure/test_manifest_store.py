"""Unit tests for infrastructure/manifest_store.py."""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from synapse_cli.infrastructure.manifest_store import ManifestStore, get_manifest_store
from synapse_cli.core.models import WorkflowManifest


class TestManifestStore:
    """Test ManifestStore class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manifest_store(self):
        """Create ManifestStore instance for testing."""
        return ManifestStore("0.3.0")

    @pytest.fixture
    def sample_manifest(self):
        """Create sample manifest for testing."""
        return WorkflowManifest(
            workflow_name='feature-implementation-v2',
            applied_at=datetime(2025, 1, 1, 12, 0, 0),
            synapse_version='0.3.0',
            files_copied=[
                {'path': '.synapse/tasks.md', 'type': 'synapse_files'}
            ],
            hooks_added=[
                {'name': 'stop_qa_check', 'path': '.claude/hooks/stop_qa_check.py'}
            ],
            settings_updated=['workflow_mode']
        )

    def test_factory_function(self):
        """Test get_manifest_store factory function."""
        store = get_manifest_store("0.3.0")
        assert isinstance(store, ManifestStore)
        assert store._synapse_version == "0.3.0"

    def test_get_path(self, manifest_store, temp_dir):
        """Test get_path returns correct path."""
        path = manifest_store.get_path(temp_dir)
        assert path == temp_dir / ".synapse" / "workflow-manifest.json"

    def test_exists_missing_file(self, manifest_store, temp_dir):
        """Test exists returns False when file doesn't exist."""
        assert manifest_store.exists(temp_dir) is False

    def test_exists_existing_file(self, manifest_store, temp_dir, sample_manifest):
        """Test exists returns True when file exists."""
        # Save manifest
        manifest_store.save(sample_manifest, temp_dir)

        # Check exists
        assert manifest_store.exists(temp_dir) is True

    def test_load_missing_file(self, manifest_store, temp_dir):
        """Test load returns None when file doesn't exist."""
        result = manifest_store.load(temp_dir)
        assert result is None

    def test_load_valid_manifest(self, manifest_store, temp_dir, sample_manifest):
        """Test load with valid manifest file."""
        # Save manifest
        manifest_store.save(sample_manifest, temp_dir)

        # Load and verify
        result = manifest_store.load(temp_dir)
        assert isinstance(result, WorkflowManifest)
        assert result.workflow_name == sample_manifest.workflow_name
        assert result.synapse_version == sample_manifest.synapse_version
        assert result.files_copied == sample_manifest.files_copied
        assert result.hooks_added == sample_manifest.hooks_added
        assert result.settings_updated == sample_manifest.settings_updated

    def test_save_valid_manifest(self, manifest_store, temp_dir, sample_manifest):
        """Test save with valid manifest."""
        result = manifest_store.save(sample_manifest, temp_dir)
        assert result is True

        # Verify file exists
        assert (temp_dir / ".synapse" / "workflow-manifest.json").exists()

    def test_save_load_roundtrip(self, manifest_store, temp_dir, sample_manifest):
        """Test save and load roundtrip."""
        # Save
        save_result = manifest_store.save(sample_manifest, temp_dir)
        assert save_result is True

        # Load
        loaded_manifest = manifest_store.load(temp_dir)
        assert loaded_manifest.workflow_name == sample_manifest.workflow_name
        assert loaded_manifest.synapse_version == sample_manifest.synapse_version
        assert loaded_manifest.files_copied == sample_manifest.files_copied
        assert loaded_manifest.hooks_added == sample_manifest.hooks_added
        assert loaded_manifest.settings_updated == sample_manifest.settings_updated

    def test_create_manifest_basic(self, manifest_store, temp_dir):
        """Test create_manifest with basic data."""
        copied_files = {
            'synapse_files': [
                temp_dir / '.synapse' / 'tasks.md'
            ]
        }
        hooks_added = [
            {'name': 'stop_qa_check', 'path': '.claude/hooks/stop_qa_check.py'}
        ]
        settings_updated = ['workflow_mode']

        manifest = manifest_store.create_manifest(
            workflow_name='feature-planning',
            copied_files=copied_files,
            hooks_added=hooks_added,
            settings_updated=settings_updated,
            target_dir=temp_dir
        )

        assert isinstance(manifest, WorkflowManifest)
        assert manifest.workflow_name == 'feature-planning'
        assert manifest.synapse_version == '0.3.0'
        assert len(manifest.files_copied) == 1
        assert manifest.files_copied[0]['path'] == '.synapse/tasks.md'
        assert manifest.files_copied[0]['type'] == 'synapse_files'
        assert manifest.hooks_added == hooks_added
        assert manifest.settings_updated == settings_updated

    def test_create_manifest_multiple_file_types(self, manifest_store, temp_dir):
        """Test create_manifest with multiple file types."""
        copied_files = {
            'synapse_files': [
                temp_dir / '.synapse' / 'tasks.md',
                temp_dir / '.synapse' / 'schema.json'
            ],
            'hooks': [
                temp_dir / '.claude' / 'hooks' / 'stop_qa_check.py'
            ]
        }

        manifest = manifest_store.create_manifest(
            workflow_name='test-workflow',
            copied_files=copied_files,
            hooks_added=[],
            settings_updated=[],
            target_dir=temp_dir
        )

        assert len(manifest.files_copied) == 3
        # Check that files are properly categorized by type
        synapse_files = [f for f in manifest.files_copied if f['type'] == 'synapse_files']
        hook_files = [f for f in manifest.files_copied if f['type'] == 'hooks']
        assert len(synapse_files) == 2
        assert len(hook_files) == 1

    def test_create_manifest_empty_data(self, manifest_store, temp_dir):
        """Test create_manifest with empty data."""
        manifest = manifest_store.create_manifest(
            workflow_name='empty-workflow',
            copied_files={},
            hooks_added=[],
            settings_updated=[],
            target_dir=temp_dir
        )

        assert isinstance(manifest, WorkflowManifest)
        assert manifest.workflow_name == 'empty-workflow'
        assert manifest.files_copied == []
        assert manifest.hooks_added == []
        assert manifest.settings_updated == []

    def test_create_manifest_absolute_paths_outside_target(self, manifest_store, temp_dir):
        """Test create_manifest with absolute paths outside target directory."""
        # Create a file outside the target directory
        with tempfile.TemporaryDirectory() as other_dir:
            other_path = Path(other_dir) / 'external.txt'

            copied_files = {
                'external': [other_path]
            }

            manifest = manifest_store.create_manifest(
                workflow_name='test-workflow',
                copied_files=copied_files,
                hooks_added=[],
                settings_updated=[],
                target_dir=temp_dir
            )

            # Should store absolute path since it's outside target_dir
            assert len(manifest.files_copied) == 1
            assert manifest.files_copied[0]['path'] == str(other_path)

    def test_delete_existing_file(self, manifest_store, temp_dir, sample_manifest):
        """Test delete with existing manifest file."""
        # Save manifest first
        manifest_store.save(sample_manifest, temp_dir)
        assert manifest_store.exists(temp_dir) is True

        # Delete
        result = manifest_store.delete(temp_dir)
        assert result is True
        assert manifest_store.exists(temp_dir) is False

    def test_delete_missing_file(self, manifest_store, temp_dir):
        """Test delete with missing manifest file."""
        # Should return True even if file doesn't exist
        result = manifest_store.delete(temp_dir)
        assert result is True

    def test_manifest_store_different_versions(self):
        """Test ManifestStore with different synapse versions."""
        store1 = ManifestStore("0.3.0")
        store2 = ManifestStore("0.4.0")

        assert store1._synapse_version == "0.3.0"
        assert store2._synapse_version == "0.4.0"

    def test_create_manifest_sets_correct_timestamp(self, manifest_store, temp_dir):
        """Test that create_manifest sets a valid timestamp."""
        before = datetime.now()

        manifest = manifest_store.create_manifest(
            workflow_name='test-workflow',
            copied_files={},
            hooks_added=[],
            settings_updated=[],
            target_dir=temp_dir
        )

        after = datetime.now()

        # Check timestamp is between before and after
        assert before <= manifest.applied_at <= after
