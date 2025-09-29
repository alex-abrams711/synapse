# /synapse:implement - Code Implementation and Development

## Description

Invoke the DEV agent for code implementation, development, and technical execution. This command handles the practical implementation of planned tasks with focus on code quality, best practices, and integration with existing systems.

## Agent Target

**DEV** - Primary code implementation and development

## Implementation

When `/synapse:implement` is invoked:

1. **Task Context Loading**: Retrieve task specifications and acceptance criteria
2. **Code Analysis**: Understand existing codebase and integration points
3. **Implementation Strategy**: Design implementation approach and architecture
4. **Code Development**: Write production-quality code following best practices
5. **Testing Integration**: Implement appropriate tests and validation
6. **Documentation**: Create necessary technical documentation

### Example Usage

```
/synapse:implement Create user authentication middleware for Express.js app
```

### Expected Workflow

1. DEV agent analyzes the middleware requirement
2. Reviews existing Express.js setup and architecture
3. Designs middleware implementation strategy
4. Implements authentication middleware with proper error handling
5. Creates unit and integration tests
6. Updates technical documentation
7. Coordinates with AUDITOR for quality verification

### Implementation Principles

- **Code Quality**: Follow established coding standards and best practices
- **Testing**: Implement comprehensive test coverage (>80%)
- **Documentation**: Maintain clear, up-to-date technical documentation
- **Integration**: Ensure seamless integration with existing systems
- **Security**: Follow security best practices and vulnerability prevention
- **Performance**: Optimize for efficiency and scalability

### Output Deliverables

- **Source Code**: Production-ready implementation
- **Test Suite**: Comprehensive automated tests
- **Documentation**: Technical documentation and API specs
- **Integration Notes**: Instructions for deployment and integration
- **Quality Report**: Code quality metrics and coverage reports

## Context Integration

- Reads from `.synapse/config.yaml` for coding standards and preferences
- Updates `.synapse/task_log.json` with implementation progress
- Coordinates with `.claude/agents/dev.md` for specialized capabilities
- Integrates with existing project structure and conventions

## Quality Standards

All implementations must meet:
- **✅ Linting**: Zero linting errors with project standards
- **✅ Type Safety**: Proper type annotations and type checking
- **✅ Test Coverage**: Minimum 80% test coverage
- **✅ Documentation**: All public APIs documented
- **✅ Security**: Security best practices followed
- **✅ Performance**: Efficient algorithms and resource usage

## Handoff Protocol

Upon completion, DEV agent:
1. Commits implementation with clear commit messages
2. Creates summary of changes and new functionality
3. Triggers AUDITOR review process
4. Updates task status and progress tracking
5. Provides deployment and integration guidance