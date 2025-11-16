"""Unit tests for core/models.py."""
import pytest
from datetime import datetime
from pathlib import Path
from synapse_cli.core.models import (
    ProjectConfig,
    WorkflowManifest,
    WorkflowInfo,
    BackupInfo,
)
from synapse_cli.core.types import ConfigDict, ManifestDict


class TestProjectConfig:
    """Test ProjectConfig dataclass."""

    def test_instantiation(self):
        """Test creating ProjectConfig instance."""
        now = datetime.now()
        config = ProjectConfig(
            name='test-project',
            root_directory=Path('/path/to/project'),
            synapse_version='0.3.0',
            initialized_at=now
        )

        assert config.name == 'test-project'
        assert config.root_directory == Path('/path/to/project')
        assert config.synapse_version == '0.3.0'
        assert config.initialized_at == now

    def test_from_dict(self):
        """Test ProjectConfig.from_dict() classmethod."""
        config_dict: ConfigDict = {
            'synapse_version': '0.3.0',
            'initialized_at': '2025-01-01T12:00:00',
            'project': {
                'name': 'test-project',
                'root_directory': '/path/to/project'
            }
        }

        config = ProjectConfig.from_dict(config_dict)

        assert config.name == 'test-project'
        assert config.root_directory == Path('/path/to/project')
        assert config.synapse_version == '0.3.0'
        assert config.initialized_at == datetime(2025, 1, 1, 12, 0, 0)

    def test_to_dict(self):
        """Test ProjectConfig.to_dict() method."""
        now = datetime(2025, 1, 1, 12, 0, 0)
        config = ProjectConfig(
            name='test-project',
            root_directory=Path('/path/to/project'),
            synapse_version='0.3.0',
            initialized_at=now
        )

        config_dict = config.to_dict()

        assert config_dict['synapse_version'] == '0.3.0'
        assert config_dict['initialized_at'] == '2025-01-01T12:00:00'
        assert config_dict['project']['name'] == 'test-project'
        assert config_dict['project']['root_directory'] == '/path/to/project'

    def test_round_trip(self):
        """Test from_dict() -> to_dict() round trip."""
        original_dict: ConfigDict = {
            'synapse_version': '0.3.0',
            'initialized_at': '2025-01-01T12:00:00',
            'project': {
                'name': 'test-project',
                'root_directory': '/path/to/project'
            }
        }

        config = ProjectConfig.from_dict(original_dict)
        result_dict = config.to_dict()

        assert result_dict['synapse_version'] == original_dict['synapse_version']
        assert result_dict['initialized_at'] == original_dict['initialized_at']
        assert result_dict['project']['name'] == original_dict['project']['name']
        assert result_dict['project']['root_directory'] == original_dict['project']['root_directory']


