"""Unit tests for template integration service."""

import tempfile
from pathlib import Path

import pytest

from synapse.models.template import TemplateConfig
from synapse.services.integrator import (
    AnalysisResult,
    IntegrationResult,
    TemplateIntegrationError,
    TemplateIntegrator,
    ValidationResult,
)


class TestTemplateIntegrator:
    """Test TemplateIntegrator service."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.integrator = TemplateIntegrator()

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_integrator_initialization(self) -> None:
        """Test TemplateIntegrator initialization."""
        assert self.integrator.template_dir.exists()
        assert self.integrator.jinja_env is not None
        assert hasattr(self.integrator, '_template_cache')

    def test_analyze_nonexistent_file(self) -> None:
        """Test analyzing non-existent CLAUDE.md file."""
        nonexistent_path = self.temp_path / "nonexistent.md"

        result = self.integrator.analyze_claude_md(str(nonexistent_path), "1.0.0")

        assert isinstance(result, AnalysisResult)
        assert result.file_exists is False
        assert result.content_sections == {}
        assert result.user_content_slots == {}
        assert result.integration_strategy == "template_replacement"
        assert result.backup_required is False

    def test_analyze_existing_file(self) -> None:
        """Test analyzing existing CLAUDE.md file."""
        # Create test CLAUDE.md file
        test_file = self.temp_path / "CLAUDE.md"
        test_content = """# Project Context

This is my project context.

## Custom Instructions

These are my custom instructions.

# Synapse Agent Workflow System

Existing synapse content.
"""
        test_file.write_text(test_content)

        result = self.integrator.analyze_claude_md(str(test_file), "1.0.0")

        assert result.file_exists is True
        assert len(result.content_sections) > 0
        assert "project_context" in result.content_sections
        assert result.backup_required is True

    def test_extract_content_sections_performance(self) -> None:
        """Test content section extraction performance with caching."""
        # Create large content
        large_content = "# Large Project\n\n" + "## Section\nContent\n" * 1000

        # First call should populate cache
        result1 = self.integrator._extract_content_sections(large_content)

        # Second call should use cache (faster)
        result2 = self.integrator._extract_content_sections(large_content)

        assert result1 == result2
        assert len(result1) > 0

    def test_extract_content_sections_no_headers(self) -> None:
        """Test content extraction with no headers."""
        content = "This is content without headers."

        result = self.integrator._extract_content_sections(content)

        assert "content" in result
        assert result["content"] == content.strip()

    def test_extract_content_sections_multiple_headers(self) -> None:
        """Test content extraction with multiple headers."""
        content = """# First Header

First content.

## Second Header

Second content.

### Third Header

Third content.
"""

        result = self.integrator._extract_content_sections(content)

        assert "first_header" in result
        assert "second_header" in result
        assert "third_header" in result
        assert "First content." in result["first_header"]

    def test_map_to_template_slots(self) -> None:
        """Test mapping content sections to template slots."""
        sections = {
            "project_context": "My project context",
            "custom_instructions": "My instructions",
            "important_notes": "Important notes",
            "synapse_agent_workflow_system": "Synapse content"
        }

        result = self.integrator._map_to_template_slots(sections)

        assert "user_context_slot" in result
        assert "user_instructions_slot" in result
        assert result["user_context_slot"] == "My project context"
        assert result["user_instructions_slot"] == "My instructions"

    def test_file_content_caching(self) -> None:
        """Test file content caching."""
        # Create test file
        test_file = self.temp_path / "test.md"
        test_content = "# Test Content\n\nThis is test content."
        test_file.write_text(test_content)

        # First load should cache content
        content1 = self.integrator._load_file_content(str(test_file))

        # Second load should use cache
        content2 = self.integrator._load_file_content(str(test_file))

        assert content1 == content2
        assert content1 == test_content

    def test_get_file_hash(self) -> None:
        """Test file hash generation."""
        # Create test file
        test_file = self.temp_path / "test.md"
        test_content = "# Test Content"
        test_file.write_text(test_content)

        hash1 = self.integrator._get_file_hash(str(test_file))

        # Hash should be consistent
        hash2 = self.integrator._get_file_hash(str(test_file))
        assert hash1 == hash2

        # Hash should change if content changes
        test_file.write_text("# Different Content")
        hash3 = self.integrator._get_file_hash(str(test_file))
        assert hash1 != hash3

    def test_integrate_template_with_backup(self) -> None:
        """Test template integration with backup creation."""
        # Create source file
        source_file = self.temp_path / "CLAUDE.md"
        source_content = """# Project Context

