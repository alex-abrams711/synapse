"""Unit tests for infrastructure/config_store.py."""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from synapse_cli.infrastructure.config_store import ConfigStore, get_config_store
from synapse_cli.core.types import ConfigDict


class TestConfigStore:
    """Test ConfigStore class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def config_store(self):
        """Create ConfigStore instance for testing."""
        return ConfigStore()

    @pytest.fixture
    def sample_config(self) -> ConfigDict:
        """Create sample config for testing."""
        return {
            'synapse_version': '0.3.0',
            'initialized_at': '2025-01-01T12:00:00',
            'project': {
                'name': 'test-project',
                'root_directory': '/path/to/project'
            },
            'agent': {},
            'workflows': {},
            'quality_config': {}
        }

    def test_singleton_pattern(self):
        """Test that get_config_store returns the same instance."""
        store1 = get_config_store()
        store2 = get_config_store()
        assert store1 is store2

    def test_get_path(self, config_store, temp_dir):
        """Test get_path returns correct path."""
        path = config_store.get_path(temp_dir)
        assert path == temp_dir / ".synapse" / "config.json"

    def test_exists_missing_file(self, config_store, temp_dir):
        """Test exists returns False when file doesn't exist."""
        assert config_store.exists(temp_dir) is False

    def test_exists_existing_file(self, config_store, temp_dir, sample_config):
        """Test exists returns True when file exists."""
        # Save config
        config_store.save(sample_config, temp_dir)

        # Check exists
        assert config_store.exists(temp_dir) is True

    def test_load_missing_file(self, config_store, temp_dir):
        """Test load returns None when file doesn't exist."""
        result = config_store.load(temp_dir)
        assert result is None

    def test_load_valid_config(self, config_store, temp_dir, sample_config):
        """Test load with valid config file."""
        # Save config
        config_store.save(sample_config, temp_dir)

        # Load and verify
        result = config_store.load(temp_dir)
        assert result == sample_config

    def test_save_valid_config(self, config_store, temp_dir, sample_config):
        """Test save with valid config."""
        result = config_store.save(sample_config, temp_dir)
        assert result is True

        # Verify file exists
        assert (temp_dir / ".synapse" / "config.json").exists()

    def test_save_load_roundtrip(self, config_store, temp_dir, sample_config):
        """Test save and load roundtrip."""
        # Save
        save_result = config_store.save(sample_config, temp_dir)
        assert save_result is True

        # Load
        loaded_config = config_store.load(temp_dir)
        assert loaded_config == sample_config

    def test_update_workflow_tracking_new_workflow(self, config_store, temp_dir, sample_config):
        """Test update_workflow_tracking with new workflow."""
        # Save initial config
        config_store.save(sample_config, temp_dir)

        # Update workflow tracking
        result = config_store.update_workflow_tracking('feature-planning', temp_dir)
        assert result is True

        # Load and verify
        config = config_store.load(temp_dir)
        assert config['workflows']['active_workflow'] == 'feature-planning'
        assert len(config['workflows']['applied_workflows']) == 1
        assert config['workflows']['applied_workflows'][0]['name'] == 'feature-planning'
        assert 'applied_at' in config['workflows']['applied_workflows'][0]

    def test_update_workflow_tracking_existing_workflow(self, config_store, temp_dir, sample_config):
        """Test update_workflow_tracking with workflow already in history."""
        # Save initial config with workflow history
        sample_config['workflows'] = {
            'active_workflow': None,
            'applied_workflows': [
                {
                    'name': 'feature-planning',
                    'applied_at': '2025-01-01T10:00:00'
                }
            ]
        }
        config_store.save(sample_config, temp_dir)

        # Update workflow tracking (same workflow)
        result = config_store.update_workflow_tracking('feature-planning', temp_dir)
        assert result is True

        # Load and verify
        config = config_store.load(temp_dir)
        assert config['workflows']['active_workflow'] == 'feature-planning'
        # Should not duplicate in history
        assert len(config['workflows']['applied_workflows']) == 1

    def test_update_workflow_tracking_different_workflow(self, config_store, temp_dir, sample_config):
        """Test update_workflow_tracking with different workflow."""
        # Save initial config with one workflow
        sample_config['workflows'] = {
            'active_workflow': None,
            'applied_workflows': [
                {
                    'name': 'feature-planning',
                    'applied_at': '2025-01-01T10:00:00'
                }
            ]
        }
        config_store.save(sample_config, temp_dir)

        # Update with different workflow
        result = config_store.update_workflow_tracking('feature-implementation', temp_dir)
        assert result is True

        # Load and verify
        config = config_store.load(temp_dir)
        assert config['workflows']['active_workflow'] == 'feature-implementation'
        # Should have both workflows in history
        assert len(config['workflows']['applied_workflows']) == 2

    def test_update_workflow_tracking_missing_config(self, config_store, temp_dir):
        """Test update_workflow_tracking when config doesn't exist."""
        result = config_store.update_workflow_tracking('feature-planning', temp_dir)
        assert result is False

    def test_clear_workflow_tracking(self, config_store, temp_dir, sample_config):
        """Test clear_workflow_tracking."""
        # Save config with active workflow
        sample_config['workflows'] = {
            'active_workflow': 'feature-planning',
            'applied_workflows': []
        }
        config_store.save(sample_config, temp_dir)

        # Clear workflow tracking
        result = config_store.clear_workflow_tracking(temp_dir)
        assert result is True

        # Load and verify
        config = config_store.load(temp_dir)
        assert config['workflows']['active_workflow'] is None

    def test_clear_workflow_tracking_missing_config(self, config_store, temp_dir):
        """Test clear_workflow_tracking when config doesn't exist."""
        result = config_store.clear_workflow_tracking(temp_dir)
        assert result is False

    def test_get_active_workflow_with_active(self, config_store, temp_dir, sample_config):
        """Test get_active_workflow with active workflow."""
        # Save config with active workflow
        sample_config['workflows'] = {
            'active_workflow': 'feature-planning',
            'applied_workflows': []
        }
        config_store.save(sample_config, temp_dir)

        # Get active workflow
        result = config_store.get_active_workflow(temp_dir)
        assert result == 'feature-planning'

    def test_get_active_workflow_no_active(self, config_store, temp_dir, sample_config):
        """Test get_active_workflow with no active workflow."""
        # Save config with no active workflow
        config_store.save(sample_config, temp_dir)

        # Get active workflow
        result = config_store.get_active_workflow(temp_dir)
        assert result is None

    def test_get_active_workflow_missing_config(self, config_store, temp_dir):
        """Test get_active_workflow when config doesn't exist."""
        result = config_store.get_active_workflow(temp_dir)
        assert result is None

    def test_get_active_workflow_no_workflows_key(self, config_store, temp_dir):
        """Test get_active_workflow when config has no workflows key."""
        # Save config without workflows key
        config: ConfigDict = {
            'synapse_version': '0.3.0',
            'initialized_at': '2025-01-01T12:00:00',
            'project': {
                'name': 'test-project',
                'root_directory': '/path/to/project'
            }
        }
        config_store.save(config, temp_dir)

        result = config_store.get_active_workflow(temp_dir)
        assert result is None
