"""Unit tests for services/validation_service.py."""
import pytest
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from synapse_cli.services.validation_service import ValidationService, get_validation_service


class TestValidationService:
    """Test ValidationService class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def validation_service(self):
        """Create ValidationService instance for testing."""
        return ValidationService()

    @pytest.fixture
    def mock_config_store(self, validation_service):
        """Mock config store."""
        mock = Mock()
        validation_service.config_store = mock
        return mock

    @pytest.fixture
    def mock_resource_manager(self, validation_service):
        """Mock resource manager."""
        mock = Mock()
        validation_service.resource_manager = mock
        return mock

    def test_singleton_pattern(self):
        """Test that get_validation_service returns the same instance."""
        service1 = get_validation_service()
        service2 = get_validation_service()
        assert service1 is service2

    def test_validate_synapse_initialized_true(
        self, validation_service, mock_config_store, temp_dir
    ):
        """Test validate_synapse_initialized when initialized."""
        mock_config_store.exists.return_value = True

        result = validation_service.validate_synapse_initialized(temp_dir)

        assert result is True
        mock_config_store.exists.assert_called_once_with(temp_dir)

    def test_validate_synapse_initialized_false(
        self, validation_service, mock_config_store, temp_dir
    ):
        """Test validate_synapse_initialized when not initialized."""
        mock_config_store.exists.return_value = False

        result = validation_service.validate_synapse_initialized(temp_dir)

        assert result is False
        mock_config_store.exists.assert_called_once_with(temp_dir)

    def test_validate_synapse_initialized_default_dir(
        self, validation_service, mock_config_store
    ):
        """Test validate_synapse_initialized with default directory."""
        mock_config_store.exists.return_value = True

        result = validation_service.validate_synapse_initialized()

        assert result is True
        mock_config_store.exists.assert_called_once_with(None)

    def test_validate_workflow_exists_true(
        self, validation_service, mock_resource_manager
    ):
        """Test validate_workflow_exists when workflow exists."""
        mock_resource_manager.validate_workflow_exists.return_value = True

        result = validation_service.validate_workflow_exists("test-workflow")

        assert result is True
        mock_resource_manager.validate_workflow_exists.assert_called_once_with(
            "test-workflow"
        )

    def test_validate_workflow_exists_false(
        self, validation_service, mock_resource_manager
    ):
        """Test validate_workflow_exists when workflow doesn't exist."""
        mock_resource_manager.validate_workflow_exists.return_value = False

        result = validation_service.validate_workflow_exists("nonexistent")

        assert result is False
        mock_resource_manager.validate_workflow_exists.assert_called_once_with(
            "nonexistent"
        )

    def test_check_uv_available_true(self, validation_service):
        """Test check_uv_available when uv is available."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = validation_service.check_uv_available()

            assert result is True
            mock_run.assert_called_once_with(
                ['uv', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )

    def test_check_uv_available_false(self, validation_service):
        """Test check_uv_available when uv is not available."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=1)

            result = validation_service.check_uv_available()

            assert result is False

    def test_check_uv_available_not_found(self, validation_service):
        """Test check_uv_available when uv command not found."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()

            result = validation_service.check_uv_available()

            assert result is False

    def test_check_uv_available_timeout(self, validation_service):
        """Test check_uv_available when command times out."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired('uv', 5)

            result = validation_service.check_uv_available()

            assert result is False

    def test_validate_workflow_preconditions_success(
        self, validation_service, mock_config_store, mock_resource_manager, temp_dir
    ):
        """Test validate_workflow_preconditions with all checks passing."""
        mock_config_store.exists.return_value = True
        mock_resource_manager.validate_workflow_exists.return_value = True
        mock_config_store.get_active_workflow.return_value = None

        with patch.object(validation_service, 'check_uv_available', return_value=True):
            # Should not raise
            validation_service.validate_workflow_preconditions("test-workflow", temp_dir)

    def test_validate_workflow_preconditions_not_initialized(
        self, validation_service, mock_config_store, temp_dir
    ):
        """Test validate_workflow_preconditions when not initialized."""
        mock_config_store.exists.return_value = False

        with pytest.raises(SystemExit) as exc_info:
            validation_service.validate_workflow_preconditions("test-workflow", temp_dir)

        assert exc_info.value.code == 1

    def test_validate_workflow_preconditions_workflow_not_found(
        self, validation_service, mock_config_store, mock_resource_manager, temp_dir
    ):
        """Test validate_workflow_preconditions when workflow doesn't exist."""
        mock_config_store.exists.return_value = True
        mock_resource_manager.validate_workflow_exists.return_value = False
        mock_resource_manager.discover_workflows.return_value = [
            "workflow1",
            "workflow2"
        ]

        with pytest.raises(SystemExit) as exc_info:
            validation_service.validate_workflow_preconditions("nonexistent", temp_dir)

        assert exc_info.value.code == 1

    def test_validate_workflow_preconditions_uv_warning(
        self, validation_service, mock_config_store, mock_resource_manager, temp_dir, capsys
    ):
        """Test validate_workflow_preconditions shows warning when uv unavailable."""
        mock_config_store.exists.return_value = True
        mock_resource_manager.validate_workflow_exists.return_value = True
        mock_config_store.get_active_workflow.return_value = None

        with patch.object(validation_service, 'check_uv_available', return_value=False):
            validation_service.validate_workflow_preconditions("test-workflow", temp_dir)

        captured = capsys.readouterr()
        assert "Warning: 'uv' not available" in captured.err

    def test_validate_workflow_preconditions_workflow_switch_accept(
        self, validation_service, mock_config_store, mock_resource_manager, temp_dir
    ):
        """Test validate_workflow_preconditions with workflow switch accepted."""
        mock_config_store.exists.return_value = True
        mock_resource_manager.validate_workflow_exists.return_value = True
        mock_config_store.get_active_workflow.return_value = "old-workflow"

        with patch.object(validation_service, 'check_uv_available', return_value=True):
            with patch('builtins.input', return_value='y'):
                # Should not raise
                validation_service.validate_workflow_preconditions("new-workflow", temp_dir)

    def test_validate_workflow_preconditions_workflow_switch_decline(
        self, validation_service, mock_config_store, mock_resource_manager, temp_dir
    ):
        """Test validate_workflow_preconditions with workflow switch declined."""
        mock_config_store.exists.return_value = True
        mock_resource_manager.validate_workflow_exists.return_value = True
        mock_config_store.get_active_workflow.return_value = "old-workflow"

        with patch.object(validation_service, 'check_uv_available', return_value=True):
            with patch('builtins.input', return_value='n'):
                with pytest.raises(SystemExit) as exc_info:
                    validation_service.validate_workflow_preconditions("new-workflow", temp_dir)

                assert exc_info.value.code == 1

    def test_validate_workflow_preconditions_workflow_switch_eof(
        self, validation_service, mock_config_store, mock_resource_manager, temp_dir
    ):
        """Test validate_workflow_preconditions with EOF on input."""
        mock_config_store.exists.return_value = True
        mock_resource_manager.validate_workflow_exists.return_value = True
        mock_config_store.get_active_workflow.return_value = "old-workflow"

        with patch.object(validation_service, 'check_uv_available', return_value=True):
            with patch('builtins.input', side_effect=EOFError()):
                with pytest.raises(SystemExit) as exc_info:
                    validation_service.validate_workflow_preconditions("new-workflow", temp_dir)

                assert exc_info.value.code == 1

    def test_validate_workflow_preconditions_workflow_switch_interrupt(
        self, validation_service, mock_config_store, mock_resource_manager, temp_dir
    ):
        """Test validate_workflow_preconditions with keyboard interrupt."""
        mock_config_store.exists.return_value = True
        mock_resource_manager.validate_workflow_exists.return_value = True
        mock_config_store.get_active_workflow.return_value = "old-workflow"

        with patch.object(validation_service, 'check_uv_available', return_value=True):
            with patch('builtins.input', side_effect=KeyboardInterrupt()):
                with pytest.raises(SystemExit) as exc_info:
                    validation_service.validate_workflow_preconditions("new-workflow", temp_dir)

                assert exc_info.value.code == 1

    def test_validate_workflow_preconditions_same_workflow(
        self, validation_service, mock_config_store, mock_resource_manager, temp_dir
    ):
        """Test validate_workflow_preconditions with same workflow (no prompt)."""
        mock_config_store.exists.return_value = True
        mock_resource_manager.validate_workflow_exists.return_value = True
        mock_config_store.get_active_workflow.return_value = "test-workflow"

        with patch.object(validation_service, 'check_uv_available', return_value=True):
            # Should not prompt, should not raise
            validation_service.validate_workflow_preconditions("test-workflow", temp_dir)

    def test_validate_removal_preconditions_success(
        self, validation_service, mock_config_store, temp_dir
    ):
        """Test validate_removal_preconditions with active workflow."""
        mock_config_store.exists.return_value = True
        mock_config_store.get_active_workflow.return_value = "test-workflow"

        # Should not raise
        validation_service.validate_removal_preconditions(temp_dir)

    def test_validate_removal_preconditions_not_initialized(
        self, validation_service, mock_config_store, temp_dir
    ):
        """Test validate_removal_preconditions when not initialized."""
        mock_config_store.exists.return_value = False

        with pytest.raises(SystemExit) as exc_info:
            validation_service.validate_removal_preconditions(temp_dir)

        assert exc_info.value.code == 1

    def test_validate_removal_preconditions_no_active_workflow(
        self, validation_service, mock_config_store, temp_dir
    ):
        """Test validate_removal_preconditions when no active workflow."""
        mock_config_store.exists.return_value = True
        mock_config_store.get_active_workflow.return_value = None

        with pytest.raises(SystemExit) as exc_info:
            validation_service.validate_removal_preconditions(temp_dir)

        assert exc_info.value.code == 0

    def test_validate_removal_preconditions_default_dir(
        self, validation_service, mock_config_store
    ):
        """Test validate_removal_preconditions with default directory."""
        mock_config_store.exists.return_value = True
        mock_config_store.get_active_workflow.return_value = "test-workflow"

        validation_service.validate_removal_preconditions()

        # When no target_dir provided, it converts to Path.cwd()
        # Just verify it was called (the path will be the actual cwd)
        assert mock_config_store.exists.called
        assert mock_config_store.get_active_workflow.called