My project context.

## Instructions

My instructions.
"""
        source_file.write_text(source_content)

        # Create template config
        template_config = TemplateConfig(
            template_version="1.0.0",
            user_content_slots={
                "user_context_slot": "My project context.",
                "user_instructions_slot": "My instructions."
            }
        )

        result = self.integrator.integrate_template(
            source_file=str(source_file),
            template_config=template_config,
            integration_strategy="slot_based",
            create_backup=True
        )

        assert isinstance(result, IntegrationResult)
        assert result.success is True
        assert result.backup_file is not None
        assert Path(result.backup_file).exists()

    def test_integrate_template_without_backup(self) -> None:
        """Test template integration without backup creation."""
        # Create source file
        source_file = self.temp_path / "CLAUDE.md"
        source_content = "# Test Content"
        source_file.write_text(source_content)

        # Create template config
        template_config = TemplateConfig(
            template_version="1.0.0",
            user_content_slots={}
        )

        result = self.integrator.integrate_template(
            source_file=str(source_file),
            template_config=template_config,
            integration_strategy="template_replacement",
            create_backup=False
        )

        assert result.success is True
        assert result.backup_file is None

    def test_integrate_template_nonexistent_source(self) -> None:
        """Test template integration with non-existent source file."""
        nonexistent_file = self.temp_path / "nonexistent.md"

        template_config = TemplateConfig(
            template_version="1.0.0",
            user_content_slots={}
        )

        with pytest.raises(TemplateIntegrationError):
            self.integrator.integrate_template(
                source_file=str(nonexistent_file),
                template_config=template_config,
                integration_strategy="template_replacement"
            )

    def test_backup_creation(self) -> None:
        """Test backup file creation."""
        # Create source file
        source_file = self.temp_path / "test.md"
        source_content = "Test content"
        source_file.write_text(source_content)

        backup_path = self.integrator._create_backup(source_file)

        assert Path(backup_path).exists()
        assert Path(backup_path).read_text() == source_content
        assert "_backup_" in backup_path

    def test_render_template(self) -> None:
        """Test template rendering."""
        template_config = TemplateConfig(
            template_version="1.0.0",
            user_content_slots={
                "user_context_slot": "Test context",
                "user_instructions_slot": "Test instructions"
            }
        )

        result = self.integrator._render_template(template_config)

        assert "Test context" in result
        assert "Test instructions" in result
        assert "Synapse Agent Workflow System" in result

    def test_render_template_with_synapse_commands(self) -> None:
        """Test template rendering with synapse commands."""
        template_config = TemplateConfig(
            template_version="1.0.0",
            user_content_slots={}
        )

        result = self.integrator._render_template(template_config)

        # Should contain synapse command definitions
        assert "/synapse:plan" in result
        assert "/synapse:implement" in result
        assert "/synapse:review" in result

    def test_get_synapse_commands(self) -> None:
        """Test getting synapse commands."""
        commands = self.integrator._get_synapse_commands()

        assert len(commands) > 0
        expected_commands = ["plan", "implement", "review", "dev", "audit", "dispatch"]

        for cmd in expected_commands:
            found = any(command["name"] == cmd for command in commands)
            assert found, f"Command {cmd} not found in synapse commands"

    def test_validate_integration_successful(self) -> None:
        """Test successful integration validation."""
        # Create integrated file
        integrated_file = self.temp_path / "integrated.md"
        integrated_content = """# Project Context

Test context

## Instructions

Test instructions

