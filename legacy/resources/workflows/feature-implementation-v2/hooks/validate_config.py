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


def validate_monorepo_structure(quality_config: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate monorepo quality-config structure.

    Returns:
        (is_valid, error_message)
    """
    if "projects" not in quality_config:
        return False, "Monorepo mode requires 'projects' object"

    projects = quality_config["projects"]
    if not isinstance(projects, dict) or len(projects) == 0:
        return False, "'projects' must be non-empty object"

    # Validate each project has required fields
    for project_name, project_config in projects.items():
        if not isinstance(project_config, dict):
            return False, f"Project '{project_name}' must be an object"

        # Check for required fields
        if "directory" not in project_config:
            return False, f"Project '{project_name}' missing 'directory' field"

        if "commands" not in project_config:
            return False, f"Project '{project_name}' missing 'commands' field"

        if "thresholds" not in project_config:
            return False, f"Project '{project_name}' missing 'thresholds' field"

        # Validate directory is a string ending with /
        directory = project_config["directory"]
        if not isinstance(directory, str):
            return False, f"Project '{project_name}' directory must be a string"

        if not directory.endswith("/"):
            return False, f"Project '{project_name}' directory must end with '/'"

        if directory.startswith("/"):
            return False, f"Project '{project_name}' directory must be relative (not start with '/')"

        # Validate commands structure
        if not isinstance(project_config["commands"], dict):
            return False, f"Project '{project_name}' commands must be object"

        # Validate thresholds structure
        if not isinstance(project_config["thresholds"], dict):
            return False, f"Project '{project_name}' thresholds must be object"

    return True, "Monorepo structure is valid"


def validate_single_structure(quality_config: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate single-project quality-config structure.

    Returns:
        (is_valid, error_message)
    """
    # Check for required sections in quality-config
    if "commands" not in quality_config:
        return False, "Single mode requires 'commands' section in quality-config"

    if "thresholds" not in quality_config:
        return False, "Single mode requires 'thresholds' section in quality-config"

    # Validate that commands is an object
    if not isinstance(quality_config["commands"], dict):
        return False, "'commands' must be an object with quality check commands"

    # Validate that thresholds is an object
    if not isinstance(quality_config["thresholds"], dict):
        return False, "'thresholds' must be an object with quality thresholds"

    # Check that projects doesn't exist (mutually exclusive)
    if "projects" in quality_config:
        return False, "Single mode cannot have 'projects' field. Set mode='monorepo' for multi-project configs"

    return True, "Single structure is valid"


def validate_structure(config: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate that config structure is compatible with quality gate hooks.

    Supports both single-project and monorepo modes:
        Single mode (default): config["quality-config"]["commands"], ["thresholds"]
        Monorepo mode: config["quality-config"]["projects"]["backend"]["commands"], etc.

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
        # Detect mode (defaults to "single")
        mode = quality_config.get("mode", "single")

        if mode not in ["single", "monorepo"]:
            return False, f"Invalid mode '{mode}'. Must be 'single' or 'monorepo'"

        # Validate based on mode
        if mode == "monorepo":
            is_valid, error_msg = validate_monorepo_structure(quality_config)
            if not is_valid:
                return False, f"Monorepo validation failed: {error_msg}"
        else:  # single mode
            is_valid, error_msg = validate_single_structure(quality_config)
            if not is_valid:
                return False, f"Single mode validation failed: {error_msg}"

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
        mode = quality_config.get("mode", "single")
        details.append(f"Mode: {mode}")

        if mode == "single":
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

        elif mode == "monorepo":
            projects = quality_config.get("projects", {})
            details.append(f"Projects: {len(projects)}")

            for project_name, project_config in projects.items():
                project_type = project_config.get("projectType", "unknown")
                directory = project_config.get("directory", "")
                details.append(f"  - {project_name} ({directory}) [{project_type}]")

                commands = project_config.get("commands", {})
                command_list = [k for k, v in commands.items() if v]
                if command_list:
                    details.append(f"    Commands: {', '.join(command_list)}")

                thresholds = project_config.get("thresholds", {})
                lint_level = thresholds.get("lintLevel", "not set")
                details.append(f"    Lint level: {lint_level}")

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
