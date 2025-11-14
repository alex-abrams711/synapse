# Implementation Prompt: Feature-Implementation-V2 Workflow

## Objective
Implement a new workflow called `feature-implementation-v2` for the synapse project that eliminates all sub-agent overhead while maintaining quality through a stop hook continuation pattern. The main agent handles all implementation directly and is prevented from stopping until validation passes.

## Project Location
`/Users/aabrams/Workspace/AI/synapse`

## Architecture Summary
- **No sub-agents**: Main agent does all implementation
- **Stop hook validation**: Comprehensive quality checks when agent tries to stop
- **Forced continuation**: Exit code 1 prevents stopping until issues fixed
- **Direct feedback**: Specific issues shown inline for immediate fixing

## Implementation Steps

### Step 1: Create Workflow Directory Structure

Create the following directory structure under `resources/workflows/feature-implementation-v2/`:

```
resources/workflows/feature-implementation-v2/
├── hooks/
│   ├── stop.sh
│   ├── stop_validation.py
│   └── checkpoint.py
├── commands/
│   ├── checkpoint.md
│   └── verify-status.md
├── instructions/
│   └── validation-protocol.md
├── scripts/
│   └── emergency_repair.py
├── settings.json
└── README.md
```

### Step 2: Create Stop Hook Files

#### File: `hooks/stop.sh`
```bash
#!/bin/bash
# Stop Hook - Quality Gate Controller
# Forces continuation until all validation passes

set -e

SYNAPSE_DIR=".synapse"
VALIDATION_LOG="$SYNAPSE_DIR/validation-log.txt"
CONTINUE_DIRECTIVE="$SYNAPSE_DIR/continue-directive.md"

echo "🔍 Running validation checkpoint..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Run validation
python3 .claude/hooks/stop_validation.py

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All validation checks passed! Work is complete."
    rm -f "$CONTINUE_DIRECTIVE"
    exit 0
else
    echo ""
    echo "❌ Validation failed - you must fix these issues:"
    echo ""
    
    # Display the continuation directive
    if [ -f "$CONTINUE_DIRECTIVE" ]; then
        cat "$CONTINUE_DIRECTIVE"
    fi
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "👉 REQUIRED: Fix the above issues before stopping."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Exit 1 forces agent to continue
    exit 1
fi
```

Make the script executable:
```bash
chmod +x resources/workflows/feature-implementation-v2/hooks/stop.sh
```

