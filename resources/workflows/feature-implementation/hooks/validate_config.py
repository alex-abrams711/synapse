"""
Config validation module for Synapse quality gate hooks.

This module validates .synapse/config.json structure against the schema
to ensure compatibility with quality gate hooks.
"""

import json
import os
from typing import Tuple, List, Dict, Any, Optional


def load_config(config_path: str = ".synapse/config.json") -> Optional[Dict[str, Any]]:
    """Load and parse the Synapse config file."""
    if not os.path.exists(config_path):
        return None

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def load_schema() -> Dict[str, Any]:
    """Load the Synapse config schema."""
    # Try to load schema from resources directory
    schema_paths = [
        "resources/schemas/synapse-config-schema.json",
        "../../../schemas/synapse-config-schema.json",
        "../../schemas/synapse-config-schema.json",
    ]

    for schema_path in schema_paths:
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                return json.load(f)

    # If schema file not found, return inline minimal schema
    return {
        "required": ["synapse_version", "project", "workflows", "settings"],
        "quality-config-required": ["commands", "thresholds"]
    }


def validate_structure(config: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate that config structure is compatible with quality gate hooks.

    Current hooks expect:
        config["quality-config"]["commands"] = {lint, test, ...}
        config["quality-config"]["thresholds"] = {coverage, lintLevel}

    Incompatible structure (from monorepo projects):
        config["quality-config"]["subprojects"]["backend"]["commands"] = {...}

    Returns:
        (is_valid, error_message)
    """
    # Validate top-level required fields
    required_fields = ["synapse_version", "project", "workflows", "settings"]
    missing_fields = [field for field in required_fields if field not in config]

    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"

    # Check quality-config structure if it exists
    quality_config = config.get("quality-config")

    if quality_config:
        # Check for subprojects structure (incompatible)
        if "subprojects" in quality_config:
            return False, (
                "Config uses 'subprojects' structure which is incompatible with current hooks. "
                "Expected flat structure with top-level 'commands' and 'thresholds'. "
                "Run '/sense' to regenerate config in compatible format."
            )

        # Check for required sections in quality-config
        if "commands" not in quality_config:
            return False, "Missing 'commands' section in quality-config"

        if "thresholds" not in quality_config:
            return False, "Missing 'thresholds' section in quality-config"

        # Validate that commands is an object (not subprojects)
        if not isinstance(quality_config["commands"], dict):
            return False, "'commands' must be an object with quality check commands"

        # Validate that thresholds is an object
        if not isinstance(quality_config["thresholds"], dict):
            return False, "'thresholds' must be an object with quality thresholds"

    return True, "Config structure is valid"


def validate_config_for_hooks(
    config_path: str = ".synapse/config.json"
) -> Tuple[bool, str, List[str]]:
    """
    Validate config structure for compatibility with quality gate hooks.

    Returns:
        (is_valid, error_summary, detailed_issues)
    """
    # Load config
    config = load_config(config_path)
    if config is None:
        return False, "Config file not found or invalid JSON", [
            f"Could not load {config_path}",
            "Run 'synapse init' to initialize project, then '/sense' to generate config"
        ]

    # Validate structure
    is_valid, error_msg = validate_structure(config)

    if not is_valid:
        return False, "Config structure incompatible with hooks", [error_msg]

    # If we get here, config is valid
    details = []

    # Add informational context about quality-config if it exists
    quality_config = config.get("quality-config")
    if quality_config:
        project_type = quality_config.get("projectType", "unknown")
        details.append(f"Project type: {project_type}")

        commands = quality_config.get("commands", {})
        command_list = [k for k, v in commands.items() if v]
        if command_list:
            details.append(f"Quality commands configured: {', '.join(command_list)}")
        else:
            details.append("No quality commands configured")

        thresholds = quality_config.get("thresholds", {})
        lint_level = thresholds.get("lintLevel", "not set")
        details.append(f"Lint level: {lint_level}")

    return True, "Config is valid and compatible with hooks", details


def format_validation_error(error_summary: str, detailed_issues: List[str]) -> str:
    """Format validation error for display in hook output."""
    lines = [
        "❌ Config Validation Failed",
        "",
        error_summary,
        "",
        "Issues:",
    ]

    for issue in detailed_issues:
        if issue.startswith("WARNING:"):
            lines.append(f"  ⚠️  {issue}")
        else:
            lines.append(f"  • {issue}")

    lines.extend([
        "",
        "Required Action:",
        "  Run '/synapse:sense' to regenerate .synapse/config.json in the correct format",
        "",
        "The '/synapse:sense' command will:",
        "  1. Analyze your project structure",
        "  2. Detect quality tools and commands",
        "  3. Generate appropriate quality thresholds",
        "  4. Create a config compatible with quality gate hooks"
    ])

    return "\n".join(lines)
