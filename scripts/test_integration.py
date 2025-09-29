#!/usr/bin/env python3
"""
Synapse Agent Workflow System - Integration Test Script

This script provides automated testing of the complete Synapse initialization
and verification process. It can be run to validate that the system works
correctly across different environments and configurations.

Usage:
    python scripts/test_integration.py
    python scripts/test_integration.py --project-name "Custom Test"
    python scripts/test_integration.py --keep-project  # Don't delete after test
    python scripts/test_integration.py --verbose       # Detailed output
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from typing import Any

import yaml


class SynapseIntegrationTest:
    """Comprehensive integration test for Synapse Agent Workflow System."""

    def __init__(self, project_name: str = "Integration Test Project",
                 keep_project: bool = False, verbose: bool = False):
        self.project_name = project_name
        self.keep_project = keep_project
        self.verbose = verbose
        self.test_dir = None
        self.original_dir = os.getcwd()
        self.results = {
            "start_time": None,
            "end_time": None,
            "total_duration": None,
            "status": "PENDING",
            "phases": {},
            "verification_results": {},
            "errors": [],
            "warnings": []
        }

        # Expected file structure
        self.expected_files = {
            "agents": [
                ".claude/agents/dev.md",
                ".claude/agents/auditor.md",
                ".claude/agents/dispatcher.md"
            ],
            "commands": [
                # Basic workflow commands
                ".claude/commands/status.md",
                ".claude/commands/workflow.md",
                ".claude/commands/validate.md",
                ".claude/commands/agent.md",
                # Enhanced synapse-prefixed commands
                ".claude/commands/synapse-plan.md",
                ".claude/commands/synapse-implement.md",
                ".claude/commands/synapse-review.md",
                ".claude/commands/synapse-dev.md",
                ".claude/commands/synapse-audit.md",
                ".claude/commands/synapse-dispatch.md"
            ],
            "workflow": [
                ".synapse/config.yaml",
                ".synapse/task_log.json",
                ".synapse/workflow_state.json"
            ],
            "root": [
                "CLAUDE.md"
            ]
        }

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp and level."""
        timestamp = time.strftime("%H:%M:%S")
        prefix = f"[{timestamp}] {level:5s}"

        if level == "ERROR":
            print(f"\033[91m{prefix}\033[0m {message}")
        elif level == "WARN":
            print(f"\033[93m{prefix}\033[0m {message}")
        elif level == "SUCCESS":
            print(f"\033[92m{prefix}\033[0m {message}")
        elif self.verbose or level in ["INFO", "SUCCESS", "ERROR", "WARN"]:
            print(f"{prefix} {message}")

    def run_command(self, cmd: list[str], cwd: str | None = None) -> tuple[int, str, str]:
        """Run command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.test_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out after 30 seconds"
        except Exception as e:
            return -1, "", str(e)

    def phase_1_setup(self) -> bool:
        """Phase 1: Create test project directory."""
        self.log("Phase 1: Setting up test project directory")
        phase_start = time.time()

        try:
            # Create temporary test directory
            self.test_dir = os.path.join(self.original_dir, f"test-integration-{int(time.time())}")
            os.makedirs(self.test_dir, exist_ok=True)
            self.log(f"Created test directory: {self.test_dir}")

            # Verify we can write to the directory
            test_file = os.path.join(self.test_dir, ".test_write")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)

            self.results["phases"]["setup"] = {
                "status": "SUCCESS",
                "duration": time.time() - phase_start,
                "test_dir": self.test_dir
            }
            self.log("Phase 1: Setup completed successfully", "SUCCESS")
            return True

        except Exception as e:
            self.results["phases"]["setup"] = {
                "status": "FAILED",
                "duration": time.time() - phase_start,
                "error": str(e)
            }
            self.results["errors"].append(f"Setup failed: {e}")
            self.log(f"Phase 1: Setup failed - {e}", "ERROR")
            return False

    def phase_2_initialization(self) -> bool:
        """Phase 2: Run synapse init command."""
        self.log("Phase 2: Running synapse initialization")
        phase_start = time.time()

        try:
            # Build the synapse init command
            cmd = [
                sys.executable, "-m", "synapse.cli.main", "init",
                "--project-name", self.project_name,
                "--template-integration",
                "--preserve-content",
                "--detect-conflicts"
            ]

            self.log(f"Executing: {' '.join(cmd)}")

            # Run synapse init
            exit_code, stdout, stderr = self.run_command(cmd, cwd=self.test_dir)

            if exit_code != 0:
                raise Exception(f"synapse init failed with exit code {exit_code}: {stderr}")

            self.results["phases"]["initialization"] = {
                "status": "SUCCESS",
                "duration": time.time() - phase_start,
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr
            }

            if self.verbose:
                self.log("Init output:")
                for line in stdout.split('\n'):
                    if line.strip():
                        self.log(f"  {line}")

            self.log("Phase 2: Initialization completed successfully", "SUCCESS")
            return True

        except Exception as e:
            self.results["phases"]["initialization"] = {
                "status": "FAILED",
                "duration": time.time() - phase_start,
                "error": str(e)
            }
            self.results["errors"].append(f"Initialization failed: {e}")
            self.log(f"Phase 2: Initialization failed - {e}", "ERROR")
            return False

    def verify_file_exists(self, file_path: str) -> dict[str, Any]:
        """Verify a single file exists and has valid content."""
        full_path = os.path.join(self.test_dir, file_path)
        result = {
            "path": file_path,
            "exists": False,
            "size": 0,
            "readable": False,
            "valid_content": False,
            "content_type": None,
            "errors": []
        }

        try:
            if os.path.exists(full_path):
                result["exists"] = True
                result["size"] = os.path.getsize(full_path)

                try:
                    with open(full_path, encoding='utf-8') as f:
                        content = f.read()
                        result["readable"] = True

                        # Validate content based on file type
                        if file_path.endswith('.yaml'):
                            yaml.safe_load(content)
                            result["valid_content"] = True
                            result["content_type"] = "yaml"
                        elif file_path.endswith('.json'):
                            json.loads(content)
                            result["valid_content"] = True
                            result["content_type"] = "json"
                        elif file_path.endswith('.md'):
                            result["valid_content"] = len(content.strip()) > 0
                            result["content_type"] = "markdown"
                        else:
                            result["valid_content"] = len(content.strip()) > 0
                            result["content_type"] = "text"

                except Exception as e:
                    result["errors"].append(f"Content validation failed: {e}")

        except Exception as e:
            result["errors"].append(f"File access failed: {e}")

        return result

    def phase_3_verification(self) -> bool:
        """Phase 3: Verify all expected files and configurations."""
        self.log("Phase 3: Verifying created files and configurations")
        phase_start = time.time()

        verification_results = {}
        all_passed = True

        # Verify each category of files
        for category, files in self.expected_files.items():
            self.log(f"Verifying {category} files...")
            category_results = {}

            for file_path in files:
                result = self.verify_file_exists(file_path)
                category_results[file_path] = result

                if result["exists"] and result["valid_content"]:
                    self.log(f"  ✓ {file_path}", "SUCCESS")
                else:
                    self.log(f"  ✗ {file_path} - {'missing' if not result['exists'] else 'invalid content'}", "ERROR")
                    all_passed = False

                if result["errors"]:
                    for error in result["errors"]:
                        self.log(f"    Error: {error}", "ERROR")
                        self.results["errors"].append(f"{file_path}: {error}")

            verification_results[category] = category_results

        # Verify specific configuration content
        config_valid = self.verify_configuration()
        verification_results["configuration_validation"] = config_valid

        if not config_valid:
            all_passed = False

        self.results["phases"]["verification"] = {
            "status": "SUCCESS" if all_passed else "FAILED",
            "duration": time.time() - phase_start,
            "files_verified": sum(len(files) for files in self.expected_files.values()),
            "all_files_valid": all_passed
        }

        self.results["verification_results"] = verification_results

        if all_passed:
            self.log("Phase 3: Verification completed successfully", "SUCCESS")
        else:
            self.log("Phase 3: Verification failed - some files missing or invalid", "ERROR")

        return all_passed

    def verify_configuration(self) -> bool:
        """Verify configuration file contents are correct."""
        self.log("Verifying configuration content...")

        try:
            # Verify config.yaml
            config_path = os.path.join(self.test_dir, ".synapse/config.yaml")
            with open(config_path) as f:
                config = yaml.safe_load(f)

            required_fields = ["project_name", "synapse_version", "workflow_dir",
                              "agents", "claude_commands"]
            for field in required_fields:
                if field not in config:
                    self.log(f"  Missing required field in config: {field}", "ERROR")
                    return False

            # Verify agents configuration
            expected_agents = ["dev", "auditor", "dispatcher"]
            for agent in expected_agents:
                if agent not in config["agents"]:
                    self.log(f"  Missing agent configuration: {agent}", "ERROR")
                    return False

            # Verify task_log.json structure
            task_log_path = os.path.join(self.test_dir, ".synapse/task_log.json")
            with open(task_log_path) as f:
                task_log = json.load(f)

            required_log_fields = ["workflow_id", "project_name", "synapse_version", "entries"]
            for field in required_log_fields:
                if field not in task_log:
                    self.log(f"  Missing required field in task log: {field}", "ERROR")
                    return False

            # Verify workflow_state.json structure
            state_path = os.path.join(self.test_dir, ".synapse/workflow_state.json")
            with open(state_path) as f:
                state = json.load(f)

            required_state_fields = ["workflow_id", "status", "task_queue",
                                     "completed_tasks"]
            for field in required_state_fields:
                if field not in state:
                    self.log(f"  Missing required field in workflow state: {field}", "ERROR")
                    return False

            self.log("  Configuration validation passed", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"  Configuration validation failed: {e}", "ERROR")
            return False

    def phase_4_reporting(self) -> None:
        """Phase 4: Generate comprehensive test report."""
        self.log("Phase 4: Generating test report")
        phase_start = time.time()

        # Calculate totals
        total_files = sum(len(files) for files in self.expected_files.values())
        valid_files = 0

        for category_results in self.results["verification_results"].values():
            if isinstance(category_results, dict):
                for file_result in category_results.values():
                    if (isinstance(file_result, dict) and
                        file_result.get("exists") and
                        file_result.get("valid_content")):
                        valid_files += 1

        # Generate summary
        success_rate = (valid_files / total_files * 100) if total_files > 0 else 0
        overall_status = ("SUCCESS" if success_rate == 100 and
                         len(self.results["errors"]) == 0 else "FAILED")

        self.results["status"] = overall_status
        self.results["phases"]["reporting"] = {
            "status": "SUCCESS",
            "duration": time.time() - phase_start
        }

        # Calculate duration for report (if end_time not set yet, use current time)
        current_time = time.time()
        test_duration = (current_time - self.results["start_time"]
                        if self.results["start_time"] else 0)

        # Print detailed report
        print("\n" + "="*80)
        print("SYNAPSE INTEGRATION TEST REPORT")
        print("="*80)
        print(f"Project Name: {self.project_name}")
        print(f"Test Directory: {self.test_dir}")
        print(f"Overall Status: {overall_status}")
        print(f"Test Duration: {test_duration:.2f} seconds")
        print(f"Success Rate: {success_rate:.1f}% "
              f"({valid_files}/{total_files} files)")

        # Phase summary
        print("\nPHASE SUMMARY:")
        for phase_name, phase_data in self.results["phases"].items():
            status_icon = "✓" if phase_data["status"] == "SUCCESS" else "✗"
            print(f"  {status_icon} {phase_name.title()}: {phase_data['status']} "
                  f"({phase_data['duration']:.2f}s)")

        # File verification details
        print("\nFILE VERIFICATION:")
        for category, files in self.expected_files.items():
            print(f"  {category.title()} Files:")
            for file_path in files:
                if category in self.results["verification_results"]:
                    result = self.results["verification_results"][category].get(
                        file_path, {}
                    )
                    status = ("✓" if result.get("exists") and
                             result.get("valid_content") else "✗")
                    size = result.get("size", 0)
                    print(f"    {status} {file_path} ({size} bytes)")

        # Errors and warnings
        if self.results["errors"]:
            print(f"\nERRORS ({len(self.results['errors'])}):")
            for error in self.results["errors"]:
                print(f"  ✗ {error}")

        if self.results["warnings"]:
            print(f"\nWARNINGS ({len(self.results['warnings'])}):")
            for warning in self.results["warnings"]:
                print(f"  ⚠ {warning}")

        # Configuration details
        if "configuration_validation" in self.results["verification_results"]:
            config_status = ("✓" if
                            self.results["verification_results"]["configuration_validation"]
                            else "✗")
            print(f"\nCONFIGURATION VALIDATION: {config_status}")

        print("="*80)

        if overall_status == "SUCCESS":
            self.log("Integration test completed successfully!", "SUCCESS")
        else:
            self.log("Integration test failed. See report above for details.", "ERROR")

    def phase_5_cleanup(self) -> bool:
        """Phase 5: Clean up test directory."""
        if self.keep_project:
            self.log(f"Phase 5: Keeping test project at {self.test_dir}")
            return True

        self.log("Phase 5: Cleaning up test directory")
        phase_start = time.time()

        try:
            if self.test_dir and os.path.exists(self.test_dir):
                shutil.rmtree(self.test_dir)
                self.log(f"Removed test directory: {self.test_dir}")

            self.results["phases"]["cleanup"] = {
                "status": "SUCCESS",
                "duration": time.time() - phase_start
            }
            self.log("Phase 5: Cleanup completed successfully", "SUCCESS")
            return True

        except Exception as e:
            self.results["phases"]["cleanup"] = {
                "status": "FAILED",
                "duration": time.time() - phase_start,
                "error": str(e)
            }
            self.results["warnings"].append(f"Cleanup failed: {e}")
            self.log(f"Phase 5: Cleanup failed - {e}", "WARN")
            return False

    def run(self) -> bool:
        """Run the complete integration test workflow."""
        self.log("Starting Synapse Integration Test")
        self.results["start_time"] = time.time()

        try:
            # Run all phases in sequence
            phases = [
                ("Setup", self.phase_1_setup),
                ("Initialization", self.phase_2_initialization),
                ("Verification", self.phase_3_verification),
                ("Reporting", self.phase_4_reporting),
                ("Cleanup", self.phase_5_cleanup)
            ]

            for phase_name, phase_func in phases:
                if phase_name == "Reporting":
                    # Reporting always runs
                    phase_func()
                elif phase_name == "Cleanup":
                    # Cleanup runs regardless of previous failures
                    phase_func()
                else:
                    # Other phases must succeed to continue
                    if not phase_func():
                        # Still run reporting and cleanup
                        self.phase_4_reporting()
                        self.phase_5_cleanup()
                        return False

            return self.results["status"] == "SUCCESS"

        finally:
            self.results["end_time"] = time.time()
            self.results["total_duration"] = self.results["end_time"] - self.results["start_time"]


def main():
    """Main entry point for the integration test script."""
    parser = argparse.ArgumentParser(description="Synapse Integration Test")
    parser.add_argument("--project-name", default="Integration Test Project",
                       help="Name for the test project")
    parser.add_argument("--keep-project", action="store_true",
                       help="Keep test project directory after completion")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose output")

    args = parser.parse_args()

    # Run the integration test
    test = SynapseIntegrationTest(
        project_name=args.project_name,
        keep_project=args.keep_project,
        verbose=args.verbose
    )

    success = test.run()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