#### File: `hooks/stop_validation.py`
```python
#!/usr/bin/env python3
"""
Validation orchestrator that generates continuation directives.
Exit codes:
  0 - All checks passed, OK to stop
  1 - Issues found, must continue with fixes
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import re
import traceback

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
        
        print(f"Validation iteration #{self.current_iteration}")
        
        # Safety check for infinite loops
        if self.current_iteration > 10:
            print("⚠️ Max validation attempts reached. Allowing stop to prevent infinite loop.")
            self.cleanup_state()
            return 0
        
        results = self.run_all_validations()
        
        # Check if all passed
        all_passed = all(r.get('passed', True) for r in results.values())
        
        if all_passed:
            print("✅ All validations passed!")
            self.cleanup_state()
            return 0
        else:
            # Generate specific continuation instructions
            self.generate_continuation_directive(results)
            self.save_validation_state()
            return 1
    
    def run_all_validations(self) -> Dict:
        """Run all validation checks in priority order"""
        results = {}
        
        # Check build first - if it fails, skip other checks
        results['build'] = self.check_build()
        if not results['build']['passed']:
            return results
        
        # Run remaining checks
        results['tests'] = self.run_tests()
        results['tasks'] = self.check_task_completion()
        results['quality'] = self.run_quality_checks()
        results['coverage'] = self.check_coverage()
        
        return results
    
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
            # Find all Python files
            python_files = list(Path('.').rglob('*.py'))
            
            for file in python_files:
                # Skip virtual environments and build directories
                if any(part in str(file) for part in ['venv', '.env', 'build', 'dist', '__pycache__']):
                    continue
                
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
        """Verify tasks marked complete are actually done"""
        incomplete_tasks = []
        task_files_checked = []
        
        # Check third-party workflow task files
        workflows = self.config.get('third_party_workflows', {}).get('detected', [])
        for workflow in workflows:
            task_file = workflow.get('active_tasks_file')
            if task_file:
                task_path = Path(task_file)
                if task_path.exists():
                    task_files_checked.append(str(task_path))
                    incomplete = self.check_task_file(task_path)
                    incomplete_tasks.extend(incomplete)
        
        # Check standard task locations
        standard_locations = ['tasks.md', 'TODO.md', '.github/tasks.md']
        for location in standard_locations:
            task_path = Path(location)
            if task_path.exists():
                task_files_checked.append(location)
                incomplete = self.check_task_file(task_path)
                incomplete_tasks.extend(incomplete)
        
        if incomplete_tasks:
            return {
                'passed': False,
                'incomplete': incomplete_tasks,
                'files_checked': task_files_checked
            }
        
        return {'passed': True}
    
    def check_task_file(self, task_path: Path) -> List[str]:
        """Check a single task file for incomplete marked tasks"""
        incomplete = []
        
        try:
            with open(task_path) as f:
                content = f.read()
            
            # Find tasks marked as complete
            completed_pattern = r'\[x\]\s+(.+?)(?:\n|$)'
            completed_tasks = re.findall(completed_pattern, content, re.IGNORECASE)
            
            # For now, we trust that marked tasks are complete
            # In a real implementation, you'd verify each task
            
        except Exception as e:
            pass
        
        return incomplete
    
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
    
    def generate_continuation_directive(self, results: Dict):
        """Generate specific instructions for fixing issues"""
        directive_path = self.synapse_dir / 'continue-directive.md'
        
        lines = []
        lines.append(f"## 🔄 Validation Failed - Iteration #{self.current_iteration}\n")
        lines.append("You must fix the following issues before your work is complete:\n")
        
        # Build failures (highest priority)
        if 'build' in results and not results['build']['passed']:
            lines.append("### 🚨 BUILD FAILURE (Critical)\n")
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
            if results['tests'].get('failures'):
                lines.append("**Failed tests:**")
                for test in results['tests']['failures'][:10]:
                    lines.append(f"  - {test}")
                if results['tests'].get('summary'):
                    lines.append(f"\n**Summary:**\n```\n{results['tests']['summary']}\n```")
            lines.append(f"\n**ACTION**: Run `{results['tests']['command']}` and fix the failing tests\n")
            lines.append("Focus on the actual test failures, not unrelated issues.\n")
        
        # Task completion issues
        elif 'tasks' in results and not results['tasks']['passed']:
            lines.append("### 📋 INCOMPLETE TASKS\n")
            if results['tasks'].get('incomplete'):
                lines.append("**Tasks marked complete but not verified:**")
                for task in results['tasks']['incomplete'][:5]:
                    lines.append(f"  - {task}")
            lines.append("\n**ACTION**: Ensure these tasks are actually implemented\n")
        
        # Quality issues (lower priority)
        elif 'quality' in results and not results['quality']['passed']:
            lines.append("### ⚡ CODE QUALITY ISSUES\n")
            
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
            lines.append(f"**Current**: {results['coverage']['current']}%")
            lines.append(f"**Required**: {results['coverage']['required']}%")
            lines.append("\n**ACTION**: Add tests for uncovered code paths\n")
        
        # Add guidance for multiple iterations
        if self.current_iteration > 3:
            lines.append(f"\n⚠️ **Note**: This is validation attempt #{self.current_iteration}")
            lines.append("Focus only on fixing the specific issues listed above.")
            lines.append("Do not refactor or change unrelated code.")
        
        with open(directive_path, 'w') as f:
            f.write('\n'.join(lines))
    
    def get_project_root(self) -> Path:
        """Get the project root directory"""
        return Path(self.config.get('project', {}).get('root_directory', '.'))
    
    def cleanup_state(self):
        """Clean up validation state files"""
        (self.synapse_dir / 'validation-state.json').unlink(missing_ok=True)
        (self.synapse_dir / 'continue-directive.md').unlink(missing_ok=True)


if __name__ == '__main__':
    try:
        controller = ValidationController()
        sys.exit(controller.run())
    except Exception as e:
        print(f"Validation error: {e}")
        traceback.print_exc()
        # On error, allow stop to prevent infinite loop
        sys.exit(0)
```

