"""CLI commands for managing CLAUDE.md templates and template integration."""

from pathlib import Path

import click

from synapse.models.template import TemplateConfig
from synapse.services.integrator import TemplateIntegrator
from synapse.services.validator import TemplateValidator


@click.group()
def template() -> None:
    """Manage CLAUDE.md templates and template integration."""
    pass


@template.command()
@click.option(
    "--file", default="CLAUDE.md", help="CLAUDE.md file to analyze (default: CLAUDE.md)", type=str
)
@click.option(
    "--template-version",
    default="1.0.0",
    help="Template version to use for analysis (default: 1.0.0)",
    type=str,
)
def analyze(file: str, template_version: str) -> None:
    """Analyze existing CLAUDE.md file for template integration potential."""
    file_path = Path(file)

    if not file_path.exists():
        click.echo(click.style(f"✗ File not found: {file}", fg="red"))
        return

    click.echo(f"Analyzing {file} for template integration...")

    try:
        integrator = TemplateIntegrator()
        result = integrator.analyze_claude_md(str(file_path), template_version)

        click.echo("\nAnalysis Results:")
        click.echo("=" * 40)
        click.echo(f"File exists: {'Yes' if result.file_exists else 'No'}")
        click.echo(f"Integration strategy: {result.integration_strategy}")
        click.echo(f"Backup required: {'Yes' if result.backup_required else 'No'}")

        if result.content_sections:
            click.echo(f"\nContent Sections Found ({len(result.content_sections)}):")
            for section_name, content in result.content_sections.items():
                content_preview = content[:100] + "..." if len(content) > 100 else content
                click.echo(f"  • {section_name}: {len(content)} chars")
                click.echo(f"    Preview: {content_preview}")

        if result.user_content_slots:
            click.echo(f"\nMappable Content Slots ({len(result.user_content_slots)}):")
            for slot_name, content in result.user_content_slots.items():
                click.echo(f"  • {slot_name}: {len(content)} chars")

        if result.parsing_errors:
            click.echo(click.style(f"\nWarnings ({len(result.parsing_errors)}):", fg="yellow"))
            for error in result.parsing_errors:
                click.echo(click.style(f"  ⚠ {error}", fg="yellow"))

        # Recommendations
        click.echo("\n💡 Recommendations:")
        if result.integration_strategy == "slot_based":
            click.echo("  • Use slot-based integration to preserve user content")
        elif result.integration_strategy == "hybrid":
            click.echo("  • Use hybrid integration with manual content mapping")
        else:
            click.echo("  • Use template replacement (no user content to preserve)")

        if result.backup_required:
            click.echo("  • Create backup before integration")

    except Exception as e:
        click.echo(click.style(f"✗ Analysis failed: {e}", fg="red"))


