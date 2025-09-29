# Contributing to Synapse

Thank you for your interest in contributing to Synapse! This document provides guidelines and information for contributors.

## 🚀 Quick Start

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/synapse.git
   cd synapse
   ```

2. **Setup Development Environment**
   ```bash
   ./scripts/dev-setup.sh
   ```

3. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make Changes and Test**
   ```bash
   # Make your changes
   ./scripts/lint-fix.sh       # Fix style issues
   ./scripts/quality-check.sh  # Run quality checks
   ```

5. **Submit Pull Request**

## 📋 Development Guidelines

### Code Quality Requirements

All contributions must meet these quality standards:

- ✅ **All tests pass**: `./scripts/test.sh`
- ✅ **Type safety**: `mypy synapse/` with no errors
- ✅ **Code style**: `ruff check .` with no issues
- ✅ **Test coverage**: New code should include tests

### Development Scripts

Use the provided scripts for consistent development:

```bash
./scripts/dev-setup.sh      # One-time setup
./scripts/quality-check.sh  # Full quality check
./scripts/lint-fix.sh       # Auto-fix style issues
./scripts/test.sh           # Run tests
./scripts/build.sh          # Build package
./scripts/demo.sh           # See Synapse demo
```

### Commit Guidelines

- Use clear, descriptive commit messages
- Include tests for new functionality
- Update documentation for user-facing changes
- Run `./scripts/quality-check.sh` before committing

Example commit messages:
```
feat: add support for custom agent templates
fix: resolve template placeholder substitution bug
docs: update README with new CLI options
test: add integration tests for workflow state
```

### Pull Request Process

1. **Pre-submission Checklist**
   - [ ] All tests pass (`./scripts/test.sh`)
   - [ ] Quality checks pass (`./scripts/quality-check.sh`)
   - [ ] Code is properly documented
   - [ ] Changes are covered by tests

2. **Pull Request Template**
   ```
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Refactoring

   ## Testing
   - [ ] Tests added/updated
   - [ ] All tests pass
   - [ ] Manual testing performed

   ## Quality Checks
   - [ ] `./scripts/quality-check.sh` passes
   - [ ] Code style follows project standards
   ```

## 🧪 Testing Guidelines

### Test Types

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **Contract Tests**: Verify CLI behavior meets specifications

### Writing Tests

- Place tests in appropriate directories under `tests/`
- Use descriptive test names: `test_init_creates_project_structure`
- Include both positive and negative test cases
- Mock external dependencies appropriately

### Running Tests

```bash
./scripts/test.sh                # All tests
./scripts/test.sh --coverage     # With coverage
./scripts/test.sh --unit         # Unit tests only
./scripts/test.sh --integration  # Integration tests only
./scripts/test.sh --contracts    # Contract tests only
```

## 📝 Documentation Standards

### Code Documentation

- Use Google-style docstrings for functions and classes
- Include type hints for all function parameters and returns
- Document complex logic with inline comments

### README Updates

- Update README.md for user-facing changes
- Include examples for new features
- Update installation or usage instructions as needed

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment Information**
   - Python version
   - Operating system
   - Synapse version

2. **Reproduction Steps**
   - Minimal example to reproduce the issue
   - Expected vs actual behavior
   - Error messages and stack traces

3. **Additional Context**
   - Related configuration files
   - Any workarounds discovered

## 💡 Feature Requests

For new features:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** and problem being solved
3. **Propose a solution** with examples if possible
4. **Consider backward compatibility** implications

## 🏗️ Architecture Guidelines

### Project Structure

```
synapse/
├── cli/           # Click CLI commands
├── models/        # Type-safe data models
├── services/      # Business logic services
├── templates/     # Agent and command templates
└── __init__.py    # Package initialization
```

### Design Principles

- **Type Safety**: Use type hints and mypy for verification
- **Separation of Concerns**: Keep CLI, business logic, and data separate
- **Template-Driven**: Use templates for extensibility
- **Test-Driven**: Write tests before implementation
- **User-Focused**: Prioritize user experience and documentation

## 🤝 Community Guidelines

- Be respectful and inclusive
- Help others learn and grow
- Share knowledge and best practices
- Provide constructive feedback
- Celebrate contributions of all sizes

## 📞 Getting Help

- **Documentation**: Check README.md first
- **Issues**: Search existing GitHub issues
- **Questions**: Create a new issue with the "question" label
- **Discussions**: Use GitHub Discussions for broader topics

---

Thank you for contributing to Synapse! 🎉