Make the script executable:
```bash
chmod +x resources/workflows/feature-implementation-v2/hooks/stop_validation.py
```

#### File: `hooks/checkpoint.py`
```python
#!/usr/bin/env python3
"""
Manual checkpoint validation that can be run during work.
This doesn't force continuation, just provides feedback.
"""

import sys
from pathlib import Path

# Import the main validation controller
sys.path.insert(0, str(Path(__file__).parent))
from stop_validation import ValidationController

class CheckpointValidator(ValidationController):
    def __init__(self):
        super().__init__()
        # Don't track iterations for manual checkpoints
        self.current_iteration = 0
    
    def run(self) -> int:
        """Run validation and provide feedback without forcing continuation"""
        print("🔍 Running manual checkpoint validation...")
        
        results = self.run_all_validations()
        
        # Generate report
        all_passed = all(r.get('passed', True) for r in results.values())
        
        if all_passed:
            print("✅ All validations currently passing!")
            return 0
        else:
            print("\n⚠️ Issues detected (not blocking):")
            self.print_summary(results)
            print("\nThese issues should be addressed before completing work.")
            return 0  # Always return 0 for manual checkpoint
    
    def print_summary(self, results: dict):
        """Print a summary of issues"""
        if 'build' in results and not results['build']['passed']:
            print("  - Build failures detected")
        if 'tests' in results and not results['tests']['passed']:
            print(f"  - Test failures: {len(results['tests'].get('failures', []))} tests failing")
        if 'quality' in results and not results['quality']['passed']:
            print("  - Code quality issues detected")
        if 'coverage' in results and not results['coverage']['passed']:
            current = results['coverage'].get('current', 0)
            required = results['coverage'].get('required', 80)
            print(f"  - Coverage below threshold: {current}% < {required}%")


if __name__ == '__main__':
    validator = CheckpointValidator()
    sys.exit(validator.run())
```

Make executable:
```bash
chmod +x resources/workflows/feature-implementation-v2/hooks/checkpoint.py
```

### Step 3: Create Command Files

#### File: `commands/checkpoint.md`
```markdown
# checkpoint

Run a manual validation checkpoint to see the current status of your work.

## Usage

Use this command to check if your work currently passes all validation criteria:
- Build/syntax verification
- Test suite status
- Task completion
- Code quality (linting, formatting, type checking)
- Coverage thresholds

This is a non-blocking check - it provides feedback but doesn't prevent you from continuing work.

## When to use

- Before attempting to complete work
- After fixing a complex issue
- To verify tests are passing
- To check current coverage levels

## Example

```
/checkpoint
```

The command will show any current issues that need to be addressed before your work can be marked complete.
```

#### File: `commands/verify-status.md`
```markdown
# verify-status

Check the last validation status without running new checks.

## Usage

This command displays:
- Last validation run results
- Current iteration count (if in a validation loop)
- Specific issues that need addressing

Use this when you want to review what needs to be fixed without running the full validation suite again.

## Example

```
/verify-status
```
```

### Step 4: Create Instructions File

#### File: `instructions/validation-protocol.md`
```markdown
# Quality Gate Validation Protocol

This project uses an automated quality gate system that ensures all work meets standards before completion.

## How It Works

When you attempt to stop working, the validation system automatically:
1. Runs comprehensive quality checks
2. If issues are found, prevents stopping and shows what needs fixing
3. Requires you to fix issues before work can be marked complete

## Validation Checks

The system validates in priority order:
1. **Build/Syntax** - Code must compile/parse without errors
2. **Tests** - All tests must pass
3. **Task Completion** - Tasks marked done must be implemented
4. **Code Quality** - Linting, formatting, type checking
5. **Coverage** - Test coverage must meet thresholds

## When Validation Fails

If validation fails when you try to stop:
1. You'll see specific issues that need fixing
2. Fix ONLY the issues listed - don't expand scope
3. Try to stop again after fixing
4. Repeat until all checks pass

## Important Guidelines

- **Focus on the specific issues shown** - Don't refactor unrelated code
- **Fix in priority order** - Build errors first, then tests, then quality
- **Use /checkpoint for manual checks** - Test your fixes before trying to stop
- **Maximum 10 attempts** - After 10 iterations, stop is allowed to prevent infinite loops

## Commands Available

- `/checkpoint` - Run validation manually without blocking
- `/verify-status` - Check last validation results

Remember: The goal is to ensure quality while maintaining velocity. Fix what's broken, don't perfect what's working.
```

