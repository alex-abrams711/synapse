"""Project scaffolding service for Synapse agent workflow system."""

import json
import uuid
from datetime import datetime
from pathlib import Path

import yaml

from synapse.models.project import AgentConfig, InitResult, ProjectConfig
from synapse.models.task import WorkflowState, WorkflowStatus


class ProjectScaffolder:
    """Service for scaffolding new Synapse projects with agent templates."""

    def __init__(self) -> None:
        """Initialize the project scaffolder."""
        self.template_dir = Path(__file__).parent.parent / "templates"

    def create_project_structure(
        self,
        project_path: Path,
        config: ProjectConfig,
        force: bool = False
    ) -> InitResult:
        """Create complete project structure with templates and configuration."""
        result = InitResult(
            success=False,
            project_name=config.project_name,
            workflow_dir=config.workflow_dir
        )

        try:
            # Check if project already exists
            workflow_path = project_path / config.workflow_dir
            if workflow_path.exists() and not force:
                result.add_warning(
                    f"Project already initialized in {workflow_path}. Use --force to overwrite."
                )
                return result

            # Create directory structure
            self._create_directories(project_path, config, result)

            # Create agent templates
            self._create_agent_templates(project_path, config, result)

            # Create command templates
            self._create_command_templates(project_path, config, result)

            # Create main CLAUDE.md context file
            self._create_claude_context(project_path, config, result)

            # Create configuration files
            self._create_configuration_files(project_path, config, result)

            # Create initial task log
            self._create_initial_task_log(project_path, config, result)

            # Create initial workflow state
            self._create_initial_workflow_state(project_path, config, result)

            result.success = True

        except Exception as e:
            result.add_warning(f"Error during project creation: {e}")
            result.success = False

        return result

    def _create_directories(
        self, project_path: Path, config: ProjectConfig, result: InitResult
    ) -> None:
        """Create required directory structure."""
        directories = [
            project_path / ".claude",
            project_path / ".claude" / "agents",
            project_path / ".claude" / "commands",
            project_path / config.workflow_dir
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            result.add_file_created(str(directory.relative_to(project_path)))

    def _create_agent_templates(
        self, project_path: Path, config: ProjectConfig, result: InitResult
    ) -> None:
        """Create agent template files from templates."""
        agents = ["dev", "auditor", "dispatcher"]

        for agent_id in agents:
            # Read template
            template_path = self.template_dir / "claude" / "agents" / f"{agent_id}.md"
            if not template_path.exists():
                result.add_warning(f"Template not found: {template_path}")
                continue

            with open(template_path, encoding='utf-8') as f:
                template_content = f.read()

            # Replace placeholders
            content = self._replace_placeholders(template_content, config)

            # Write agent file
            agent_file = project_path / ".claude" / "agents" / f"{agent_id}.md"
            with open(agent_file, 'w', encoding='utf-8') as f:
                f.write(content)

            result.add_agent_created(agent_id)
            result.add_file_created(str(agent_file.relative_to(project_path)))

    def _create_command_templates(
        self, project_path: Path, config: ProjectConfig, result: InitResult
    ) -> None:
        """Create command template files from templates."""
        commands = ["status", "workflow", "validate", "agent"]

        for command_name in commands:
            # Read template
            template_path = self.template_dir / "claude" / "commands" / f"{command_name}.md"
            if not template_path.exists():
                result.add_warning(f"Command template not found: {template_path}")
                continue

            with open(template_path, encoding='utf-8') as f:
                template_content = f.read()

            # Replace placeholders
            content = self._replace_placeholders(template_content, config)

            # Write command file
            command_file = project_path / ".claude" / "commands" / f"{command_name}.md"
            with open(command_file, 'w', encoding='utf-8') as f:
                f.write(content)

            result.add_command_created(command_name)
            result.add_file_created(str(command_file.relative_to(project_path)))

    def _create_claude_context(
        self, project_path: Path, config: ProjectConfig, result: InitResult
    ) -> None:
        """Create main CLAUDE.md context file."""
        # Read template
        template_path = self.template_dir / "claude" / "CLAUDE.md"
        if not template_path.exists():
            result.add_warning(f"CLAUDE.md template not found: {template_path}")
            return

        with open(template_path, encoding='utf-8') as f:
            template_content = f.read()

        # Replace placeholders
        content = self._replace_placeholders(template_content, config)

        # Write CLAUDE.md file
        claude_file = project_path / "CLAUDE.md"
        with open(claude_file, 'w', encoding='utf-8') as f:
            f.write(content)

        result.add_file_created("CLAUDE.md")

    def _create_configuration_files(
        self, project_path: Path, config: ProjectConfig, result: InitResult
    ) -> None:
        """Create configuration files."""
        # Read template
        template_path = self.template_dir / "synapse" / "config.yaml"
        if not template_path.exists():
            result.add_warning(f"Config template not found: {template_path}")
            return

        with open(template_path, encoding='utf-8') as f:
            template_content = f.read()

        # Replace placeholders
        content = self._replace_placeholders(template_content, config)

        # Write config file
        config_file = project_path / config.workflow_dir / "config.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)

        result.add_file_created(str(config_file.relative_to(project_path)))

    def _create_initial_task_log(
        self, project_path: Path, config: ProjectConfig, result: InitResult
    ) -> None:
        """Create initial empty task log."""
        # Read template
        template_path = self.template_dir / "synapse" / "task_log.json"
        if not template_path.exists():
            result.add_warning(f"Task log template not found: {template_path}")
            return

        with open(template_path, encoding='utf-8') as f:
            template_content = f.read()

        # Add workflow_id to replacements
        workflow_id = str(uuid.uuid4())
        template_content = template_content.replace("{{workflow_id}}", workflow_id)

        # Replace other placeholders
        content = self._replace_placeholders(template_content, config)

        # Write task log file
        log_file = project_path / config.workflow_dir / config.task_log_path
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(content)

        result.add_file_created(str(log_file.relative_to(project_path)))

    def _create_initial_workflow_state(
        self, project_path: Path, config: ProjectConfig, result: InitResult
    ) -> None:
        """Create initial workflow state file."""
        workflow_state = WorkflowState(
            workflow_id=str(uuid.uuid4()),
            status=WorkflowStatus.IDLE
        )

        state_data = {
            "workflow_id": workflow_state.workflow_id,
            "status": workflow_state.status.value,
            "current_task_id": workflow_state.current_task_id,
            "task_queue": workflow_state.task_queue,
            "completed_tasks": workflow_state.completed_tasks,
            "failed_tasks": workflow_state.failed_tasks,
            "created_at": workflow_state.created_at.isoformat(),
            "last_activity": workflow_state.last_activity.isoformat()
        }

        state_file = project_path / config.workflow_dir / "workflow_state.json"
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, indent=2)

        result.add_file_created(str(state_file.relative_to(project_path)))


    def _replace_placeholders(self, content: str, config: ProjectConfig) -> str:
        """Replace template placeholders with actual values."""
        replacements = {
            "{{project_name}}": config.project_name,
            "{{synapse_version}}": config.synapse_version,
            "{{workflow_dir}}": config.workflow_dir,
            "{{created_at}}": config.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }

        result = content
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)

        return result

    def detect_project_name(self, project_path: Path) -> str:
        """Detect project name from directory or existing files."""
        # Try to get from directory name
        project_name = project_path.name

        # Check if there's an existing package.json, pyproject.toml, etc.
        config_files = [
            (project_path / "package.json", "name"),
            (project_path / "pyproject.toml", "name"),
            (project_path / "setup.py", None),  # More complex parsing needed
            (project_path / "Cargo.toml", "name")
        ]

        for config_file, name_key in config_files:
            if config_file.exists():
                try:
                    if config_file.suffix == ".json":
                        import json
                        with open(config_file, encoding='utf-8') as f:
                            data = json.load(f)
                        if name_key and name_key in data and isinstance(data[name_key], str):
                            return str(data[name_key])
                    elif config_file.suffix == ".toml":
                        # Simple TOML parsing for name field
                        with open(config_file, encoding='utf-8') as f:
                            content = f.read()
                        # Look for name = "project_name" pattern
                        import re
                        match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                        if match:
                            return match.group(1)
                except Exception:
                    # If parsing fails, continue with directory name
                    pass

        # Clean up directory name
        if project_name:
            # Remove common suffixes and clean up
            project_name = project_name.replace('-', ' ').replace('_', ' ')
            project_name = ' '.join(word.capitalize() for word in project_name.split())

        return project_name or "Synapse Project"

    def is_project_initialized(self, project_path: Path, workflow_dir: str = ".synapse") -> bool:
        """Check if a project is already initialized with Synapse."""
        workflow_path = project_path / workflow_dir
        config_file = workflow_path / "config.yaml"

        return workflow_path.exists() and config_file.exists()

    def get_project_config(
        self, project_path: Path, workflow_dir: str = ".synapse"
    ) -> ProjectConfig | None:
        """Load existing project configuration if available."""
        config_file = project_path / workflow_dir / "config.yaml"

        if not config_file.exists():
            return None

        try:
            with open(config_file, encoding='utf-8') as f:
                data = yaml.safe_load(f)

            # Create ProjectConfig from loaded data
            config = ProjectConfig(
                project_name=data.get("project_name", "Unknown Project"),
                synapse_version=data.get("synapse_version", "1.0.0"),
                workflow_dir=data.get("workflow_dir", workflow_dir),
                task_log_path=data.get("task_log_path", "task_log.json"),
                created_at=datetime.fromisoformat(
                    data.get("created_at", datetime.now().isoformat())
                ),
                last_updated=datetime.fromisoformat(
                    data.get("last_updated", datetime.now().isoformat())
                )
            )

            # Load agent configurations
            if "agents" in data:
                for agent_id, agent_data in data["agents"].items():
                    agent_config = AgentConfig(
                        agent_id=agent_id,
                        enabled=agent_data.get("enabled", True),
                        context_file=agent_data.get(
                            "context_file", f".claude/agents/{agent_id}.md"
                        ),
                        custom_prompt=agent_data.get("custom_prompt"),
                        custom_rules=agent_data.get("custom_rules", [])
                    )
                    config.agents[agent_id] = agent_config

            return config

        except Exception:
            # If loading fails, return None
            return None
