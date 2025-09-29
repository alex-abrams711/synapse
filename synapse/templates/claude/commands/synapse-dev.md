# /synapse:dev - Direct Developer Agent Communication

## Description

Direct communication channel with the DEV agent for development-specific questions, technical consultations, and implementation guidance. This command provides immediate access to development expertise without formal task planning.

## Agent Target

**DEV** - Primary code implementation and development

## Implementation

When `/synapse:dev` is invoked:

1. **Direct Connection**: Establish direct communication with DEV agent
2. **Context Awareness**: Load current development context and project state
3. **Technical Consultation**: Provide expert development advice and guidance
4. **Code Analysis**: Analyze existing code for improvement opportunities
5. **Problem Solving**: Help debug issues and resolve technical challenges
6. **Best Practices**: Share development best practices and patterns

### Example Usage

```
/synapse:dev How should I structure the database schema for user roles and permissions?
```

```
/synapse:dev Can you help debug this React component performance issue?
```

```
/synapse:dev What's the best approach for implementing real-time notifications?
```

### Consultation Types

#### Architecture & Design
- **System Architecture**: High-level system design decisions
- **Database Design**: Schema design, relationships, and optimization
- **API Design**: RESTful API design and best practices
- **Component Architecture**: Frontend component structure and patterns

#### Implementation Guidance
- **Code Patterns**: Best practices for specific programming languages
- **Framework Usage**: Optimal use of frameworks and libraries
- **Performance Optimization**: Code optimization and efficiency improvements
- **Security Implementation**: Secure coding practices and vulnerability prevention

#### Problem Solving
- **Debugging Help**: Assistance with identifying and fixing bugs
- **Performance Issues**: Diagnosing and resolving performance bottlenecks
- **Integration Challenges**: Solving system integration problems
- **Technical Debt**: Strategies for managing and reducing technical debt

#### Technology Selection
- **Tool Evaluation**: Comparing technologies and making selection recommendations
- **Library Assessment**: Evaluating third-party libraries and dependencies
- **Technology Stack**: Recommendations for technology stack decisions
- **Migration Planning**: Planning technology migrations and upgrades

### Response Format

DEV agent provides:
- **Direct Answer**: Clear, actionable response to the question
- **Code Examples**: Relevant code snippets and implementation examples
- **Best Practices**: Industry best practices and patterns
- **Trade-offs**: Analysis of different approaches and their trade-offs
- **Resources**: Links to documentation, tutorials, and reference materials

### Interactive Features

- **Follow-up Questions**: Ask clarifying questions for better understanding
- **Code Review**: Share code for quick review and feedback
- **Pair Programming**: Collaborative problem-solving and implementation
- **Knowledge Sharing**: Learn about new technologies and approaches

## Context Integration

- Accesses current project codebase and documentation
- References `.synapse/config.yaml` for project standards and preferences
- Maintains conversation history for context in ongoing discussions
- Coordinates with other agents when cross-functional expertise is needed

## Availability

DEV agent is available for:
- **Real-time Consultation**: Immediate responses to development questions
- **Code Reviews**: Quick feedback on code snippets and implementations
- **Technical Discussions**: In-depth technical conversations and planning
- **Learning Support**: Educational guidance and skill development

### Response Time
- **Simple Questions**: Immediate responses (< 30 seconds)
- **Code Analysis**: Quick analysis (< 2 minutes)
- **Complex Problems**: Detailed analysis (< 5 minutes)
- **Research Required**: May require additional time for thorough research

## Best Practices

### Effective Questions
- **Be Specific**: Provide clear context and specific questions
- **Include Code**: Share relevant code snippets when applicable
- **Describe Goals**: Explain what you're trying to achieve
- **Mention Constraints**: Include any technical or business constraints

### Collaboration Etiquette
- **Respectful Communication**: Maintain professional and respectful dialogue
- **Clear Context**: Provide sufficient background information
- **Constructive Feedback**: Be open to suggestions and alternative approaches
- **Knowledge Sharing**: Share insights and learnings with the team

## Integration with Workflow

While `/synapse:dev` provides direct access, for formal development tasks:
1. Use `/synapse:plan` for task planning and breakdown
2. Use `/synapse:implement` for formal implementation tasks
3. Use `/synapse:review` for quality assurance and code review
4. Use `/synapse:dev` for consultation, guidance, and problem-solving