# Synapse Agent Workflow System
"""
        integrated_file.write_text(integrated_content)

        original_content = {
            "user_context_slot": "Test context",
            "user_instructions_slot": "Test instructions"
        }

        result = self.integrator.validate_integration(
            integrated_file=str(integrated_file),
            original_content=original_content,
            template_version="1.0.0"
        )

        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert len(result.validation_errors) == 0

    def test_validate_integration_missing_content(self) -> None:
        """Test integration validation with missing content."""
        # Create integrated file without expected content
        integrated_file = self.temp_path / "integrated.md"
        integrated_content = "# Synapse Agent Workflow System"
        integrated_file.write_text(integrated_content)

        original_content = {
            "user_context_slot": "Missing context",
            "user_instructions_slot": "Missing instructions"
        }

        result = self.integrator.validate_integration(
            integrated_file=str(integrated_file),
            original_content=original_content,
            template_version="1.0.0"
        )

        assert result.is_valid is False
        assert len(result.validation_errors) > 0

    def test_validate_integration_nonexistent_file(self) -> None:
        """Test validation with non-existent integrated file."""
        nonexistent_file = self.temp_path / "nonexistent.md"

        result = self.integrator.validate_integration(
            integrated_file=str(nonexistent_file),
            original_content={},
            template_version="1.0.0"
        )

        assert result.is_valid is False
        assert len(result.validation_errors) > 0


class TestAnalysisResult:
    """Test AnalysisResult model."""

    def test_analysis_result_creation(self) -> None:
        """Test AnalysisResult creation."""
        result = AnalysisResult(
            file_exists=True,
            content_sections={"section1": "content1"},
            user_content_slots={"slot1": "value1"},
            integration_strategy="slot_based",
            backup_required=True
        )

        assert result.file_exists is True
        assert result.content_sections["section1"] == "content1"
        assert result.user_content_slots["slot1"] == "value1"
        assert result.integration_strategy == "slot_based"
        assert result.backup_required is True


class TestIntegrationResult:
    """Test IntegrationResult model."""

    def test_integration_result_creation(self) -> None:
        """Test IntegrationResult creation."""
        result = IntegrationResult(
            success=True,
            output_file="/path/to/output.md",
            backup_file="/path/to/backup.md",
            preserved_content={"slot1": "content1"},
            warnings=["Warning message"]
        )

        assert result.success is True
        assert result.output_file == "/path/to/output.md"
        assert result.backup_file == "/path/to/backup.md"
        assert result.preserved_content["slot1"] == "content1"
        assert len(result.warnings) == 1


class TestValidationResult:
    """Test ValidationResult model."""

    def test_validation_result_creation(self) -> None:
        """Test ValidationResult creation."""
        result = ValidationResult(
            is_valid=True,
            validation_errors=[],
            content_integrity={"slots_preserved": 2, "slots_lost": 0}
        )

        assert result.is_valid is True
        assert len(result.validation_errors) == 0
        assert result.content_integrity["slots_preserved"] == 2


class TestTemplateIntegrationError:
    """Test TemplateIntegrationError exception."""

    def test_template_integration_error(self) -> None:
        """Test TemplateIntegrationError creation."""
        error = TemplateIntegrationError("Test error message")
        assert str(error) == "Test error message"

        with pytest.raises(TemplateIntegrationError):
            raise TemplateIntegrationError("Test exception")


class TestIntegratorPerformance:
    """Test TemplateIntegrator performance characteristics."""

    def test_large_file_analysis_performance(self) -> None:
        """Test performance with large files."""
        import time

        integrator = TemplateIntegrator()

        # Create large content
        large_content = "# Large Project\n\n" + "## Section\nContent\n" * 1000

        start_time = time.time()
        result = integrator._extract_content_sections(large_content)
        end_time = time.time()

        processing_time = end_time - start_time

        # Should complete quickly due to optimizations
        assert processing_time < 0.1  # Less than 100ms
        assert len(result) > 0

    def test_template_caching_performance(self) -> None:
        """Test template caching improves performance."""
        import time

        integrator = TemplateIntegrator()

        template_config = TemplateConfig(
            template_version="1.0.0",
            user_content_slots={}
        )

        # First render (cache miss)
        start_time = time.time()
        result1 = integrator._render_template(template_config)
        first_time = time.time() - start_time

        # Second render (cache hit should be faster or same)
        start_time = time.time()
        result2 = integrator._render_template(template_config)
        second_time = time.time() - start_time

        assert result1 == result2
        # Second call should not be significantly slower
        assert second_time <= first_time * 2