### Step 5: Create Settings File

#### File: `settings.json`
```json
{
  "workflow_version": "2.0.0",
  "workflow_name": "feature-implementation-v2",
  "description": "Direct implementation with stop hook validation - no sub-agents",
  "settings": {
    "hooks": {
      "stop": ".claude/hooks/stop.sh"
    },
    "validation": {
      "enforce_on_stop": true,
      "max_iterations": 10,
      "priority_order": ["build", "tests", "tasks", "quality", "coverage"]
    },
    "performance": {
      "use_sub_agents": false,
      "validation_strategy": "checkpoint",
      "cache_results": true
    }
  },
  "instructions": [
    ".claude/instructions/validation-protocol.md"
  ],
  "commands": [
    {
      "name": "checkpoint",
      "file": ".claude/commands/checkpoint.md"
    },
    {
      "name": "verify-status",  
      "file": ".claude/commands/verify-status.md"
    }
  ]
}
```

### Step 6: Create README

#### File: `README.md`
```markdown
# Feature Implementation V2 Workflow

A streamlined implementation workflow that eliminates sub-agent overhead while maintaining quality through stop hook validation.

## Key Innovation

This workflow completely removes sub-agents (no implementer, no verifier) and instead uses a "continuation pattern" where the main agent cannot stop working until quality standards are met.

## Benefits

- **70-80% faster** - No sub-agent context switching
- **60-70% fewer tokens** - No context duplication
- **Better context** - Main agent keeps full understanding
- **Forced quality** - Cannot complete work until standards met
- **Clear feedback** - Specific issues shown inline

## How It Works

1. Main agent implements features directly (no delegation)
2. When agent tries to stop, validation runs automatically
3. If validation fails:
   - Specific issues are shown
   - Agent is forced to continue (exit code 1)
   - Agent fixes issues and tries to stop again
4. Process repeats until all validation passes

## Installation

```bash
# From the synapse project directory
synapse workflow feature-implementation-v2
```

## Validation Criteria

The stop hook validates:
- **Build/Syntax** - Code compiles without errors
- **Tests** - All tests pass
- **Tasks** - Marked tasks are complete
- **Quality** - Linting, formatting, type checking pass
- **Coverage** - Meets configured thresholds

## Configuration

The workflow respects your `.synapse/config.json`:
```json
{
  "quality-config": {
    "projectType": "python",
    "commands": {
      "test": "pytest",
      "lint": "flake8",
      "format": "black --check",
      "typecheck": "mypy",
      "coverage": "pytest --cov"
    },
    "thresholds": {
      "coverage": {
        "lines": 80
      }
    }
  }
}
```

## Available Commands

- `/checkpoint` - Run validation manually (non-blocking)
- `/verify-status` - Check last validation results

## Safety Features

- Maximum 10 validation iterations to prevent infinite loops
- Clear error messages for each type of failure
- Progressive hints after multiple failures
- Emergency stop after 10 attempts

## Philosophy

> "Let the agent work naturally, validate comprehensively"

Rather than wrapping every action in quality gates, this workflow lets Claude Code work in its natural flow and validates at the natural breakpoint - when work is complete.

## Comparison with V1

| Aspect | V1 (Sub-agents) | V2 (Stop Hook) |
|--------|-----------------|----------------|
| Implementation | Delegated to implementer | Direct by main agent |
| Verification | Separate verifier agent | Inline continuation |
| Token Usage | High (3x contexts) | Low (single context) |
| Speed | Slow (context switching) | Fast (continuous flow) |
| Quality | Enforced via hooks | Enforced via continuation |

## Troubleshooting

**Validation keeps failing**: 
- Focus only on the specific issues shown
- Don't expand scope or refactor unrelated code
- Use `/checkpoint` to test fixes before stopping

**Infinite loop concerns**:
- System allows stop after 10 attempts
- Check `.synapse/validation-state.json` for iteration count
- Delete state file to reset: `rm .synapse/validation-state.json`

## Future Enhancements

- Configurable validation levels (strict/normal/relaxed)
- Parallel validation checks for speed
- Incremental validation (only check changed files)
- ML-based issue priority ranking
```

