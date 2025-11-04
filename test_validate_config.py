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

# Valid monorepo config
VALID_MONOREPO_CONFIG = {
    "synapse_version": "0.1.0",
    "initialized_at": "2025-11-02T12:40:32.295018",
    "project": {
        "name": "test-monorepo",
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
        "mode": "monorepo",
        "projects": {
            "backend": {
                "directory": "backend/",
                "projectType": "python",
                "commands": {
                    "lint": "cd backend && ruff check .",
                    "test": "cd backend && pytest"
                },
                "thresholds": {
                    "lintLevel": "strict"
                }
            },
            "frontend": {
                "directory": "frontend/",
                "projectType": "node",
                "commands": {
                    "lint": "cd frontend && npm run lint",
                    "test": "cd frontend && npm test"
                },
                "thresholds": {
                    "lintLevel": "flexible"
                }
            }
        }
    }
}

# Invalid: monorepo mode missing projects
INVALID_MONOREPO_MISSING_PROJECTS = {
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
        "mode": "monorepo"
        # Missing "projects"
    }
}

# Invalid: monorepo project missing directory field
INVALID_MONOREPO_MISSING_DIRECTORY = {
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
        "mode": "monorepo",
        "projects": {
            "backend": {
                # Missing "directory"
                "projectType": "python",
                "commands": {
                    "lint": "ruff check ."
                },
                "thresholds": {
                    "lintLevel": "strict"
                }
            }
        }
    }
}

# Invalid: monorepo with empty projects
INVALID_MONOREPO_EMPTY_PROJECTS = {
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
        "mode": "monorepo",
        "projects": {}
    }
}

# Invalid: single mode with projects field
INVALID_SINGLE_WITH_PROJECTS = {
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
        "mode": "single",
        "commands": {
            "lint": "ruff check ."
        },
        "thresholds": {
            "lintLevel": "strict"
        },
        "projects": {  # Invalid: single mode can't have projects
            "backend": {}
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


def test_valid_monorepo_config():
    """Test that valid monorepo config passes validation."""
    print("=" * 80)
    print("TEST 1: Valid Monorepo Config")
    print("=" * 80)

    is_valid, error_msg = validate_structure(VALID_MONOREPO_CONFIG)

    print(f"\nResult: {'✅ PASS' if is_valid else '❌ FAIL'}")
    print("Expected: is_valid=True (valid monorepo config should pass)")
    print(f"Got: is_valid={is_valid}")
    print(f"Message: {error_msg}\n")

    assert is_valid, f"Valid monorepo config should pass. Error: {error_msg}"

    print("✅ Test passed: Valid monorepo config correctly accepted\n")


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


def test_monorepo_missing_projects():
    """Test that monorepo mode without projects is rejected."""
    print("=" * 80)
    print("TEST 7: Monorepo Missing Projects")
    print("=" * 80)

    is_valid, error_msg = validate_structure(INVALID_MONOREPO_MISSING_PROJECTS)

    print(f"\nResult: {'✅ PASS' if not is_valid else '❌ FAIL'}")
    print("Expected: is_valid=False (monorepo without projects should be invalid)")
    print(f"Got: is_valid={is_valid}")
    print(f"Error: {error_msg}\n")

    assert not is_valid, "Monorepo without projects should be invalid"
    assert "projects" in error_msg.lower(), "Error should mention projects"

    print("✅ Test passed: Monorepo missing projects correctly rejected\n")


def test_monorepo_missing_directory():
    """Test that monorepo project without directory is rejected."""
    print("=" * 80)
    print("TEST 8: Monorepo Project Missing Directory")
    print("=" * 80)

    is_valid, error_msg = validate_structure(INVALID_MONOREPO_MISSING_DIRECTORY)

    print(f"\nResult: {'✅ PASS' if not is_valid else '❌ FAIL'}")
    print("Expected: is_valid=False (project without directory should be invalid)")
    print(f"Got: is_valid={is_valid}")
    print(f"Error: {error_msg}\n")

    assert not is_valid, "Project without directory should be invalid"
    assert "directory" in error_msg.lower(), "Error should mention directory"

    print("✅ Test passed: Missing directory correctly detected\n")


def test_monorepo_empty_projects():
    """Test that monorepo with empty projects is rejected."""
    print("=" * 80)
    print("TEST 9: Monorepo with Empty Projects")
    print("=" * 80)

    is_valid, error_msg = validate_structure(INVALID_MONOREPO_EMPTY_PROJECTS)

    print(f"\nResult: {'✅ PASS' if not is_valid else '❌ FAIL'}")
    print("Expected: is_valid=False (empty projects should be invalid)")
    print(f"Got: is_valid={is_valid}")
    print(f"Error: {error_msg}\n")

    assert not is_valid, "Empty projects should be invalid"
    assert "non-empty" in error_msg.lower() or "empty" in error_msg.lower(), "Error should mention empty/non-empty"

    print("✅ Test passed: Empty projects correctly rejected\n")


def test_single_mode_with_projects():
    """Test that single mode with projects field is rejected."""
    print("=" * 80)
    print("TEST 10: Single Mode with Projects Field")
    print("=" * 80)

    is_valid, error_msg = validate_structure(INVALID_SINGLE_WITH_PROJECTS)

    print(f"\nResult: {'✅ PASS' if not is_valid else '❌ FAIL'}")
    print("Expected: is_valid=False (single mode can't have projects)")
    print(f"Got: is_valid={is_valid}")
    print(f"Error: {error_msg}\n")

    assert not is_valid, "Single mode with projects should be invalid"
    assert "projects" in error_msg.lower() or "single" in error_msg.lower(), "Error should mention projects or single mode"

    print("✅ Test passed: Single mode with projects correctly rejected\n")


def test_full_validation_monorepo():
    """Test full validation with monorepo config."""
    print("=" * 80)
    print("TEST 11: Full Validation (monorepo config)")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".synapse"
        config_dir.mkdir()
        config_path = config_dir / "config.json"

        with open(config_path, 'w') as f:
            json.dump(VALID_MONOREPO_CONFIG, f, indent=2)

        is_valid, summary, details = validate_config_for_hooks(
            config_path=str(config_path)
        )

        print(f"\nResult: {'✅ PASS' if is_valid else '❌ FAIL'}")
        print("Expected: is_valid=True")
        print(f"Got: is_valid={is_valid}")
        print(f"Summary: {summary}")
        print("Details:")
        for detail in details:
            print(f"  {detail}")

        assert is_valid, "Valid monorepo config should pass full validation"
        assert any("monorepo" in d.lower() for d in details), "Details should mention monorepo mode"

    print("\n✅ Test passed: Full validation accepts monorepo config\n")


if __name__ == "__main__":
    print("\n🧪 Running Config Validation Tests (Single & Monorepo Modes)\n")

    try:
        # Monorepo mode tests
        test_valid_monorepo_config()

        # Single mode tests
        test_valid_config()
        test_incomplete_config()
        test_missing_commands()

        # Full validation tests
        test_full_validation_with_valid_config()
        test_full_validation_monorepo()

        # Monorepo error case tests
        test_monorepo_missing_projects()
        test_monorepo_missing_directory()
        test_monorepo_empty_projects()
        test_single_mode_with_projects()

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
