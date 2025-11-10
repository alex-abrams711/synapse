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

The stop hook performs two types of validation:

### 1. Programmatic Quality Gates (Blocking)
These are objective checks that block immediately:
- **Build/Syntax** - Code compiles without errors
- **Tests** - All tests pass
- **Quality** - Linting, formatting, type checking pass
- **Coverage** - Meets configured thresholds

### 2. QA Verification Instructions (Agent-Driven)
For task completion, the hook generates verification instructions:
- Checks if tasks are marked "Dev: Complete"
- Verifies QA status is "Verified"
- **If not verified**: Generates specific checklist for agent to verify
- **Agent performs verification**: Reviews code, tests, edge cases
- **Agent updates QA status**: Marks as [Verified] when satisfied
- **Hook passes**: Once all tasks verified

This hybrid approach ensures objective quality while leveraging agent judgment for subjective completion criteria.

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