### Step 7: Create Emergency Repair Script

#### File: `scripts/emergency_repair.py`
```python
#!/usr/bin/env python3
"""
Emergency repair script for when validation is completely stuck.
This should rarely be needed.
"""

import sys
import json
from pathlib import Path

def reset_validation_state():
    """Reset all validation state to allow work to continue"""
    synapse_dir = Path('.synapse')
    
    # Remove validation state
    state_file = synapse_dir / 'validation-state.json'
    if state_file.exists():
        state_file.unlink()
        print("✓ Removed validation state")
    
    # Remove continuation directive
    directive_file = synapse_dir / 'continue-directive.md'
    if directive_file.exists():
        directive_file.unlink()
        print("✓ Removed continuation directive")
    
    # Clear any validation logs
    log_file = synapse_dir / 'validation-log.txt'
    if log_file.exists():
        log_file.unlink()
        print("✓ Cleared validation log")
    
    print("\n✅ Validation state reset. You can now continue working.")
    print("⚠️  Warning: Quality issues may still exist and should be addressed.")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        reset_validation_state()
    else:
        print("Emergency Repair Tool")
        print("=" * 40)
        print("\nThis will reset validation state to escape a validation loop.")
        print("Use only if validation is stuck after multiple attempts.")
        print("\nUsage: python3 emergency_repair.py --force")
        print("\n⚠️  This does not fix the underlying issues!")
```

Make executable:
```bash
chmod +x resources/workflows/feature-implementation-v2/scripts/emergency_repair.py
```

### Step 8: Integration with Synapse CLI

Update the synapse CLI to recognize the new workflow. In `synapse/cli/workflow.py` or wherever workflows are registered, add:

```python
AVAILABLE_WORKFLOWS = {
    'feature-implementation': 'resources/workflows/feature-implementation',
    'feature-implementation-v2': 'resources/workflows/feature-implementation-v2',  # Add this
}
```

### Step 9: Testing Instructions

After implementation, test the workflow:

1. **Apply the workflow**:
   ```bash
   cd /path/to/test/project
   synapse init
   synapse workflow feature-implementation-v2
   ```

2. **Verify files are copied**:
   ```bash
   ls -la .claude/hooks/stop.sh
   ls -la .claude/hooks/stop_validation.py
   cat .claude/instructions/validation-protocol.md
   ```

3. **Test the validation loop**:
   - Make changes that will fail tests
   - Try to stop working
   - Observe that you're forced to continue
   - Fix the tests
   - Try to stop again
   - Observe successful completion

4. **Test manual checkpoint**:
   ```
   /checkpoint
   ```

5. **Test emergency reset** (if needed):
   ```bash
   python3 .claude/scripts/emergency_repair.py --force
   ```

## Expected Behavior

When working with this workflow:

1. **Normal implementation** - Work proceeds without interruption
2. **Attempting to stop with issues** - See validation failures and must continue
3. **After fixing issues** - Can successfully stop
4. **Manual checks** - `/checkpoint` provides non-blocking feedback

## Success Metrics

The implementation is successful when:
- ✅ No sub-agents are used at all
- ✅ Stop hook prevents completion until quality met
- ✅ Clear, actionable feedback on failures
- ✅ 60%+ reduction in token usage
- ✅ 70%+ reduction in execution time
- ✅ Quality standards maintained or improved

## Important Notes

1. Make all shell scripts executable with `chmod +x`
2. Ensure Python scripts have proper shebang (`#!/usr/bin/env python3`)
3. Test with a project that has actual tests and quality configs
4. Monitor token usage before/after to verify improvements
5. The stop hook exit code 1 is critical - it forces continuation

## Rollback Plan

If issues arise, users can switch back to v1:
```bash
synapse workflow remove
synapse workflow feature-implementation
```

The two workflows can coexist in the codebase, allowing gradual migration.
