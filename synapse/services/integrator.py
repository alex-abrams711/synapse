"""Template integration service for CLAUDE.md and command management."""

import hashlib
import shutil
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from synapse.models.template import (
    TemplateConfig,
)


class TemplateIntegrationError(Exception):
    """Error during template integration process."""

    pass


class AnalysisResult:
    """Result of analyzing existing CLAUDE.md file."""

    def __init__(
        self,
        file_exists: bool,
        content_sections: dict[str, str],
        user_content_slots: dict[str, str],
        integration_strategy: str,
        backup_required: bool,
        file_hash: str = "",
        has_warnings: bool = False,
        parsing_errors: list[str] | None = None,
    ):
        """Initialize analysis result."""
        self.file_exists = file_exists
        self.content_sections = content_sections
        self.user_content_slots = user_content_slots
        self.integration_strategy = integration_strategy
        self.backup_required = backup_required
        self.file_hash = file_hash
        self.has_warnings = has_warnings
        self.parsing_errors = parsing_errors or []


class IntegrationResult:
    """Result of template integration process."""

    def __init__(
        self,
        success: bool,
        output_file: str | None = None,
        backup_file: str | None = None,
        preserved_content: dict[str, str] | None = None,
        warnings: list[str] | None = None,
    ):
        """Initialize integration result."""
        self.success = success
        self.output_file = output_file
        self.backup_file = backup_file
        self.preserved_content = preserved_content or {}
        self.warnings = warnings or []


class ValidationResult:
    """Result of template validation."""

    def __init__(
        self,
        is_valid: bool,
        validation_errors: list[str],
        content_integrity: dict[str, Any],
    ):
        """Initialize validation result."""
        self.is_valid = is_valid
        self.validation_errors = validation_errors
        self.content_integrity = content_integrity