@template.command()
@click.option(
    "--file", default="CLAUDE.md", help="CLAUDE.md file to integrate (default: CLAUDE.md)", type=str
)
@click.option("--project-name", help="Project name for template context", type=str)
@click.option(
    "--preserve-content/--no-preserve-content",
    default=True,
    help="Preserve existing user content (default: enabled)",
)
@click.option(
    "--create-backup/--no-create-backup",
    default=True,
    help="Create backup before integration (default: enabled)",
)
@click.option(
    "--force-backup", is_flag=True, help="Force backup creation even if integration fails"
)
@click.option(
    "--strategy",
    type=click.Choice(["slot_based", "template_replacement", "hybrid"]),
    help="Integration strategy (default: auto-detect)",
)
def integrate(
    file: str,
    project_name: str | None,
    preserve_content: bool,
    create_backup: bool,
    force_backup: bool,
    strategy: str | None,
) -> None:
    """Integrate CLAUDE.md file with Synapse template."""
    file_path = Path(file)

    # Auto-detect project name if not provided
    if not project_name:
        project_name = file_path.parent.name

    click.echo(f"Integrating {file} with Synapse template...")
    click.echo(f"Project: {project_name}")
    click.echo(f"Preserve content: {'Yes' if preserve_content else 'No'}")
    click.echo(f"Create backup: {'Yes' if create_backup else 'No'}")

    try:
        integrator = TemplateIntegrator()

        # Analyze file first
        if file_path.exists():
            analysis = integrator.analyze_claude_md(str(file_path), "1.0.0")

            # Use detected strategy if none specified
            if not strategy:
                strategy = analysis.integration_strategy

            click.echo(f"Strategy: {strategy}")

            # Create template config
            template_config = TemplateConfig(
                template_version="1.0.0",
                user_content_slots=analysis.user_content_slots if preserve_content else {},
                backup_created=False,
                integration_date=None,
                original_file_hash=analysis.file_hash,
            )

            # Add project name
            template_config.add_content_slot("project_name", project_name)

        else:
            # New file
            click.echo("Creating new CLAUDE.md file")
            template_config = TemplateConfig(
                template_version="1.0.0", user_content_slots={"project_name": project_name}
            )
            strategy = "template_replacement"

        # Perform integration
        result = integrator.integrate_template(
            str(file_path),
            template_config,
            integration_strategy=strategy,
            create_backup=create_backup or force_backup,
        )

        # Display results
        if result.success:
            click.echo(click.style("✓ Template integration successful!", fg="green"))

            if result.output_file:
                click.echo(f"Generated: {result.output_file}")

            if result.backup_file:
                click.echo(f"Backup: {result.backup_file}")

            if result.preserved_content:
                click.echo(f"Content preserved: {len(result.preserved_content)} slots")

            # Validate integration
            click.echo("\nValidating integration...")
            validator = TemplateValidator()
            validation = validator.validate_template_integration(template_config, str(file_path))

            if validation.is_valid:
                click.echo(click.style("✓ Integration validation passed", fg="green"))
            else:
                click.echo(click.style("⚠ Integration validation warnings:", fg="yellow"))
                for error in validation.errors:
                    click.echo(click.style(f"  • {error}", fg="yellow"))

        else:
            click.echo(click.style("✗ Template integration failed!", fg="red"))

        if result.warnings:
            click.echo(click.style(f"\nWarnings ({len(result.warnings)}):", fg="yellow"))
            for warning in result.warnings:
                click.echo(click.style(f"  ⚠ {warning}", fg="yellow"))

    except Exception as e:
        click.echo(click.style(f"✗ Integration failed: {e}", fg="red"))


@template.command()
@click.option(
    "--file", default="CLAUDE.md", help="CLAUDE.md file to validate (default: CLAUDE.md)", type=str
)
@click.option(
    "--template-type",
    type=click.Choice(["claude", "command"]),
    default="claude",
    help="Type of template to validate (default: claude)",
)
@click.option("--command-name", help="Command name for command template validation", type=str)
def validate(file: str, template_type: str, command_name: str | None) -> None:
    """Validate template file structure and content."""
    file_path = Path(file)

    if not file_path.exists():
        click.echo(click.style(f"✗ File not found: {file}", fg="red"))
        return

    click.echo(f"Validating {file} as {template_type} template...")

    try:
        content = file_path.read_text(encoding="utf-8")
        validator = TemplateValidator()

        if template_type == "claude":
            # Validate as CLAUDE.md template
            if file_path.suffix == ".j2":
                # Jinja2 template
                result = validator.validate_jinja_template(content)
            else:
                # Regular CLAUDE.md
                result = validator.validate_context_template(content)

        elif template_type == "command":
            # Validate as command template
            if not command_name:
                command_name = file_path.stem.replace("synapse-", "")

            result = validator.validate_command_template_syntax(content, command_name)

        # Display results
        if result.is_valid:
            click.echo(click.style("✓ Template validation passed!", fg="green"))
        else:
            click.echo(click.style("✗ Template validation failed!", fg="red"))

        if result.errors:
            click.echo(click.style(f"\nErrors ({len(result.errors)}):", fg="red"))
            for error in result.errors:
                click.echo(click.style(f"  ✗ {error}", fg="red"))

        if result.warnings:
            click.echo(click.style(f"\nWarnings ({len(result.warnings)}):", fg="yellow"))
            for warning in result.warnings:
                click.echo(click.style(f"  ⚠ {warning}", fg="yellow"))

    except Exception as e:
        click.echo(click.style(f"✗ Validation failed: {e}", fg="red"))


