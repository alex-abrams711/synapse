# Research: Synapse Workflow UX Improvements

**Feature**: Template Integration and Slash Command System
**Date**: 2025-09-28
**Research Phase**: Phase 0 - Technical Decisions

## Research Areas

### 1. Jinja2 Templating for Markdown Integration

**Decision**: Use Jinja2 with custom delimiters and content preservation blocks

**Rationale**:
- Jinja2 provides mature templating with fine-grained control over delimiters
- Custom delimiters (e.g., `{# #}` instead of `{{ }}`) avoid conflicts with markdown syntax
- Block-level content preservation through `{% raw %}...{% endraw %}` or custom tags
- Conditional rendering allows graceful handling of missing user content

**Alternatives Considered**:
- **String replacement**: Too brittle, no conditional logic support
- **Template literals**: Python f-strings insufficient for complex template logic
- **Mustache/Handlebars**: Less Python ecosystem integration than Jinja2

**Implementation Approach**:
```python
# Custom Jinja2 environment with markdown-safe delimiters
template_env = Environment(
    block_start_string='{%',
    block_end_string='%}',
    variable_start_string='{{{',  # Triple to avoid markdown conflicts
    variable_end_string='}}}',
    comment_start_string='{#',
    comment_end_string='#}'
)
```

### 2. Claude Code Slash Command Implementation

**Decision**: Create command definition files in `.claude/commands/` with `/synapse:` prefix

**Rationale**:
- Claude Code reads command definitions from `.claude/commands/*.md` files
- Prefixed commands (`/synapse:plan`) eliminate conflict with user commands
- Each command file contains agent invocation logic and context setup
- Template-based command generation enables consistent command structure

**Alternatives Considered**:
- **Direct command registration**: No standard API available in Claude Code
- **Plugin system**: Claude Code doesn't support runtime plugin registration
- **Command aliasing**: More complex, doesn't solve namespace conflicts

**Command Structure**:
```markdown
# /synapse:plan - Planning Command

## Description
Invoke DISPATCHER agent for task analysis and breakdown.

## Implementation
Load current workflow context and invoke DISPATCHER agent with user request.
```

### 3. File Content Preservation Strategies

**Decision**: Structured template with designated user content slots

**Rationale**:
- Creates clear boundaries between Synapse functionality and user content
- Enables version control of template changes while preserving user modifications
- Supports migration and upgrades through slot-based content extraction
- Maintains readability and user control over their portions

**Alternatives Considered**:
- **Append-only**: Poor organization, content becomes unwieldy
- **Inline integration**: Too complex to maintain boundaries
- **Separate files**: Fragmentations user experience, multiple file management

**Template Structure**:
```markdown
# Project Context

{{{ user_context_slot }}}

# Synapse Agent Workflow System

[Synapse-managed content]

# Custom Instructions

{{{ user_instructions_slot }}}

# Synapse Commands

[Generated command definitions]
```

### 4. Command Conflict Detection Patterns

**Decision**: Parse existing command files and maintain conflict registry

**Rationale**:
- Proactive conflict detection prevents installation failures
- Registry-based tracking enables conflict resolution recommendations
- File parsing approach works with existing Claude Code command structure
- Warning-based approach (vs. blocking) gives users control

**Alternatives Considered**:
- **Runtime detection**: Too late, commands already installed
- **Override approach**: Destroys user customizations
- **Interactive resolution**: Complicates automation and scripting

**Detection Strategy**:
```python
def detect_conflicts(command_dir: Path) -> List[ConflictInfo]:
    existing_commands = parse_command_files(command_dir)
    synapse_commands = get_synapse_commands()
    return [
        ConflictInfo(cmd, existing, synapse)
        for cmd in synapse_commands
        if cmd.name in existing_commands
    ]
```

## Integration Architecture

### Template Processing Pipeline
1. **Discovery**: Detect existing CLAUDE.md and extract user content
2. **Parsing**: Identify user content sections vs. Synapse-managed sections
3. **Slot Population**: Extract user content into template variables
4. **Rendering**: Generate new CLAUDE.md from template with user content preserved
5. **Validation**: Verify template structure and content integrity

### Command Registration Pipeline
1. **Conflict Detection**: Scan existing commands for naming conflicts
2. **Command Generation**: Create command files from templates with context injection
3. **Installation**: Write command files to `.claude/commands/` directory
4. **Registry Update**: Track installed commands for future conflict detection
5. **Validation**: Verify command files are properly formatted and functional

### Error Handling Strategy
- **Template Parsing Errors**: Preserve original file, log warnings, continue with defaults
- **Command Conflicts**: Warn user, use prefixed names, document conflicts
- **File Permission Issues**: Clear error messages with resolution guidance
- **Malformed User Content**: Best-effort preservation with validation warnings

## Performance Considerations

### Template Processing
- **Target**: <500ms for CLAUDE.md template integration
- **Optimization**: Cache parsed templates, lazy loading of user content
- **Memory**: Streaming approach for large user content sections

### Command Installation
- **Target**: <1s for complete command installation
- **Optimization**: Parallel command file generation, batch file operations
- **Validation**: Background validation with immediate user feedback

## Security Considerations

### Template Injection Prevention
- **User Content Sanitization**: Escape template syntax in user content
- **Template Validation**: Validate template structure before rendering
- **Sandboxed Execution**: Jinja2 environment with restricted globals

### File System Safety
- **Path Validation**: Prevent directory traversal in template paths
- **Permission Checks**: Verify write permissions before modification
- **Backup Strategy**: Create backup copies before modification

## Summary

The research establishes a robust foundation for template-based CLAUDE.md integration using Jinja2 with custom delimiters, conflict-aware slash command registration with `/synapse:` prefixing, and content preservation through structured template slots. This approach balances user control with system functionality while maintaining compatibility with existing Claude Code patterns.

**Ready for Phase 1**: Design and contract generation based on these architectural decisions.