class TestWorkflowManifest:
    """Test WorkflowManifest dataclass."""

    def test_instantiation(self):
        """Test creating WorkflowManifest instance."""
        now = datetime.now()
        manifest = WorkflowManifest(
            workflow_name='feature-implementation',
            applied_at=now,
            synapse_version='0.3.0',
            files_copied=[{'source': 'tasks.md', 'destination': '.synapse/tasks.md'}],
            hooks_added=[{'name': 'stop_qa_check', 'path': '.claude/hooks/stop_qa_check.py'}],
            settings_updated=['workflow_mode']
        )

        assert manifest.workflow_name == 'feature-implementation'
        assert manifest.applied_at == now
        assert manifest.synapse_version == '0.3.0'
        assert len(manifest.files_copied) == 1
        assert len(manifest.hooks_added) == 1
        assert len(manifest.settings_updated) == 1

    def test_instantiation_with_defaults(self):
        """Test creating WorkflowManifest with default values."""
        now = datetime.now()
        manifest = WorkflowManifest(
            workflow_name='test-workflow',
            applied_at=now,
            synapse_version='0.3.0'
        )

        assert manifest.workflow_name == 'test-workflow'
        assert manifest.applied_at == now
        assert manifest.synapse_version == '0.3.0'
        assert manifest.files_copied == []
        assert manifest.hooks_added == []
        assert manifest.settings_updated == []

    def test_from_dict(self):
        """Test WorkflowManifest.from_dict() classmethod."""
        manifest_dict: ManifestDict = {
            'workflow_name': 'feature-implementation',
            'applied_at': '2025-01-01T12:00:00',
            'synapse_version': '0.3.0',
            'files_copied': [
                {'source': 'tasks.md', 'destination': '.synapse/tasks.md'}
            ],
            'hooks_added': [
                {'name': 'stop_qa_check', 'path': '.claude/hooks/stop_qa_check.py'}
            ],
            'settings_updated': ['workflow_mode']
        }

        manifest = WorkflowManifest.from_dict(manifest_dict)

        assert manifest.workflow_name == 'feature-implementation'
        assert manifest.applied_at == datetime(2025, 1, 1, 12, 0, 0)
        assert manifest.synapse_version == '0.3.0'
        assert len(manifest.files_copied) == 1
        assert len(manifest.hooks_added) == 1
        assert len(manifest.settings_updated) == 1

    def test_from_dict_with_missing_optional_fields(self):
        """Test WorkflowManifest.from_dict() with missing optional fields."""
        manifest_dict: ManifestDict = {
            'workflow_name': 'test-workflow',
            'applied_at': '2025-01-01T12:00:00',
            'synapse_version': '0.3.0',
            'files_copied': [],
            'hooks_added': [],
            'settings_updated': []
        }

        manifest = WorkflowManifest.from_dict(manifest_dict)

        assert manifest.files_copied == []
        assert manifest.hooks_added == []
        assert manifest.settings_updated == []

    def test_to_dict(self):
        """Test WorkflowManifest.to_dict() method."""
        now = datetime(2025, 1, 1, 12, 0, 0)
        manifest = WorkflowManifest(
            workflow_name='feature-implementation',
            applied_at=now,
            synapse_version='0.3.0',
            files_copied=[{'source': 'tasks.md', 'destination': '.synapse/tasks.md'}],
            hooks_added=[{'name': 'stop_qa_check', 'path': '.claude/hooks/stop_qa_check.py'}],
            settings_updated=['workflow_mode']
        )

        manifest_dict = manifest.to_dict()

        assert manifest_dict['workflow_name'] == 'feature-implementation'
        assert manifest_dict['applied_at'] == '2025-01-01T12:00:00'
        assert manifest_dict['synapse_version'] == '0.3.0'
        assert len(manifest_dict['files_copied']) == 1
        assert len(manifest_dict['hooks_added']) == 1
        assert len(manifest_dict['settings_updated']) == 1

    def test_round_trip(self):
        """Test from_dict() -> to_dict() round trip."""
        original_dict: ManifestDict = {
            'workflow_name': 'feature-implementation',
            'applied_at': '2025-01-01T12:00:00',
            'synapse_version': '0.3.0',
            'files_copied': [
                {'source': 'tasks.md', 'destination': '.synapse/tasks.md'}
            ],
            'hooks_added': [
                {'name': 'stop_qa_check', 'path': '.claude/hooks/stop_qa_check.py'}
            ],
            'settings_updated': ['workflow_mode']
        }

        manifest = WorkflowManifest.from_dict(original_dict)
        result_dict = manifest.to_dict()

        assert result_dict['workflow_name'] == original_dict['workflow_name']
        assert result_dict['applied_at'] == original_dict['applied_at']
        assert result_dict['synapse_version'] == original_dict['synapse_version']
        assert result_dict['files_copied'] == original_dict['files_copied']
        assert result_dict['hooks_added'] == original_dict['hooks_added']
        assert result_dict['settings_updated'] == original_dict['settings_updated']


class TestWorkflowInfo:
    """Test WorkflowInfo dataclass."""

    def test_instantiation(self):
        """Test creating WorkflowInfo instance."""
        workflow = WorkflowInfo(
            name='feature-implementation',
            description='Feature implementation workflow',
            version='2.0',
            path=Path('/path/to/workflow')
        )

        assert workflow.name == 'feature-implementation'
        assert workflow.description == 'Feature implementation workflow'
        assert workflow.version == '2.0'
        assert workflow.path == Path('/path/to/workflow')

    def test_instantiation_with_defaults(self):
        """Test creating WorkflowInfo with default values."""
        workflow = WorkflowInfo(name='test-workflow')

        assert workflow.name == 'test-workflow'
        assert workflow.description is None
        assert workflow.version is None
        assert workflow.path is None

    def test_instantiation_with_partial_defaults(self):
        """Test creating WorkflowInfo with some optional fields."""
        workflow = WorkflowInfo(
            name='test-workflow',
            description='Test workflow'
        )

        assert workflow.name == 'test-workflow'
        assert workflow.description == 'Test workflow'
        assert workflow.version is None
        assert workflow.path is None


class TestBackupInfo:
    """Test BackupInfo dataclass."""

    def test_instantiation(self):
        """Test creating BackupInfo instance."""
        now = datetime.now()
        backup = BackupInfo(
            path=Path('/path/to/backup'),
            created_at=now,
            workflow_name='feature-implementation'
        )

        assert backup.path == Path('/path/to/backup')
        assert backup.created_at == now
        assert backup.workflow_name == 'feature-implementation'

    def test_instantiation_with_defaults(self):
        """Test creating BackupInfo with default values."""
        now = datetime.now()
        backup = BackupInfo(
            path=Path('/path/to/backup'),
            created_at=now
        )

        assert backup.path == Path('/path/to/backup')
        assert backup.created_at == now
        assert backup.workflow_name is None

    def test_path_type(self):
        """Test that path is correctly stored as Path object."""
        now = datetime.now()
        backup = BackupInfo(
            path=Path('/path/to/backup'),
            created_at=now
        )

        assert isinstance(backup.path, Path)
        assert str(backup.path) == '/path/to/backup'