@template.command()
@click.option(
    "--source",
    default="synapse/templates/claude/CLAUDE.md.j2",
    help="Source template file (default: built-in template)",
    type=str,
)
@click.option("--output", default="CLAUDE.md", help="Output file (default: CLAUDE.md)", type=str)
@click.option("--project-name", prompt=True, help="Project name for template context")
@click.option("--user-context", help="User context content", type=str)
@click.option("--user-instructions", help="User instructions content", type=str)
@click.option("--user-guidelines", help="User guidelines content", type=str)
def render(
    source: str,
    output: str,
    project_name: str,
    user_context: str | None,
    user_instructions: str | None,
    user_guidelines: str | None,
) -> None:
    """Render template with provided context."""
    source_path = Path(source)

    if not source_path.exists():
        click.echo(click.style(f"✗ Template not found: {source}", fg="red"))
        return

    click.echo(f"Rendering template {source} → {output}")
    click.echo(f"Project: {project_name}")

    try:
        # Create template config
        template_config = TemplateConfig(
            template_version="1.0.0",
            user_content_slots={
                "project_name": project_name,
                "user_context_slot": user_context or "",
                "user_instructions_slot": user_instructions or "",
                "user_guidelines_slot": user_guidelines or "",
                "user_metadata_slot": "",
            },
        )

        # Use integrator to render
        integrator = TemplateIntegrator()
        result = integrator.integrate_template(
            output,
            template_config,
            integration_strategy="template_replacement",
            create_backup=False,
        )

        if result.success:
            click.echo(click.style("✓ Template rendered successfully!", fg="green"))
            click.echo(f"Output: {result.output_file}")
        else:
            click.echo(click.style("✗ Template rendering failed!", fg="red"))
            for warning in result.warnings:
                click.echo(click.style(f"  • {warning}", fg="red"))

    except Exception as e:
        click.echo(click.style(f"✗ Rendering failed: {e}", fg="red"))


@template.command(name="list")
@click.option(
    "--template-dir",
    default="synapse/templates/claude",
    help="Template directory to list (default: synapse/templates/claude)",
    type=str,
)
def list_templates(template_dir: str) -> None:
    """List available templates."""
    template_path = Path(template_dir)

    if not template_path.exists():
        click.echo(click.style(f"✗ Template directory not found: {template_dir}", fg="red"))
        return

    click.echo(f"Templates in {template_dir}:")
    click.echo("=" * 40)

    # List main templates
    claude_templates = list(template_path.glob("*.j2"))
    if claude_templates:
        click.echo("\n📄 CLAUDE.md Templates:")
        for template in claude_templates:
            size = template.stat().st_size
            click.echo(f"  • {template.name} ({size} bytes)")

    # List command templates
    commands_dir = template_path / "commands"
    if commands_dir.exists():
        command_templates = list(commands_dir.glob("*.md"))
        if command_templates:
            click.echo(f"\n⚡ Command Templates ({len(command_templates)}):")
            for template in sorted(command_templates):
                size = template.stat().st_size
                click.echo(f"  • {template.name} ({size} bytes)")

    # Show total count
    command_count = len(list(commands_dir.glob("*.md"))) if commands_dir.exists() else 0
    total_templates = len(claude_templates) + command_count
    click.echo(f"\nTotal: {total_templates} templates")


def register_template_group(cli_group: click.Group) -> None:
    """Register the template group with the main CLI."""
    cli_group.add_command(template)
