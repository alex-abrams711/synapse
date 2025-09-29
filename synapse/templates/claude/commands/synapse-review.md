# /synapse:review - Quality Assurance and Code Review

## Description

Invoke the AUDITOR agent for comprehensive quality assurance, code review, and verification. This command ensures all implementations meet high standards for code quality, security, performance, and maintainability.

## Agent Target

**AUDITOR** - Quality assurance and verification

## Implementation

When `/synapse:review` is invoked:

1. **Code Analysis**: Comprehensive static analysis of implementation
2. **Quality Assessment**: Evaluate code quality against established standards
3. **Security Review**: Identify potential security vulnerabilities
4. **Performance Analysis**: Assess performance characteristics and bottlenecks
5. **Test Verification**: Validate test coverage and quality
6. **Documentation Review**: Ensure documentation completeness and accuracy

### Example Usage

```
/synapse:review Verify authentication middleware implementation for production readiness
```

### Expected Workflow

1. AUDITOR agent receives implementation for review
2. Performs automated code quality analysis
3. Conducts security vulnerability assessment
4. Reviews test coverage and test quality
5. Validates documentation completeness
6. Generates comprehensive quality report
7. Provides specific recommendations for improvements
8. Coordinates with DEV agent for any necessary changes

### Review Dimensions

#### Code Quality
- **Style Consistency**: Adherence to coding standards
- **Complexity Analysis**: Cyclomatic complexity and maintainability
- **Best Practices**: Implementation of language-specific best practices
- **Architecture**: Proper design patterns and architectural decisions

#### Security Assessment
- **Vulnerability Scanning**: Common security vulnerabilities (OWASP Top 10)
- **Input Validation**: Proper sanitization and validation
- **Authentication/Authorization**: Secure access control implementation
- **Data Protection**: Sensitive data handling and encryption

#### Performance Analysis
- **Algorithm Efficiency**: Big-O analysis and optimization opportunities
- **Resource Usage**: Memory and CPU usage patterns
- **Scalability**: Performance under load and scaling characteristics
- **Caching Strategy**: Effective caching implementation

#### Test Quality
- **Coverage Analysis**: Line, branch, and functional coverage metrics
- **Test Design**: Test case quality and edge case coverage
- **Integration Testing**: End-to-end workflow validation
- **Performance Testing**: Load and stress testing where applicable

### Output Deliverables

- **Quality Report**: Comprehensive analysis with metrics and scores
- **Issue Inventory**: Categorized list of findings with severity levels
- **Recommendations**: Specific, actionable improvement suggestions
- **Compliance Report**: Adherence to standards and best practices
- **Approval Status**: Go/no-go decision for production deployment

## Review Standards

### Quality Gates
- **Critical Issues**: Zero critical security or functionality issues
- **Code Coverage**: Minimum 80% test coverage
- **Performance**: Meets established performance benchmarks
- **Documentation**: All public APIs documented with examples
- **Compliance**: Adheres to project coding standards

### Severity Levels
- **🔴 Critical**: Security vulnerabilities, data loss risks, system crashes
- **🟡 Major**: Performance issues, maintainability concerns, missing tests
- **🟢 Minor**: Style issues, documentation improvements, optimization opportunities
- **ℹ️ Info**: Best practice suggestions, architectural recommendations

## Context Integration

- References `.synapse/config.yaml` for quality standards and thresholds
- Updates `.synapse/task_log.json` with review activities and findings
- Coordinates with `.claude/agents/auditor.md` for specialized review procedures
- Integrates with CI/CD pipelines for automated quality gates

## Approval Process

1. **Automated Analysis**: Run all automated quality checks
2. **Manual Review**: Conduct targeted manual review of critical areas
3. **Risk Assessment**: Evaluate deployment risks and mitigation strategies
4. **Decision**: Approve, request changes, or reject with detailed rationale
5. **Documentation**: Record decision and rationale in quality log
6. **Notification**: Inform relevant stakeholders of review results

## Continuous Improvement

AUDITOR maintains quality metrics over time to:
- **Track Trends**: Monitor code quality evolution
- **Identify Patterns**: Recognize recurring issues and improvement opportunities
- **Update Standards**: Evolve quality standards based on project needs
- **Team Learning**: Share insights and best practices across the team