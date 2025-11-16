"""Unit tests for core/types.py."""
import pytest
from synapse_cli.core.types import (
    WorkflowMode,
    ExitCode,
    ConfigDict,
    ManifestDict,
)


class TestWorkflowMode:
    """Test WorkflowMode enum."""

    def test_single_mode(self):
        """Test SINGLE mode value."""
        assert WorkflowMode.SINGLE.value == "single"

    def test_monorepo_mode(self):
        """Test MONOREPO mode value."""
        assert WorkflowMode.MONOREPO.value == "monorepo"

    def test_enum_members(self):
        """Test all enum members exist."""
        assert len(WorkflowMode) == 2
        assert WorkflowMode.SINGLE in WorkflowMode
        assert WorkflowMode.MONOREPO in WorkflowMode


class TestExitCode:
    """Test ExitCode enum."""

    def test_success_code(self):
        """Test SUCCESS exit code."""
        assert ExitCode.SUCCESS.value == 0

    def test_show_message_code(self):
        """Test SHOW_MESSAGE exit code."""
        assert ExitCode.SHOW_MESSAGE.value == 1

    def test_block_code(self):
        """Test BLOCK exit code."""
        assert ExitCode.BLOCK.value == 2

    def test_enum_members(self):
        """Test all enum members exist."""
        assert len(ExitCode) == 3
        assert ExitCode.SUCCESS in ExitCode
        assert ExitCode.SHOW_MESSAGE in ExitCode
        assert ExitCode.BLOCK in ExitCode


class TestConfigDict:
    """Test ConfigDict TypedDict."""

    def test_valid_config_dict(self):
        """Test creating a valid ConfigDict."""
        config: ConfigDict = {
            'synapse_version': '0.3.0',
            'initialized_at': '2025-01-01T12:00:00',
            'project': {
                'name': 'test-project',
                'root_directory': '/path/to/project'
            },
            'agent': {
                'name': 'test-agent'
            },
            'workflows': {},
            'quality_config': {}
        }

        assert config['synapse_version'] == '0.3.0'
        assert config['initialized_at'] == '2025-01-01T12:00:00'
        assert config['project']['name'] == 'test-project'

    def test_minimal_config_dict(self):
        """Test ConfigDict with only required fields."""
        # ConfigDict has total=False, so all fields are optional
        config: ConfigDict = {}
        assert isinstance(config, dict)

    def test_config_dict_with_optional_fields(self):
        """Test ConfigDict with third_party_workflow."""
        config: ConfigDict = {
            'synapse_version': '0.3.0',
            'third_party_workflow': {
                'name': 'custom-workflow'
            }
        }

        assert config.get('third_party_workflow') is not None
        assert config['third_party_workflow']['name'] == 'custom-workflow'


class TestManifestDict:
    """Test ManifestDict TypedDict."""

    def test_valid_manifest_dict(self):
        """Test creating a valid ManifestDict."""
        manifest: ManifestDict = {
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

        assert manifest['workflow_name'] == 'feature-implementation'
        assert manifest['applied_at'] == '2025-01-01T12:00:00'
        assert manifest['synapse_version'] == '0.3.0'
        assert len(manifest['files_copied']) == 1
        assert len(manifest['hooks_added']) == 1
        assert len(manifest['settings_updated']) == 1

    def test_manifest_dict_empty_lists(self):
        """Test ManifestDict with empty lists."""
        manifest: ManifestDict = {
            'workflow_name': 'test-workflow',
            'applied_at': '2025-01-01T12:00:00',
            'synapse_version': '0.3.0',
            'files_copied': [],
            'hooks_added': [],
            'settings_updated': []
        }

        assert manifest['files_copied'] == []
        assert manifest['hooks_added'] == []
        assert manifest['settings_updated'] == []
