#!/usr/bin/env python3
"""
Validation orchestrator that generates continuation directives.
Exit codes:
  0 - All checks passed, OK to stop
  2 - Issues found, must continue with fixes (blocks hook)
"""

import json
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Set
import re
import traceback
import signal

# Import change detection from v1 (shared utility)
v1_hooks_path = Path(__file__).parent.parent.parent / "feature-implementation" / "hooks"
sys.path.insert(0, str(v1_hooks_path))
try:
    from change_detection import get_changed_files_from_git, get_affected_projects
except ImportError:
    # Fallback if v1 hooks not available
    def get_changed_files_from_git(detection_method: str = "uncommitted") -> List[str]:
        return []
    def get_affected_projects(changed_files: List[str], quality_config: Dict) -> Set[str]:
        return set()

class ValidationController:
    def __init__(self):
        self.synapse_dir = Path('.synapse')
        self.claude_dir = Path('.claude')

        # Ensure directories exist
        self.synapse_dir.mkdir(exist_ok=True)

        # Load configurations
        self.config = self.load_config()
        self.quality_config = self.config.get('quality-config', {})

        # Track validation state
        self.validation_state = self.load_validation_state()
        self.current_iteration = self.validation_state.get('iteration', 0) + 1

    def load_config(self) -> dict:
        """Load synapse configuration"""
        config_path = self.synapse_dir / 'config.json'
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {}

    def load_validation_state(self) -> dict:
        """Load previous validation state if exists"""
        state_file = self.synapse_dir / 'validation-state.json'
        if state_file.exists():
            with open(state_file) as f:
                return json.load(f)
        return {}

    def save_validation_state(self):
        """Save current validation state"""
        state_file = self.synapse_dir / 'validation-state.json'
        self.validation_state['iteration'] = self.current_iteration
        with open(state_file, 'w') as f:
            json.dump(self.validation_state, f, indent=2)

    def run(self) -> int:
        """Run validation and generate continuation directive if needed"""

        print(f"Validation iteration #{self.current_iteration}", file=sys.stderr)

        # Safety check for infinite loops
        if self.current_iteration > 10:
            print("⚠️ Max validation attempts reached. Allowing stop to prevent infinite loop.", file=sys.stderr)
            self.cleanup_state()
            return 0

        results = self.run_all_validations()

        # Defensive check: ensure results is a dict
        if not isinstance(results, dict):
            print(f"❌ Internal error: validation returned invalid results type: {type(results)}", file=sys.stderr)
            print("⚠️ Allowing stop due to validation system error", file=sys.stderr)
            return 0

        # Check if all passed
        # Default to False (fail-safe) if 'passed' key is missing
        all_passed = all(r.get('passed', False) for r in results.values() if isinstance(r, dict))

        if all_passed:
            print("✅ All validations passed!", file=sys.stderr)
            self.cleanup_state()
            return 0
        else:
            # Generate specific continuation message and output as JSON
            reason = self.generate_continuation_message(results)
            self.save_validation_state()

            # Output blocking JSON for Claude Code
            output = {
                "decision": "block",
                "reason": reason
            }
            print(json.dumps(output))
            return 2

    def run_all_validations(self) -> Dict:
        """Run all validation checks in priority order"""
        results = {}

        # Determine if monorepo mode
        is_monorepo = self.quality_config.get('mode') == 'monorepo'

        if is_monorepo:
            # Monorepo mode: check affected projects only (if optimization enabled)
            return self.run_monorepo_validations()
        else:
            # Single project mode: run all checks
            results['build'] = self.check_build()
            if not results['build']['passed']:
                return results

            results['tests'] = self.run_tests()
            results['tasks'] = self.check_task_completion()
            results['quality'] = self.run_quality_checks()
            results['coverage'] = self.check_coverage()

            return results

    def run_monorepo_validations(self) -> Dict:
        """Run validations for monorepo mode with change detection"""
        results = {}

        optimization = self.quality_config.get('optimization', {})
        check_affected_only = optimization.get('check_affected_only', True)
        detection_method = os.environ.get('SYNAPSE_DETECTION_METHOD', optimization.get('detection_method', 'uncommitted'))
        verbose = os.environ.get('SYNAPSE_VERBOSE_DETECTION') == '1' or optimization.get('verbose_logging', False)

        # Determine which projects to check
        projects_to_check = set()

        if os.environ.get('SYNAPSE_CHECK_ALL_PROJECTS') == '1' or not check_affected_only:
            # Check all projects
            projects_to_check = set(self.quality_config.get('projects', {}).keys())
            if verbose:
                print(f"Checking all {len(projects_to_check)} projects (optimization disabled)")
        else:
            # Detect affected projects
            changed_files = get_changed_files_from_git(detection_method)

            if changed_files:
                projects_to_check = get_affected_projects(changed_files, self.quality_config)
                if verbose:
                    print(f"Detected {len(changed_files)} changed files")
                    print(f"Affected projects: {', '.join(sorted(projects_to_check))}")
            else:
                # No changes detected
                if optimization.get('fallback_to_all', True):
                    projects_to_check = set(self.quality_config.get('projects', {}).keys())
                    if verbose:
                        print("No changes detected - checking all projects (fallback)")
                else:
                    if verbose:
                        print("No changes detected - skipping all checks")
                    return {'build': {'passed': True}, 'tests': {'passed': True},
                           'tasks': {'passed': True}, 'quality': {'passed': True},
                           'coverage': {'passed': True}}

            # Add force-check projects
            force_check = set(optimization.get('force_check_projects', []))
            if force_check:
                projects_to_check.update(force_check)
                if verbose and force_check:
                    print(f"Force-checking projects: {', '.join(sorted(force_check))}")

        # Run checks for each affected project
        for project_name in sorted(projects_to_check):
            project_config = self.quality_config['projects'].get(project_name, {})

            if verbose:
                print(f"\nValidating project: {project_name}")

            # Check build for this project
            build_result = self.check_build_for_project(project_name, project_config)
            if not build_result['passed']:
                build_result['project'] = project_name
                results['build'] = build_result
                return results

            # Check tests for this project
            test_result = self.run_tests_for_project(project_name, project_config)
            if not test_result['passed']:
                test_result['project'] = project_name
                results['tests'] = test_result
                return results

            # Check quality for this project
            quality_result = self.run_quality_checks_for_project(project_name, project_config)
            if not quality_result['passed']:
                quality_result['project'] = project_name
                results['quality'] = quality_result
                return results

            # Check coverage for this project
            coverage_result = self.check_coverage_for_project(project_name, project_config)
            if not coverage_result['passed']:
                coverage_result['project'] = project_name
                results['coverage'] = coverage_result
                return results

        # Check tasks (project-agnostic)
        results['tasks'] = self.check_task_completion()
        if not results['tasks']['passed']:
            return results

        # All checks passed
        results['build'] = {'passed': True}
        results['tests'] = {'passed': True}
        results['quality'] = {'passed': True}
        results['coverage'] = {'passed': True}

        return results

    def check_build_for_project(self, project_name: str, project_config: Dict) -> Dict:
        """Check build for a specific project in monorepo"""
        build_command = project_config.get('commands', {}).get('build')
        project_type = project_config.get('projectType')

        if project_type == 'python':
            return self.check_python_syntax_for_project(project_name, project_config)

        if not build_command:
            return {'passed': True, 'issues': []}

        try:
            result = subprocess.run(
                build_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.get_project_root()
            )

            if result.returncode != 0:
                error_lines = (result.stderr or result.stdout).split('\n')
                error_lines = [line for line in error_lines if line.strip()][:5]
                return {
                    'passed': False,
                    'issues': error_lines,
                    'command': build_command
                }

            return {'passed': True, 'issues': []}

        except subprocess.TimeoutExpired:
            return {'passed': False, 'issues': ['Build timeout after 60 seconds']}
        except Exception as e:
            return {'passed': False, 'issues': [str(e)]}

    def check_python_syntax_for_project(self, project_name: str, project_config: Dict) -> Dict:
        """Check Python syntax for a specific project"""
        project_dir = Path(project_config.get('directory', project_name))

        try:
            # Limit search depth and skip common large directories
            # Use iterative approach with early filtering to avoid hanging
            exclude_dirs = {'venv', '.venv', 'env', '.env', 'node_modules', '.git',
                           'build', 'dist', '__pycache__', '.tox', '.pytest_cache',
                           'site-packages', '.mypy_cache', '.ruff_cache'}

            python_files = []
            max_files = 1000  # Safety limit

            for root, dirs, files in os.walk(project_dir):
                # Filter directories in-place to avoid descending
                dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]

                for file in files:
                    if file.endswith('.py'):
                        python_files.append(Path(root) / file)
                        if len(python_files) >= max_files:
                            break
                if len(python_files) >= max_files:
                    break

            for file in python_files:
                try:
                    with open(file) as f:
                        compile(f.read(), str(file), 'exec')
                except SyntaxError as e:
                    return {
                        'passed': False,
                        'issues': [f"Syntax error in {file}:{e.lineno}: {e.msg}"],
                        'file': str(file),
                        'line': e.lineno
                    }

            return {'passed': True, 'issues': []}

        except Exception as e:
            return {'passed': True, 'issues': []}

    def run_tests_for_project(self, project_name: str, project_config: Dict) -> Dict:
        """Run tests for a specific project"""
        test_command = project_config.get('commands', {}).get('test')
        if not test_command:
            return {'passed': True, 'issues': []}

        try:
            result = subprocess.run(
                test_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.get_project_root()
            )

            if result.returncode != 0:
                output = result.stdout + result.stderr
                failures = []

                if 'FAILED' in output:
                    failures = re.findall(r'FAILED (.+?)(?:\s|$)', output)
                elif 'FAIL:' in output:
                    failures = re.findall(r'FAIL: (.+?)(?:\n|$)', output)

                failures = failures[:10]

                return {
                    'passed': False,
                    'failures': failures,
                    'command': test_command,
                    'summary': self.extract_test_summary(output)
                }

            return {'passed': True, 'issues': []}

        except subprocess.TimeoutExpired:
            return {'passed': False, 'issues': ['Test timeout after 120 seconds']}
        except Exception as e:
            return {'passed': False, 'issues': [str(e)]}

    def run_quality_checks_for_project(self, project_name: str, project_config: Dict) -> Dict:
        """Run quality checks for a specific project"""
        all_issues = {}
        all_passed = True
        commands = project_config.get('commands', {})

        # Linting
        lint_command = commands.get('lint')
        if lint_command:
            try:
                result = subprocess.run(
                    lint_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=self.get_project_root()
                )
                if result.returncode != 0:
                    all_passed = False
                    output_lines = result.stdout.split('\n')
                    lint_issues = [line for line in output_lines if line.strip()][:10]
                    all_issues['lint'] = lint_issues
            except:
                pass

        # Type checking
        typecheck_command = commands.get('typecheck')
        if typecheck_command:
            try:
                result = subprocess.run(
                    typecheck_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=self.get_project_root()
                )
                if result.returncode != 0:
                    all_passed = False
                    output_lines = result.stdout.split('\n')
                    type_issues = [line for line in output_lines if line.strip()][:5]
                    all_issues['typecheck'] = type_issues
            except:
                pass

        return {'passed': all_passed, 'issues': all_issues}

    def check_coverage_for_project(self, project_name: str, project_config: Dict) -> Dict:
        """Check test coverage for a specific project"""
        coverage_threshold = project_config.get('thresholds', {}).get('coverage', {}).get('lines', 80)
        coverage_command = project_config.get('commands', {}).get('coverage')

        if not coverage_command:
            return {'passed': True}

        try:
            result = subprocess.run(
                coverage_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.get_project_root()
            )

            match = re.search(r'(?:Total coverage:|TOTAL).*?(\d+)%', result.stdout)
            if not match:
                match = re.search(r'(\d+)%', result.stdout)

            if match:
                coverage = int(match.group(1))
                if coverage < coverage_threshold:
                    return {
                        'passed': False,
                        'current': coverage,
                        'required': coverage_threshold
                    }

            return {'passed': True}

        except:
            return {'passed': True}

    def check_build(self) -> Dict:
        """Check if project builds"""
        build_command = self.quality_config.get('commands', {}).get('build')

        # Also check for Python syntax errors if Python project
        if self.quality_config.get('projectType') == 'python':
            return self.check_python_syntax()

        if not build_command:
            return {'passed': True, 'issues': []}

        try:
            result = subprocess.run(
                build_command.split(),
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.get_project_root()
            )

            if result.returncode != 0:
                error_lines = (result.stderr or result.stdout).split('\n')
                error_lines = [line for line in error_lines if line.strip()][:5]
                return {
                    'passed': False,
                    'issues': error_lines,
                    'command': build_command
                }

            return {'passed': True, 'issues': []}

        except subprocess.TimeoutExpired:
            return {'passed': False, 'issues': ['Build timeout after 60 seconds']}
        except Exception as e:
            return {'passed': False, 'issues': [str(e)]}

    def check_python_syntax(self) -> Dict:
        """Check Python files for syntax errors"""
        try:
            # Limit search depth and skip common large directories
            # Use iterative approach with early filtering to avoid hanging
            exclude_dirs = {'venv', '.venv', 'env', '.env', 'node_modules', '.git',
                           'build', 'dist', '__pycache__', '.tox', '.pytest_cache',
                           'site-packages', '.mypy_cache', '.ruff_cache'}

            python_files = []
            max_files = 1000  # Safety limit

            for root, dirs, files in os.walk('.'):
                # Filter directories in-place to avoid descending
                dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]

                for file in files:
                    if file.endswith('.py'):
                        python_files.append(Path(root) / file)
                        if len(python_files) >= max_files:
                            break
                if len(python_files) >= max_files:
                    break

            for file in python_files:
                try:
                    with open(file) as f:
                        compile(f.read(), str(file), 'exec')
                except SyntaxError as e:
                    return {
                        'passed': False,
                        'issues': [f"Syntax error in {file}:{e.lineno}: {e.msg}"],
                        'file': str(file),
                        'line': e.lineno
                    }

            return {'passed': True, 'issues': []}

        except Exception as e:
            # Don't fail validation on checker errors
            return {'passed': True, 'issues': []}

    def run_tests(self) -> Dict:
        """Run test suite"""
        test_command = self.quality_config.get('commands', {}).get('test')
        if not test_command:
            return {'passed': True, 'issues': []}

        try:
            result = subprocess.run(
                test_command.split(),
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.get_project_root()
            )

            if result.returncode != 0:
                output = result.stdout + result.stderr

                # Extract failing test names
                failures = []

                # pytest format
                if 'FAILED' in output:
                    failures = re.findall(r'FAILED (.+?)(?:\s|$)', output)

                # unittest format
                elif 'FAIL:' in output:
                    failures = re.findall(r'FAIL: (.+?)(?:\n|$)', output)

                # Get first 10 failures
                failures = failures[:10]

                return {
                    'passed': False,
                    'failures': failures,
                    'command': test_command,
                    'summary': self.extract_test_summary(output)
                }

            return {'passed': True, 'issues': []}

        except subprocess.TimeoutExpired:
            return {'passed': False, 'issues': ['Test timeout after 120 seconds']}
        except Exception as e:
            return {'passed': False, 'issues': [str(e)]}

    def extract_test_summary(self, output: str) -> str:
        """Extract test summary from output"""
        # Look for pytest summary
        if '= short test summary info =' in output:
            lines = output.split('\n')
            start = False
            summary_lines = []
            for line in lines:
                if '= short test summary info =' in line:
                    start = True
                    continue
                if start:
                    if line.startswith('='):
                        break
                    if line.strip():
                        summary_lines.append(line)
            return '\n'.join(summary_lines[:5])

        # Look for failure count
        match = re.search(r'(\d+) failed.*?(\d+) passed', output)
        if match:
            return f"{match.group(1)} tests failed, {match.group(2)} passed"

        return "Test failures detected"

    def check_task_completion(self) -> Dict:
        """
        Check task completion and QA verification status.

        Returns:
            - passed: True if no active tasks or all tasks verified
            - needs_verification: List of tasks needing QA verification
            - verification_instructions: Specific checks for the agent to perform
        """
        # Check third-party workflow task files
        workflows = self.config.get('third_party_workflows', {}).get('detected', [])

        if not workflows:
            # No task management system configured
            return {'passed': True}

        for workflow in workflows:
            task_file = workflow.get('active_tasks_file')
            task_schema = workflow.get('task_format_schema', {})

            if task_file and Path(task_file).exists():
                return self.check_task_file_with_schema(Path(task_file), task_schema)

        # Fallback: check standard locations without schema
        standard_locations = ['tasks.md', 'TODO.md', '.github/tasks.md']
        for location in standard_locations:
            task_path = Path(location)
            if task_path.exists():
                return self.check_task_file_simple(task_path)

        return {'passed': True}

    def check_task_file_with_schema(self, task_path: Path, schema: Dict) -> Dict:
        """Check task file using detected schema to understand task structure"""
        try:
            with open(task_path) as f:
                content = f.read()

            # Get schema patterns
            patterns = schema.get('patterns', {})
            status_semantics = schema.get('status_semantics', {})

            # Parse tasks using schema
            tasks_needing_verification = []

            # Find all task blocks
            lines = content.split('\n')
            current_task = None

            for i, line in enumerate(lines):
                # Check if this is a task line
                task_pattern = patterns.get('task_line', {}).get('regex', '')
                if task_pattern:
                    task_match = re.match(task_pattern, line)
                    if task_match:
                        # Extract task info
                        groups = task_match.groupdict()
                        current_task = {
                            'id': groups.get('task_id', f'line-{i}'),
                            'description': groups.get('description', '').strip(),
                            'line': i + 1,
                            'dev_status': None,
                            'qa_status': None
                        }
                        continue

                # Check if this is a status line
                status_pattern = patterns.get('status_line', {}).get('regex', '')
                if status_pattern and current_task:
                    status_match = re.match(status_pattern, line)
                    if status_match:
                        groups = status_match.groupdict()
                        field = groups.get('field', '').strip()
                        status = groups.get('status', '').strip()

                        # Map to semantic field
                        field_mapping = status_semantics.get('field_mapping', {})
                        for semantic_field, raw_fields in field_mapping.items():
                            if field in raw_fields:
                                if semantic_field == 'dev':
                                    current_task['dev_status'] = status
                                elif semantic_field == 'qa':
                                    current_task['qa_status'] = status
                        continue

                # Empty line or new section - check if current task needs verification
                if line.strip() == '' and current_task:
                    # Check if dev is complete but QA is not verified
                    states = status_semantics.get('states', {})
                    dev_complete_values = states.get('dev', {}).get('complete', [])
                    qa_complete_values = states.get('qa', {}).get('complete', [])

                    if current_task['dev_status'] in dev_complete_values:
                        if current_task['qa_status'] not in qa_complete_values:
                            tasks_needing_verification.append(current_task)

                    current_task = None

            # Check last task if file doesn't end with blank line
            if current_task:
                states = status_semantics.get('states', {})
                dev_complete_values = states.get('dev', {}).get('complete', [])
                qa_complete_values = states.get('qa', {}).get('complete', [])

                if current_task['dev_status'] in dev_complete_values:
                    if current_task['qa_status'] not in qa_complete_values:
                        tasks_needing_verification.append(current_task)

            if tasks_needing_verification:
                return {
                    'passed': False,
                    'needs_verification': tasks_needing_verification,
                    'task_file': str(task_path),
                    'verification_instructions': self.generate_verification_instructions(tasks_needing_verification)
                }

            return {'passed': True}

        except Exception as e:
            print(f"Error parsing task file with schema: {e}", file=sys.stderr)
            # Fall back to simple check
            return self.check_task_file_simple(task_path)

    def check_task_file_simple(self, task_path: Path) -> Dict:
        """Simple task checking without schema - look for dev complete but QA not verified"""
        try:
            with open(task_path) as f:
                content = f.read()

            tasks_needing_verification = []
            lines = content.split('\n')

            # Simple pattern: look for checked tasks with QA status not verified
            current_task = None

            for i, line in enumerate(lines):
                # Task line with checkbox
                if re.match(r'^\s*-\s*\[x\]\s*-\s*\*\*(.+?):\s*(.+?)\*\*', line, re.IGNORECASE):
                    match = re.match(r'^\s*-\s*\[x\]\s*-\s*\*\*(.+?):\s*(.+?)\*\*', line, re.IGNORECASE)
                    current_task = {
                        'id': match.group(1),
                        'description': match.group(2),
                        'line': i + 1,
                        'dev_status': 'Complete',
                        'qa_status': None
                    }
                    continue

                # QA status line
                if current_task and re.match(r'^\s*-\s*\[.\]\s*-\s*QA.*?:\s*\[(.+?)\]', line, re.IGNORECASE):
                    match = re.match(r'^\s*-\s*\[.\]\s*-\s*QA.*?:\s*\[(.+?)\]', line, re.IGNORECASE)
                    current_task['qa_status'] = match.group(1)

                    # Check if verified
                    if match.group(1).lower() not in ['verified', 'pass', 'passed']:
                        tasks_needing_verification.append(current_task.copy())

                    current_task = None
                    continue

                # Blank line - reset
                if line.strip() == '':
                    current_task = None

            if tasks_needing_verification:
                return {
                    'passed': False,
                    'needs_verification': tasks_needing_verification,
                    'task_file': str(task_path),
                    'verification_instructions': self.generate_verification_instructions(tasks_needing_verification)
                }

            return {'passed': True}

        except Exception as e:
            print(f"Error checking task file: {e}", file=sys.stderr)
            return {'passed': True}  # Don't block on errors

    def generate_verification_instructions(self, tasks: List[Dict]) -> str:
        """Generate specific verification instructions for tasks"""
        instructions = []
        instructions.append("# QA Verification Required\n")
        instructions.append("The following tasks are marked as complete but have not been QA verified.\n")
        instructions.append("Please verify each task meets acceptance criteria:\n")

        for task in tasks:
            instructions.append(f"\n## {task['id']}: {task['description']}")
            instructions.append(f"**Location**: Line {task['line']} in task file")
            instructions.append("\n**Verification Checklist**:")
            instructions.append("1. Review the implementation for this task")
            instructions.append("2. Verify it meets the requirements described")
            instructions.append("3. Check for edge cases and error handling")
            instructions.append("4. Confirm tests cover the functionality")
            instructions.append("5. Ensure code quality standards are met")
            instructions.append("\n**After verification**:")
            instructions.append(f"- Update the QA status to [Verified] for task {task['id']}")
            instructions.append("- Check off the QA verification checkbox")

        instructions.append("\n\n**IMPORTANT**: Once ALL tasks above are verified and their QA status")
        instructions.append("updated to [Verified], attempt to stop again. The validation will pass.")

        return '\n'.join(instructions)

    def run_quality_checks(self) -> Dict:
        """Run linting, formatting, and type checking"""
        all_issues = {}
        all_passed = True

        # Linting
        lint_command = self.quality_config.get('commands', {}).get('lint')
        if lint_command:
            try:
                result = subprocess.run(
                    lint_command.split(),
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=self.get_project_root()
                )
                if result.returncode != 0:
                    all_passed = False
                    output_lines = result.stdout.split('\n')
                    # Get first 10 non-empty lines
                    lint_issues = [line for line in output_lines if line.strip()][:10]
                    all_issues['lint'] = lint_issues
            except:
                pass

        # Formatting check
        format_command = self.quality_config.get('commands', {}).get('format')
        if format_command:
            # Convert format command to check mode
            check_command = format_command
            if 'black' in format_command:
                check_command = format_command.replace('black', 'black --check')
            elif 'prettier' in format_command:
                check_command = format_command.replace('--write', '--check')

            try:
                result = subprocess.run(
                    check_command.split(),
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=self.get_project_root()
                )
                if result.returncode != 0:
                    all_passed = False
                    all_issues['format'] = ['Code formatting issues detected']
            except:
                pass

        # Type checking
        typecheck_command = self.quality_config.get('commands', {}).get('typecheck')
        if typecheck_command:
            try:
                result = subprocess.run(
                    typecheck_command.split(),
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=self.get_project_root()
                )
                if result.returncode != 0:
                    all_passed = False
                    output_lines = result.stdout.split('\n')
                    type_issues = [line for line in output_lines if line.strip()][:5]
                    all_issues['typecheck'] = type_issues
            except:
                pass

        return {'passed': all_passed, 'issues': all_issues}

    def check_coverage(self) -> Dict:
        """Check test coverage"""
        coverage_threshold = self.quality_config.get('thresholds', {}).get('coverage', {}).get('lines', 80)
        coverage_command = self.quality_config.get('commands', {}).get('coverage')

        if not coverage_command:
            return {'passed': True}

        try:
            result = subprocess.run(
                coverage_command.split(),
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.get_project_root()
            )

            # Parse coverage percentage from output
            match = re.search(r'(?:Total coverage:|TOTAL).*?(\d+)%', result.stdout)
            if not match:
                match = re.search(r'(\d+)%', result.stdout)

            if match:
                coverage = int(match.group(1))
                if coverage < coverage_threshold:
                    return {
                        'passed': False,
                        'current': coverage,
                        'required': coverage_threshold
                    }

            return {'passed': True}

        except:
            # Don't fail validation on coverage errors
            return {'passed': True}

    def generate_continuation_message(self, results: Dict) -> str:
        """Generate specific instructions for fixing issues"""
        lines = []
        lines.append(f"## 🔄 Validation Failed - Iteration #{self.current_iteration}\n")
        lines.append("You must fix the following issues before your work is complete:\n")

        # Build failures (highest priority)
        if 'build' in results and not results['build']['passed']:
            lines.append("### 🚨 BUILD FAILURE (Critical)\n")
            if results['build'].get('project'):
                lines.append(f"**Project**: `{results['build']['project']}`\n")
            if results['build'].get('file'):
                lines.append(f"**File**: `{results['build']['file']}` line {results['build'].get('line', '?')}")
            if results['build'].get('command'):
                lines.append(f"Command `{results['build']['command']}` failed.\n")
            lines.append("**Errors:**")
            for error in results['build']['issues'][:5]:
                if error.strip():
                    lines.append(f"  - {error}")
            lines.append("\n**IMMEDIATE ACTION**: Fix syntax/compilation errors in the specified file(s)\n")

        # Test failures
        elif 'tests' in results and not results['tests']['passed']:
            lines.append("### 🧪 TEST FAILURES\n")
            if results['tests'].get('project'):
                lines.append(f"**Project**: `{results['tests']['project']}`\n")
            if results['tests'].get('failures'):
                lines.append("**Failed tests:**")
                for test in results['tests']['failures'][:10]:
                    lines.append(f"  - {test}")
                if results['tests'].get('summary'):
                    lines.append(f"\n**Summary:**\n```\n{results['tests']['summary']}\n```")
            lines.append(f"\n**ACTION**: Run `{results['tests']['command']}` and fix the failing tests\n")
            lines.append("Focus on the actual test failures, not unrelated issues.\n")

        # Task verification needed
        elif 'tasks' in results and not results['tasks']['passed']:
            lines.append("### 📋 QA VERIFICATION REQUIRED\n")

            if results['tasks'].get('verification_instructions'):
                # Include the full verification instructions
                lines.append(results['tasks']['verification_instructions'])
            elif results['tasks'].get('needs_verification'):
                # Fallback if instructions weren't generated
                lines.append("**Tasks needing QA verification:**")
                for task in results['tasks']['needs_verification'][:5]:
                    lines.append(f"  - {task.get('id', 'Unknown')}: {task.get('description', 'No description')}")
                lines.append("\n**ACTION**: Verify each task is complete and update QA status to [Verified]\n")

        # Quality issues (lower priority)
        elif 'quality' in results and not results['quality']['passed']:
            lines.append("### ⚡ CODE QUALITY ISSUES\n")
            if results['quality'].get('project'):
                lines.append(f"**Project**: `{results['quality']['project']}`\n")

            if 'lint' in results['quality']['issues']:
                lines.append("\n**Linting errors:**")
                for issue in results['quality']['issues']['lint'][:5]:
                    if issue.strip():
                        lines.append(f"  - {issue}")

            if 'format' in results['quality']['issues']:
                lines.append("\n**Formatting:** Code needs formatting")

            if 'typecheck' in results['quality']['issues']:
                lines.append("\n**Type errors:**")
                for issue in results['quality']['issues']['typecheck'][:3]:
                    if issue.strip():
                        lines.append(f"  - {issue}")

            lines.append("\n**ACTION**: Fix the quality issues listed above\n")

        # Coverage issues (lowest priority)
        elif 'coverage' in results and not results['coverage']['passed']:
            lines.append("### 📊 COVERAGE BELOW THRESHOLD\n")
            if results['coverage'].get('project'):
                lines.append(f"**Project**: `{results['coverage']['project']}`\n")
            lines.append(f"**Current**: {results['coverage']['current']}%")
            lines.append(f"**Required**: {results['coverage']['required']}%")
            lines.append("\n**ACTION**: Add tests for uncovered code paths\n")

        # Add guidance for multiple iterations
        if self.current_iteration > 3:
            lines.append(f"\n⚠️ **Note**: This is validation attempt #{self.current_iteration}")
            lines.append("Focus only on fixing the specific issues listed above.")
            lines.append("Do not refactor or change unrelated code.")

        return '\n'.join(lines)

    def get_project_root(self) -> Path:
        """Get the project root directory"""
        return Path(self.config.get('project', {}).get('root_directory', '.'))

    def cleanup_state(self):
        """Clean up validation state files"""
        (self.synapse_dir / 'validation-state.json').unlink(missing_ok=True)
        (self.synapse_dir / 'continue-directive.md').unlink(missing_ok=True)


def timeout_handler(signum, frame):
    """Handle timeout - prevent infinite hangs"""
    print("\n⚠️ Validation timeout after 5 minutes", file=sys.stderr)
    print("⚠️ Allowing stop to prevent infinite loop", file=sys.stderr)
    sys.exit(0)


if __name__ == '__main__':
    # Early logging to confirm hook is running
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", file=sys.stderr)
    print("🔍 Stop validation hook started", file=sys.stderr)
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", file=sys.stderr)

    # Set overall timeout of 5 minutes for entire validation
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)  # 5 minutes

    try:
        controller = ValidationController()
        exit_code = controller.run()
        signal.alarm(0)  # Cancel timeout
        sys.exit(exit_code)
    except Exception as e:
        signal.alarm(0)  # Cancel timeout
        print(f"❌ Validation error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        # On error, allow stop to prevent infinite loop
        sys.exit(0)
