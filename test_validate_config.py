#!/usr/bin/env python3
"""Test script for config validation with the broken config example."""

import json
import sys
import tempfile
from pathlib import Path

# Add hooks directory to path
sys.path.insert(0, 'resources/workflows/feature-implementation/hooks')

from validate_config import (
    validate_structure,
    validate_config_for_hooks,
    format_validation_error
)

# The broken config from the user
BROKEN_CONFIG = {
    "synapse_version": "0.1.0",
    "initialized_at": "2025-11-02T12:40:32.295018",
    "project": {
        "name": "test-project",
        "root_directory": "/tmp/test"
    },
    "workflows": {
        "active_workflow": "feature-implementation",
        "applied_workflows": []
    },
    "settings": {
        "auto_backup": True,
        "strict_validation": True
    },
    "quality-config": {
        "projectType": "fullstack-python-typescript",
        "subprojects": {
            "backend": {
                "projectType": "python",
                "directory": "backend/",
                "commands": {
                    "lint": "cd backend && ruff check .",
                    "test": "cd backend && pytest"
                },
                "thresholds": {
                    "coverage": {
                        "statements": 0,
                        "branches": 0,
                        "functions": 0,
                        "lines": 0
                    },
                    "lintLevel": "strict"
                }
            }
        }
    }
}

# A valid config for comparison
VALID_CONFIG = {
    "synapse_version": "0.1.0",
    "initialized_at": "2025-11-02T12:40:32.295018",
    "project": {
        "name": "test-project",
        "root_directory": "/tmp/test"
    },
    "workflows": {
        "active_workflow": "feature-implementation",
        "applied_workflows": []
    },
    "settings": {
        "auto_backup": True,
        "strict_validation": True
    },
    "quality-config": {
        "projectType": "python",
        "commands": {
            "lint": "ruff check .",
            "test": "pytest"
        },
        "thresholds": {
            "coverage": {
                "statements": 80,
                "branches": 75,
                "functions": 80,
                "lines": 80
            },
            "lintLevel": "strict"
        }
    }
}

# Config missing required fields
INCOMPLETE_CONFIG = {
    "synapse_version": "0.1.0",
    # Missing project, workflows, settings
}

# Config with quality-config but missing commands
MISSING_COMMANDS_CONFIG = {
    "synapse_version": "0.1.0",
    "project": {
        "name": "test-project",
        "root_directory": "/tmp/test"
    },
    "workflows": {
        "active_workflow": "feature-implementation",
        "applied_workflows": []
    },
    "settings": {
        "auto_backup": True
    },
    "quality-config": {
        "projectType": "python",
        "thresholds": {
            "lintLevel": "strict"
        }
        # Missing "commands"
    }
}


def test_broken_config():
    """Test that broken config is correctly identified."""
    print("=" * 80)
    print("TEST 1: Broken Config (subprojects structure)")
    print("=" * 80)

    is_valid, error_msg = validate_structure(BROKEN_CONFIG)

    print(f"\nResult: {'✅ PASS' if not is_valid else '❌ FAIL'}")
    print("Expected: is_valid=False (broken config should be invalid)")
    print(f"Got: is_valid={is_valid}")
    print(f"Error: {error_msg}\n")

    assert not is_valid, "Broken config should be invalid"
    assert "subprojects" in error_msg, "Error should mention subprojects"

    print("✅ Test passed: Broken config correctly identified\n")


def test_valid_config():
    """Test that valid config passes validation."""
    print("=" * 80)
    print("TEST 2: Valid Config (flat structure)")
    print("=" * 80)

    is_valid, error_msg = validate_structure(VALID_CONFIG)

    print(f"\nResult: {'✅ PASS' if is_valid else '❌ FAIL'}")
    print("Expected: is_valid=True (valid config should pass)")
    print(f"Got: is_valid={is_valid}")
    print(f"Error: {error_msg}\n")

    assert is_valid, "Valid config should pass"

    print("✅ Test passed: Valid config correctly accepted\n")


def test_incomplete_config():
    """Test that config missing required fields is rejected."""
    print("=" * 80)
    print("TEST 3: Incomplete Config (missing required fields)")
    print("=" * 80)

    is_valid, error_msg = validate_structure(INCOMPLETE_CONFIG)

    print(f"\nResult: {'✅ PASS' if not is_valid else '❌ FAIL'}")
    print("Expected: is_valid=False (incomplete config should be invalid)")
    print(f"Got: is_valid={is_valid}")
    print(f"Error: {error_msg}\n")

    assert not is_valid, "Incomplete config should be invalid"
    assert "Missing required fields" in error_msg, "Error should mention missing fields"

    print("✅ Test passed: Incomplete config correctly rejected\n")


def test_missing_commands():
    """Test that config with quality-config but missing commands is rejected."""
    print("=" * 80)
    print("TEST 4: Config with quality-config but missing commands")
    print("=" * 80)

    is_valid, error_msg = validate_structure(MISSING_COMMANDS_CONFIG)

    print(f"\nResult: {'✅ PASS' if not is_valid else '❌ FAIL'}")
    print("Expected: is_valid=False (missing commands should be invalid)")
    print(f"Got: is_valid={is_valid}")
    print(f"Error: {error_msg}\n")

    assert not is_valid, "Config missing commands should be invalid"
    assert "commands" in error_msg.lower(), "Error should mention commands"

    print("✅ Test passed: Missing commands correctly detected\n")


def test_full_validation_with_broken_config():
    """Test full validation with temporary config file."""
    print("=" * 80)
    print("TEST 5: Full Validation (broken config in temp file)")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".synapse"
        config_dir.mkdir()
        config_path = config_dir / "config.json"

        with open(config_path, 'w') as f:
            json.dump(BROKEN_CONFIG, f, indent=2)

        is_valid, summary, issues = validate_config_for_hooks(
            config_path=str(config_path)
        )

        print(f"\nResult: {'✅ PASS' if not is_valid else '❌ FAIL'}")
        print("Expected: is_valid=False")
        print(f"Got: is_valid={is_valid}")
        print(f"Summary: {summary}")
        print("Issues:")
        for issue in issues:
            print(f"  - {issue}")

        error_formatted = format_validation_error(summary, issues)
        print("\nFormatted error message:")
        print(error_formatted)

        assert not is_valid, "Broken config should fail full validation"

    print("\n✅ Test passed: Full validation correctly identifies broken config\n")


def test_full_validation_with_valid_config():
    """Test full validation with valid config."""
    print("=" * 80)
    print("TEST 6: Full Validation (valid config in temp file)")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".synapse"
        config_dir.mkdir()
        config_path = config_dir / "config.json"

        with open(config_path, 'w') as f:
            json.dump(VALID_CONFIG, f, indent=2)

        is_valid, summary, issues = validate_config_for_hooks(
            config_path=str(config_path)
        )

        print(f"\nResult: {'✅ PASS' if is_valid else '❌ FAIL'}")
        print("Expected: is_valid=True")
        print(f"Got: is_valid={is_valid}")
        print(f"Summary: {summary}")
        print("Details:")
        for detail in issues:
            print(f"  - {detail}")

        assert is_valid, "Valid config should pass full validation"

    print("\n✅ Test passed: Full validation accepts valid config\n")


if __name__ == "__main__":
    print("\n🧪 Running Config Validation Tests (Structure Only)\n")

    try:
        test_broken_config()
        test_valid_config()
        test_incomplete_config()
        test_missing_commands()
        test_full_validation_with_broken_config()
        test_full_validation_with_valid_config()

        print("=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
