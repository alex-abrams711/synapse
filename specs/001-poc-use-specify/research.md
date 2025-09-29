# Research Findings: Synapse Agent Workflow System POC

## Global CLI Package Architecture Research

### Decision: Click Framework for CLI Implementation
**Rationale**: Click provides robust command structure, sub-commands, and parameter validation. Industry standard for Python CLI tools.
**Alternatives considered**:
- argparse: Standard library but verbose for complex CLIs
- Typer: Type-hint based but adds dependency complexity
- Fire: Less control over interface design

### Decision: Template-Based Project Scaffolding
**Rationale**: Copying template files to user projects avoids runtime dependencies while providing agent context files that Claude Code can read.
**Alternatives considered**:
- Runtime library imports: Rejected per user clarification
- Git repository templates: More complex, requires git dependency
- Package data files: Limited flexibility for customization

## Agent Template Research

### Decision: Markdown Agent Templates
**Rationale**: Claude Code reads .md files natively. Agent templates can contain prompts, rules, and context in human-readable format.
**Alternatives considered**:
- YAML configurations: Less readable for agent instructions
- JSON templates: Poor for multi-line agent prompts
- Python files: Would require runtime imports (rejected)

### Decision: Agent Context via CLAUDE.md Files
**Rationale**: Claude Code recognizes CLAUDE.md as context file. Templates can scaffold project-specific agent behavior.
**Alternatives considered**:
- Per-agent files: Too granular for POC
- Single config file: Less modular than agent-specific context
- Environment variables: Not persistent across sessions

## Workflow State Management

### Decision: JSON Task Log Files
**Rationale**: Persistent, human-readable, diffable, version-controllable. No external dependencies.
**Alternatives considered**:
- SQLite database: Overkill for POC scope
- YAML files: Less structured for programmatic access
- CSV files: Poor for nested data structures

### Decision: File-Based Workflow State
**Rationale**: Aligns with template scaffolding approach. Each project gets its own workflow state directory.
**Alternatives considered**:
- Global state directory: Conflicts between projects
- In-memory state: Not persistent across Claude sessions
- Remote state storage: Adds complexity and dependencies

## CLI Command Structure Research

### Decision: Git-Style Sub-Commands
**Rationale**: Familiar pattern (git init, git status). Extensible for future commands.
**Implementation**:
- `synapse init` - Initialize project with agent templates
- `synapse status` - Show workflow state and agent activity
- Future: `synapse validate`, `synapse reset`

**Alternatives considered**:
- Single command with flags: Less intuitive
- Separate executable per command: Package complexity
- Interactive prompts: Less scriptable

## Project Initialization Workflow

### Decision: Directory Detection and Smart Scaffolding
**Rationale**: Detect existing project structure and adapt template placement accordingly.
**Implementation Strategy**:
1. Detect existing directories (src/, tests/, etc.)
2. Create `.synapse/` directory for workflow state
3. Place agent templates in appropriate locations
4. Generate project-specific CLAUDE.md

**Alternatives considered**:
- Fixed template structure: Less flexible
- User-prompted structure: More complex UX
- Existing file overwriting: Destructive approach

## Agent Communication Protocol

### Decision: JSON Schema for Agent Messages
**Rationale**: Structured validation while maintaining human readability. Python standard library support.
**Schema Elements**:
- Task definitions with acceptance criteria
- Agent status updates and results
- Verification reports from AUDITOR
- Orchestration commands from DISPATCHER

**Alternatives considered**:
- Free-form text: No validation guarantees
- Binary protocols: Not human-readable
- XML: Verbose and dated

## Testing Strategy Research

### Decision: Template Validation Testing
**Rationale**: Ensure scaffolded templates are valid and functional before user deployment.
**Test Categories**:
- Template syntax validation
- Agent prompt completeness
- Workflow configuration validity
- CLI command integration

**Alternatives considered**:
- End-to-end Claude testing: Not feasible in CI
- Manual testing only: Not sustainable
- Mock-only testing: Insufficient coverage

## Distribution and Installation

### Decision: PyPI Distribution with Entry Point
**Rationale**: Standard Python package distribution. Global installation provides `synapse` command.
**Configuration**:
```toml
[project.scripts]
synapse = "synapse.cli.main:cli"
```

**Alternatives considered**:
- Conda distribution: Smaller audience
- Direct download: No dependency management
- GitHub releases only: Manual installation

## Version Management

### Decision: Semantic Versioning with Template Compatibility
**Rationale**: Clear upgrade paths and template migration strategies.
**Implementation**:
- Template version markers in scaffolded files
- Migration commands for template updates
- Backward compatibility checks

**Alternatives considered**:
- Date-based versioning: Less semantic
- Git commit versioning: Too granular
- No versioning: Unmaintainable

## Resolved Clarifications

All technical clarifications have been resolved based on user input and spec clarifications:
- Installation approach: Global CLI package that scaffolds templates
- Communication: JSON task logs in project directories
- Failure handling: Immediate user escalation via Claude interface
- Agent mutability: Immutable templates, modifiable per-project
- Task limits: No artificial constraints on subtask breakdown

No remaining NEEDS CLARIFICATION items.