class TemplateIntegrator:
    """Service for integrating CLAUDE.md templates with user content preservation."""

    def __init__(self, template_dir: str | None = None):
        """Initialize template integrator.

        Args:
            template_dir: Directory containing Jinja2 templates.
                         Defaults to synapse/templates/claude.
        """
        if template_dir is None:
            # Get the synapse package directory
            synapse_dir = Path(__file__).parent.parent
            template_dir = str(synapse_dir / "templates" / "claude")

        self.template_dir = Path(template_dir)
        self._template_cache: dict[str, str] = {}
        self._setup_jinja_env()

    def _setup_jinja_env(self) -> None:
        """Set up Jinja2 environment with markdown-safe delimiters."""
        try:
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                block_start_string="{%",
                block_end_string="%}",
                variable_start_string="{{{",  # Triple to avoid markdown conflicts
                variable_end_string="}}}",
                comment_start_string="{#",
                comment_end_string="#}",
                trim_blocks=True,
                lstrip_blocks=True,
                # Enable template caching for performance
                cache_size=100,
                auto_reload=False,  # Disable auto-reload for performance
            )
        except Exception as e:
            raise TemplateIntegrationError(f"Failed to setup Jinja2 environment: {e}")

    def _load_file_content(self, file_path: str) -> str:
        """Load file content."""
        return Path(file_path).read_text(encoding="utf-8")

    def _get_file_hash(self, file_path: str) -> str:
        """Get hash of file content for cache validation."""
        if not Path(file_path).exists():
            raise TemplateIntegrationError(f"File not found: {file_path}")
        content = self._load_file_content(file_path)
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def analyze_claude_md(self, file_path: str, template_version: str) -> AnalysisResult:
        """Analyze existing CLAUDE.md file for template integration.

        Args:
            file_path: Path to existing CLAUDE.md file
            template_version: Version of template to use

        Returns:
            AnalysisResult with analysis findings
        """
        path = Path(file_path)

        if not path.exists():
            return AnalysisResult(
                file_exists=False,
                content_sections={},
                user_content_slots={},
                integration_strategy="template_replacement",
                backup_required=False,
            )

        try:
            content = self._load_file_content(file_path)
            file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

            # Extract user content sections
            content_sections = self._extract_content_sections(content)
            user_content_slots = self._map_to_template_slots(content_sections)

            # Determine integration strategy
            strategy = self._determine_integration_strategy(content_sections)

            return AnalysisResult(
                file_exists=True,
                content_sections=content_sections,
                user_content_slots=user_content_slots,
                integration_strategy=strategy,
                backup_required=True,
                file_hash=file_hash,
            )

        except Exception as e:
            return AnalysisResult(
                file_exists=True,
                content_sections={},
                user_content_slots={},
                integration_strategy="template_replacement",
                backup_required=True,
                has_warnings=True,
                parsing_errors=[f"Failed to analyze file: {e}"],
            )

    def integrate_template(
        self,
        source_file: str,
        template_config: TemplateConfig,
        integration_strategy: str = "slot_based",
        create_backup: bool = True,
    ) -> IntegrationResult:
        """Integrate CLAUDE.md template with user content.

        Args:
            source_file: Path to source CLAUDE.md file
            template_config: Template configuration with user content
            integration_strategy: Strategy for integration
            create_backup: Whether to create backup before integration

        Returns:
            IntegrationResult with integration status
        """
        try:
            source_path = Path(source_file)
            backup_file = None

            # Raise error if source doesn't exist and backup is requested
            if create_backup and not source_path.exists():
                raise TemplateIntegrationError(f"Source file does not exist: {source_file}")

            # Create backup if requested and file exists
            if create_backup and source_path.exists():
                backup_file = self._create_backup(source_path)

            # Load and render template
            template_content = self._render_claude_template(template_config)

            # Ensure parent directory exists
            source_path.parent.mkdir(parents=True, exist_ok=True)

            # Write integrated content
            source_path.write_text(template_content, encoding="utf-8")

            return IntegrationResult(
                success=True,
                output_file=str(source_path),
                backup_file=backup_file,
                preserved_content=template_config.user_content_slots,
            )

        except TemplateIntegrationError:
            # Re-raise template integration errors
            raise
        except Exception as e:
            return IntegrationResult(
                success=False,
                warnings=[f"Integration failed: {e}"],
            )

    def validate_integration(
        self,
        integrated_file: str,
        original_content: dict[str, str],
        template_version: str,
    ) -> ValidationResult:
        """Validate template integration results.

        Args:
            integrated_file: Path to integrated CLAUDE.md file
            original_content: Original user content that should be preserved
            template_version: Version of template used

        Returns:
            ValidationResult with validation status
        """
        try:
            path = Path(integrated_file)
            if not path.exists():
                return ValidationResult(
                    is_valid=False,
                    validation_errors=["Integrated file does not exist"],
                    content_integrity={},
                )

            integrated_content = path.read_text(encoding="utf-8")

            # Check content preservation
            content_integrity = self._validate_content_preservation(
                integrated_content, original_content
            )

            validation_errors = []
            if content_integrity["slots_lost"] > 0:
                validation_errors.append(f"Lost {content_integrity['slots_lost']} content slots")

            return ValidationResult(
                is_valid=len(validation_errors) == 0,
                validation_errors=validation_errors,
                content_integrity=content_integrity,
            )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                validation_errors=[f"Validation failed: {e}"],
                content_integrity={},
            )

    @lru_cache(maxsize=64)
    def _extract_content_sections(self, content: str) -> dict[str, str]:
        """Extract content sections from existing CLAUDE.md with performance optimization."""
        sections = {}

        # Use regex for faster header detection on large files
        import re

        header_pattern = re.compile(r"^(#+)\s*(.*)$", re.MULTILINE)
        matches = list(header_pattern.finditer(content))

        if not matches:
            # No headers found, treat as single section
            return {"content": content.strip()}

        for i, match in enumerate(matches):
            section_name = match.group(2).strip().lower().replace(" ", "_")

            # Get content between this header and next
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)

            section_content = content[start_pos:end_pos].strip()
            if section_content:
                sections[section_name] = section_content

        return sections

    def _map_to_template_slots(self, sections: dict[str, str]) -> dict[str, str]:
        """Map content sections to template slots."""
        slot_mapping = {
            "project_context": "user_context_slot",
            "context": "user_context_slot",
            "custom_instructions": "user_instructions_slot",
            "instructions": "user_instructions_slot",
            "project_guidelines": "user_guidelines_slot",
            "guidelines": "user_guidelines_slot",
            "additional_information": "user_metadata_slot",
            "metadata": "user_metadata_slot",
        }

        user_slots = {}
        for section, content in sections.items():
            slot_name = slot_mapping.get(section)
            if slot_name and content.strip():
                user_slots[slot_name] = content.strip()

        return user_slots

    def _determine_integration_strategy(self, content_sections: dict[str, str]) -> str:
        """Determine best integration strategy based on content."""
        if not content_sections:
            return "template_replacement"

        # If we can map most content to slots, use slot-based
        mappable_sections = sum(
            1
            for section in content_sections.keys()
            if section
            in [
                "project_context",
                "context",
                "custom_instructions",
                "instructions",
                "project_guidelines",
                "guidelines",
            ]
        )

        if mappable_sections >= len(content_sections) * 0.7:
            return "slot_based"
        else:
            return "hybrid"

    def _render_claude_template(self, config: TemplateConfig) -> str:
        """Render CLAUDE.md template with user content."""
        try:
            template = self.jinja_env.get_template("CLAUDE.md.j2")

            # Prepare template context
            # Use a fixed date if none provided for consistent rendering
            default_date = datetime(2025, 1, 1, 12, 0, 0)
            context = {
                "project_name": config.user_content_slots.get("project_name", "Project"),
                "initialization_date": (
                    config.integration_date.isoformat()
                    if config.integration_date
                    else default_date.isoformat()
                ),
                "user_context_slot": config.user_content_slots.get("user_context_slot", ""),
                "user_instructions_slot": config.user_content_slots.get(
                    "user_instructions_slot", ""
                ),
                "user_guidelines_slot": config.user_content_slots.get("user_guidelines_slot", ""),
                "user_metadata_slot": config.user_content_slots.get("user_metadata_slot", ""),
                "synapse_commands": self._get_synapse_commands(),
            }

            return template.render(**context)

        except TemplateNotFound:
            raise TemplateIntegrationError("CLAUDE.md.j2 template not found")
        except Exception as e:
            raise TemplateIntegrationError(f"Failed to render template: {e}")

    def _render_template(self, config: TemplateConfig) -> str:
        """Render template with user content (backward compatibility alias)."""
        return self._render_claude_template(config)

    def _get_synapse_commands(self) -> list[dict[str, str]]:
        """Get list of synapse commands for template."""
        commands = [
            {
                "name": "plan",
                "description": "Planning and task analysis with DISPATCHER agent",
                "file_name": "synapse-plan.md",
            },
            {
                "name": "implement",
                "description": "Code implementation and development with DEV agent",
                "file_name": "synapse-implement.md",
            },
            {
                "name": "review",
                "description": "Quality assurance and code review with AUDITOR agent",
                "file_name": "synapse-review.md",
            },
            {
                "name": "dev",
                "description": "Direct communication with DEV agent",
                "file_name": "synapse-dev.md",
            },
            {
                "name": "audit",
                "description": "Direct communication with AUDITOR agent",
                "file_name": "synapse-audit.md",
            },
            {
                "name": "dispatch",
                "description": "Direct communication with DISPATCHER agent",
                "file_name": "synapse-dispatch.md",
            },
        ]
        return commands

    def _create_backup(self, source_path: Path) -> str:
        """Create backup of source file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = (
            source_path.parent / f"{source_path.stem}_backup_{timestamp}{source_path.suffix}"
        )

        shutil.copy2(source_path, backup_path)
        return str(backup_path)

    def restore_from_backup(self, backup_file: str, target_file: str | None = None) -> bool:
        """Restore file from backup.

        Args:
            backup_file: Path to backup file
            target_file: Path to target file to restore to (optional)

        Returns:
            True if restoration was successful, False otherwise
        """
        backup_path = Path(backup_file)

        if not backup_path.exists():
            return False

        try:
            # Determine target file path
            if target_file:
                target_path = Path(target_file)
            else:
                # Extract original filename from backup name
                # Pattern: filename_backup_timestamp.extension
                stem = backup_path.stem
                if "_backup_" in stem:
                    original_stem = stem.split("_backup_")[0]
                    target_path = backup_path.parent / f"{original_stem}{backup_path.suffix}"
                else:
                    # Fallback: remove backup extension
                    target_path = backup_path.parent / backup_path.name.replace("_backup", "")

            # Copy backup to target location
            shutil.copy2(backup_path, target_path)
            return True

        except Exception:
            return False

    def list_backups(self, file_path: str) -> list[str]:
        """List available backup files for a given file.

        Args:
            file_path: Path to the original file

        Returns:
            List of backup file paths, sorted by creation time (newest first)
        """
        source_path = Path(file_path)
        backup_pattern = f"{source_path.stem}_backup_*{source_path.suffix}"

        backup_files = []
        for backup_file in source_path.parent.glob(backup_pattern):
            backup_files.append(str(backup_file))

        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: Path(x).stat().st_mtime, reverse=True)
        return backup_files

    def _validate_content_preservation(
        self, integrated_content: str, original_content: dict[str, str]
    ) -> dict[str, Any]:
        """Validate that user content was preserved in integration."""
        preserved = 0
        lost = 0

        for _slot_name, content in original_content.items():
            if content.strip() and content.strip() in integrated_content:
                preserved += 1
            else:
                lost += 1

        return {
            "slots_preserved": preserved,
            "slots_lost": lost,
            "preservation_rate": preserved / (preserved + lost) if (preserved + lost) > 0 else 1.0,
        }
