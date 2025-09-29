# Synapse Agent Workflow System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Tests](https://img.shields.io/badge/tests-40%20passing-green.svg)](#testing)
[![Coverage](https://img.shields.io/badge/coverage-60%25-orange.svg)](#quality-metrics)

A powerful CLI tool for orchestrating agent workflows in Claude Code through specialized AI agents that collaborate via structured task logging and state management.

## 🎯 Purpose

Synapse transforms Claude Code into a multi-agent development environment where specialized AI agents (DEV, AUDITOR, DISPATCHER) work together on complex software projects. Each agent has distinct roles and capabilities, coordinating through JSON task logs and shared workflow state.

## 🚀 Quick Start

### Installation

```bash
pip install synapse-workflow
```

### Initialize a Project

```bash
# Initialize in current directory
synapse init

# Initialize with custom project name
synapse init --project-name "My Project"

# Initialize with custom workflow directory
synapse init --workflow-dir ".workflow"

# Force overwrite existing configuration
synapse init --force
```

### Example Output

```
✓ Project initialized successfully!

Project: My Project
Workflow Directory: .synapse

Agents Created (3):
  • DEV agent
  • AUDITOR agent
  • DISPATCHER agent

Commands Created (4):
  • /status
  • /workflow
  • /validate
  • /agent

Files Created (15):
  • .claude/agents/dev.md
  • .claude/agents/auditor.md
  • .claude/agents/dispatcher.md
  • .claude/commands/status.md
  • .claude/commands/workflow.md
  • .claude/commands/validate.md
  • .claude/commands/agent.md
  • .synapse/config.yaml
  • .synapse/task_log.json
  • .synapse/workflow_state.json
  • CLAUDE.md
```

## 📁 Project Structure

After initialization, your project will have this structure:

```
your-project/
├── .claude/                 # Claude Code integration
│   ├── agents/             # Agent templates
│   │   ├── dev.md          # Development agent
│   │   ├── auditor.md      # Quality assurance agent
│   │   └── dispatcher.md   # Coordination agent
│   └── commands/           # Slash commands
│       ├── status.md       # /status command
│       ├── workflow.md     # /workflow command
│       ├── validate.md     # /validate command
│       └── agent.md        # /agent command
├── .synapse/               # Workflow management
│   ├── config.yaml         # Project configuration
│   ├── task_log.json       # Task history
│   └── workflow_state.json # Current state
└── CLAUDE.md               # Main context file
```

## 🤖 Agent Roles

### DEV Agent
- **Primary Role**: Implementation and development
- **Capabilities**: Code writing, debugging, refactoring
- **Focus**: Technical execution and problem-solving

### AUDITOR Agent
- **Primary Role**: Quality assurance and verification
- **Capabilities**: Code review, testing, compliance checking
- **Focus**: Ensuring quality and standards

### DISPATCHER Agent
- **Primary Role**: Task coordination and workflow management
- **Capabilities**: Task assignment, progress tracking, agent coordination
- **Focus**: Project orchestration and communication

## 🔧 Development

### Prerequisites

- Python 3.11 or higher
- Git

### Setup Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd synapse

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### Development Scripts

The project includes convenient development scripts in the `scripts/` directory:

```bash
# One-time development setup
./scripts/dev-setup.sh

# Run all quality checks (linting, type checking, tests)
./scripts/quality-check.sh

# Auto-fix code style issues
./scripts/lint-fix.sh

# Run tests with various options
./scripts/test.sh                # All tests
./scripts/test.sh --coverage     # Tests with coverage report
./scripts/test.sh --contracts    # Contract tests only
./scripts/test.sh --integration  # Integration tests only
./scripts/test.sh --unit         # Unit tests only

# Build distribution packages
./scripts/build.sh

# See Synapse in action
./scripts/demo.sh
```

#### Manual Quality Checks

```bash
# Run all quality checks (recommended before commits)
ruff check . && mypy synapse/ && pytest

# Fix auto-fixable linting issues
ruff check --fix .

# Format code
ruff format .

# Type checking only
mypy synapse/

# Linting only
ruff check .
```

#### Testing

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=synapse --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run CLI contract tests
pytest specs/001-poc-use-specify/contracts/

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_templates/test_agent_templates.py

# Run tests matching pattern
pytest -k "test_init"
```

#### Building and Distribution

```bash
# Build distribution packages
python -m build

# Build wheel only
python -m build --wheel

# Build source distribution only
python -m build --sdist

# Install from local wheel
pip install dist/synapse_workflow-*.whl

# Test installation in clean environment
pip install --force-reinstall dist/synapse_workflow-*.whl
```

### Code Quality Standards

The project maintains high code quality through:

- **Type Safety**: 100% type coverage with mypy
- **Code Style**: ruff formatting and linting
- **Testing**: Comprehensive test suite with pytest
- **Coverage**: Minimum 60% test coverage (80% target for production)

### Development Workflow

1. **Setup**: Run `./scripts/dev-setup.sh` for first-time setup
2. **Make Changes**: Implement features or fixes
3. **Style**: Run `./scripts/lint-fix.sh` to auto-fix style issues
4. **Quality Checks**: Run `./scripts/quality-check.sh` before commits
5. **Testing**: Run `./scripts/test.sh --coverage` for detailed testing
6. **Build**: Run `./scripts/build.sh` to create distribution packages

#### Quick Development Commands

```bash
# Start development (one-time setup)
./scripts/dev-setup.sh

# Daily development cycle
./scripts/lint-fix.sh       # Fix style issues
./scripts/quality-check.sh  # Verify quality
./scripts/test.sh --coverage # Check tests & coverage

# Before committing
./scripts/quality-check.sh

# Before releasing
./scripts/build.sh
```

## 🧪 Testing

### Test Structure

```
tests/
├── cli/                    # CLI command tests
├── integration/            # Integration tests
│   ├── test_claude_integration.py
│   └── test_project_scaffolding.py
└── unit/                   # Unit tests
    └── test_templates/     # Template validation tests
```

### Test Categories

- **Contract Tests**: Verify CLI behavior matches specifications
- **Integration Tests**: End-to-end workflow testing
- **Unit Tests**: Component-level testing
- **Template Tests**: Agent and command template validation

### Running Specific Test Suites

```bash
# Contract tests (requirements validation)
pytest specs/001-poc-use-specify/contracts/ -v

# All template tests
pytest tests/unit/test_templates/ -v

# Claude Code integration tests
pytest tests/integration/test_claude_integration.py -v

# Project scaffolding tests
pytest tests/integration/test_project_scaffolding.py -v
```

## ⚙️ Configuration

### Project Configuration

The `.synapse/config.yaml` file contains project settings:

```yaml
project_name: "Your Project"
synapse_version: "1.0.0"
workflow_dir: ".synapse"
task_log_path: "task_log.json"

agents:
  dev:
    enabled: true
    context_file: ".claude/agents/dev.md"
  auditor:
    enabled: true
    context_file: ".claude/agents/auditor.md"
  dispatcher:
    enabled: true
    context_file: ".claude/agents/dispatcher.md"

claude_commands:
  status:
    enabled: true
    command_file: ".claude/commands/status.md"
  workflow:
    enabled: true
    command_file: ".claude/commands/workflow.md"
  validate:
    enabled: true
    command_file: ".claude/commands/validate.md"
  agent:
    enabled: true
    command_file: ".claude/commands/agent.md"
```

### Environment Variables

No environment variables are required for basic operation.

## 📝 Usage in Claude Code

After initialization, open your project in Claude Code and use:

- **`/status`**: Check workflow status and progress
- **`/workflow`**: Manage workflow state and tasks
- **`/validate`**: Run validation and quality checks
- **`/agent`**: Switch between or communicate with agents

## 🛠️ Architecture

### Core Components

- **CLI**: Click-based command-line interface
- **Models**: Type-safe data models for projects, tasks, and workflow state
- **Services**: Project scaffolding and template validation
- **Templates**: Agent definitions and command implementations

### Key Technologies

- **Click**: CLI framework
- **PyYAML**: Configuration management
- **Pathlib**: File system operations
- **JSON**: Task logging and state persistence

## 📊 Quality Metrics

Current project quality metrics:

- **Tests**: 40 passing, 0 failing
- **Coverage**: 60% (integration-focused)
- **Type Safety**: 100% (mypy strict mode)
- **Code Style**: 100% compliant (ruff)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Quick Contribution Steps

1. Fork the repository
2. Setup development: `./scripts/dev-setup.sh`
3. Create feature branch: `git checkout -b feature-name`
4. Make changes with tests
5. Run quality checks: `./scripts/quality-check.sh`
6. Submit Pull Request

### Contribution Guidelines

- Follow existing code style (ruff)
- Add tests for new functionality
- Ensure type safety (mypy)
- Update documentation as needed
- All tests must pass

See [CONTRIBUTING.md](CONTRIBUTING.md) for complete guidelines including:
- Development setup and workflow
- Testing requirements
- Code quality standards
- Pull request process
- Architecture guidelines

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Documentation**: [Coming Soon]
- **Issue Tracker**: [Repository Issues]
- **PyPI Package**: `pip install synapse-workflow`

## 🆘 Support

For support and questions:

1. Check existing [GitHub Issues]
2. Create a new issue with detailed information
3. Include system information and error messages
4. Provide minimal reproduction steps

---

**Made with ❤️ for the Claude Code community**