# /synapse:audit - Direct Quality Assurance Communication

## Description

Direct communication channel with the AUDITOR agent for quality assurance questions, security consultations, and compliance guidance. This command provides immediate access to quality expertise for specific reviews and assessments.

## Agent Target

**AUDITOR** - Quality assurance and verification

## Implementation

When `/synapse:audit` is invoked:

1. **Direct Connection**: Establish direct communication with AUDITOR agent
2. **Quality Context**: Load current quality standards and project requirements
3. **Expert Assessment**: Provide specialized quality assurance guidance
4. **Security Analysis**: Conduct targeted security assessments
5. **Compliance Review**: Verify adherence to standards and regulations
6. **Risk Evaluation**: Assess potential risks and mitigation strategies

### Example Usage

```
/synapse:audit Can you review this authentication flow for security vulnerabilities?
```

```
/synapse:audit What testing strategy should we use for this microservices architecture?
```

```
/synapse:audit How do we ensure GDPR compliance in our data processing pipeline?
```

### Consultation Types

#### Security Assessment
- **Vulnerability Analysis**: Identify potential security weaknesses
- **Threat Modeling**: Analyze potential attack vectors and threats
- **Security Architecture**: Review security design and implementation
- **Penetration Testing**: Guided security testing approaches

#### Quality Review
- **Code Quality**: Assess code quality and maintainability
- **Architecture Review**: Evaluate system design and architectural decisions
- **Performance Analysis**: Identify performance bottlenecks and optimization opportunities
- **Testing Strategy**: Design comprehensive testing approaches

#### Compliance Guidance
- **Regulatory Compliance**: Ensure adherence to industry regulations (GDPR, HIPAA, SOX)
- **Standards Compliance**: Verify compliance with coding and security standards
- **Audit Preparation**: Prepare for external audits and assessments
- **Documentation Review**: Ensure proper documentation for compliance

#### Risk Management
- **Risk Assessment**: Identify and evaluate project risks
- **Mitigation Strategies**: Develop risk mitigation and contingency plans
- **Quality Gates**: Define quality checkpoints and criteria
- **Incident Response**: Plan for security incidents and quality issues

### Assessment Framework

#### Security Dimensions
- **🔐 Authentication**: Identity verification and access control
- **🛡️ Authorization**: Permission management and role-based access
- **🔒 Data Protection**: Encryption, data handling, and privacy
- **🚫 Input Validation**: Protection against injection attacks
- **📡 Communication Security**: Secure data transmission and APIs

#### Quality Dimensions
- **📊 Code Quality**: Maintainability, readability, and complexity
- **🧪 Test Quality**: Coverage, effectiveness, and reliability
- **📈 Performance**: Speed, scalability, and resource efficiency
- **📚 Documentation**: Completeness, accuracy, and usefulness
- **🔧 Maintainability**: Ease of modification and extensibility

### Response Format

AUDITOR agent provides:
- **Assessment Summary**: Overall quality and security evaluation
- **Detailed Findings**: Specific issues, risks, and recommendations
- **Severity Rating**: Risk levels and priority for addressing issues
- **Remediation Guidance**: Step-by-step instructions for improvements
- **Best Practices**: Industry standards and recommended approaches

### Interactive Features

- **Targeted Reviews**: Focus on specific components or concerns
- **Real-time Feedback**: Immediate assessment of proposed solutions
- **Compliance Checking**: Verify adherence to specific standards
- **Quality Metrics**: Quantitative assessment of quality indicators

## Assessment Tools

### Automated Analysis
- **Static Code Analysis**: Automated code quality and security scanning
- **Dependency Scanning**: Third-party library vulnerability assessment
- **Performance Profiling**: Automated performance analysis
- **Compliance Checking**: Automated standards compliance verification

### Manual Review
- **Expert Analysis**: Human expert review of critical components
- **Threat Modeling**: Manual security threat analysis
- **Architecture Review**: Design pattern and architectural assessment
- **Business Logic Review**: Domain-specific logic validation

## Context Integration

- References `.synapse/config.yaml` for quality standards and security requirements
- Maintains audit trail in `.synapse/task_log.json` for compliance tracking
- Coordinates with `.claude/agents/auditor.md` for specialized procedures
- Integrates with CI/CD pipelines for automated quality gates

## Quality Standards

### Security Standards
- **OWASP Top 10**: Protection against common web vulnerabilities
- **CWE/SANS Top 25**: Defense against most dangerous software errors
- **NIST Framework**: Comprehensive cybersecurity framework
- **Industry Standards**: Sector-specific security requirements

### Quality Standards
- **ISO 25010**: Software quality characteristics and metrics
- **Clean Code**: Principles of readable and maintainable code
- **SOLID Principles**: Object-oriented design principles
- **Testing Pyramid**: Balanced testing strategy across layers

## Reporting and Documentation

### Assessment Reports
- **Executive Summary**: High-level findings for stakeholders
- **Technical Details**: Detailed technical assessment for developers
- **Remediation Plan**: Prioritized action items with timelines
- **Compliance Matrix**: Mapping to specific compliance requirements

### Continuous Monitoring
- **Quality Metrics Tracking**: Monitor quality trends over time
- **Security Posture**: Ongoing security assessment and improvement
- **Compliance Status**: Continuous compliance monitoring
- **Risk Register**: Maintain updated risk assessment and mitigation status

## Integration with Workflow

While `/synapse:audit` provides direct access, for formal quality processes:
1. Use `/synapse:plan` to include quality requirements in planning
2. Use `/synapse:implement` with quality considerations built-in
3. Use `/synapse:review` for comprehensive formal quality reviews
4. Use `/synapse:audit` for targeted assessments and expert consultation