"""Task and workflow models for Synapse agent workflow system."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TaskType(Enum):
    """Types of tasks in the workflow."""
    CODING = "CODING"
    REFACTORING = "REFACTORING"
    TESTING = "TESTING"
    VERIFICATION = "VERIFICATION"
    ORCHESTRATION = "ORCHESTRATION"


class TaskStatus(Enum):
    """Status of a task in the workflow."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NEEDS_REVISION = "NEEDS_REVISION"


class SubtaskStatus(Enum):
    """Status of a subtask."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class WorkflowStatus(Enum):
    """Status of the overall workflow."""
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class VerificationStatus(Enum):
    """Status of verification reports."""
    PASSED = "PASSED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


@dataclass
class AgentTemplate:
    """Template for agent behavior that gets scaffolded into projects."""
    id: str
    name: str
    description: str
    prompt_template: str
    rules: list[str]
    capabilities: list[str]
    version: str

    def __post_init__(self) -> None:
        """Validate agent template fields."""
        if not self.id.isalnum() or not self.id.islower():
            raise ValueError("Agent ID must be lowercase alphanumeric")
        if not self.prompt_template.strip():
            raise ValueError("Prompt template must be non-empty")
        if not self.capabilities:
            raise ValueError("Capabilities cannot be empty")


@dataclass
class Subtask:
    """Granular breakdown of a Task."""
    id: str
    parent_task_id: str
    description: str
    status: SubtaskStatus
    order: int
    estimated_effort: str | None = None
    actual_effort: str | None = None
    result: str | None = None
    verification_notes: str | None = None

    def __post_init__(self) -> None:
        """Validate subtask fields."""
        if self.order <= 0:
            raise ValueError("Order must be positive integer")
        if not self.description.strip():
            raise ValueError("Description must be non-empty")


@dataclass
class Task:
    """Unit of work within the workflow."""
    id: str
    description: str
    type: TaskType
    status: TaskStatus
    assigned_agent: str
    acceptance_criteria: list[str]
    subtasks: list[Subtask] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    parent_task_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate task fields."""
        if not self.description.strip():
            raise ValueError("Description must be non-empty")
        if not self.acceptance_criteria:
            raise ValueError("Acceptance criteria must have at least one criterion")

    def add_subtask(self, description: str, order: int) -> Subtask:
        """Add a new subtask to this task."""
        subtask = Subtask(
            id=str(uuid.uuid4()),
            parent_task_id=self.id,
            description=description,
            status=SubtaskStatus.PENDING,
            order=order
        )
        self.subtasks.append(subtask)
        self.updated_at = datetime.now()
        return subtask

    def update_status(self, new_status: TaskStatus) -> None:
        """Update task status with validation."""
        # Define valid transitions
        valid_transitions = {
            TaskStatus.PENDING: [TaskStatus.IN_PROGRESS],
            TaskStatus.IN_PROGRESS: [
                TaskStatus.COMPLETED,
                TaskStatus.NEEDS_REVISION,
                TaskStatus.FAILED,
            ],
            TaskStatus.NEEDS_REVISION: [TaskStatus.IN_PROGRESS, TaskStatus.FAILED],
            TaskStatus.COMPLETED: [],  # Terminal state
            TaskStatus.FAILED: [TaskStatus.IN_PROGRESS]  # Can retry
        }

        if new_status not in valid_transitions.get(self.status, []):
            raise ValueError(f"Invalid status transition from {self.status} to {new_status}")

        self.status = new_status
        self.updated_at = datetime.now()


@dataclass
class WorkflowState:
    """Current state of the project's workflow execution."""
    workflow_id: str
    status: WorkflowStatus
    current_task_id: str | None = None
    task_queue: list[str] = field(default_factory=list)
    completed_tasks: list[str] = field(default_factory=list)
    failed_tasks: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    def update_status(self, new_status: WorkflowStatus) -> None:
        """Update workflow status with validation."""
        # Define valid transitions
        valid_transitions = {
            WorkflowStatus.IDLE: [WorkflowStatus.ACTIVE],
            WorkflowStatus.ACTIVE: [
                WorkflowStatus.COMPLETED,
                WorkflowStatus.PAUSED,
                WorkflowStatus.ERROR,
            ],
            WorkflowStatus.PAUSED: [WorkflowStatus.ACTIVE, WorkflowStatus.ERROR],
            WorkflowStatus.COMPLETED: [],  # Terminal state
            WorkflowStatus.ERROR: [WorkflowStatus.ACTIVE, WorkflowStatus.IDLE]  # Can recover
        }

        if new_status not in valid_transitions.get(self.status, []):
            raise ValueError(
                f"Invalid workflow status transition from {self.status} to {new_status}"
            )

        self.status = new_status
        self.last_activity = datetime.now()

    def assign_task(self, task_id: str) -> None:
        """Assign a task as current and update workflow status."""
        if self.status == WorkflowStatus.IDLE:
            self.update_status(WorkflowStatus.ACTIVE)

        self.current_task_id = task_id
        if task_id in self.task_queue:
            self.task_queue.remove(task_id)

        self.last_activity = datetime.now()

    def complete_task(self, task_id: str) -> None:
        """Mark a task as completed."""
        if self.current_task_id == task_id:
            self.current_task_id = None

        if task_id not in self.completed_tasks:
            self.completed_tasks.append(task_id)

        # Remove from failed tasks if it was there
        if task_id in self.failed_tasks:
            self.failed_tasks.remove(task_id)

        self.last_activity = datetime.now()

        # If no more tasks, mark workflow as completed
        if not self.task_queue and not self.current_task_id:
            self.update_status(WorkflowStatus.COMPLETED)

    def fail_task(self, task_id: str) -> None:
        """Mark a task as failed."""
        if self.current_task_id == task_id:
            self.current_task_id = None

        if task_id not in self.failed_tasks:
            self.failed_tasks.append(task_id)

        self.last_activity = datetime.now()


@dataclass
class TaskLogEntry:
    """Individual entry in the workflow task log."""
    timestamp: datetime
    agent_id: str
    action: str
    message: str
    log_level: str = "INFO"
    task_id: str | None = None
    subtask_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate task log entry fields."""
        if not self.message.strip():
            raise ValueError("Message must be non-empty")
        if self.log_level not in ["INFO", "WARNING", "ERROR", "DEBUG"]:
            raise ValueError("Log level must be INFO, WARNING, ERROR, or DEBUG")


@dataclass
class Finding:
    """Individual verification result within a report."""
    subtask_id: str
    criterion: str
    passed: bool
    details: str
    evidence_path: str | None = None
    automated_check: bool = False

    def __post_init__(self) -> None:
        """Validate finding fields."""
        if not self.details.strip():
            raise ValueError("Details must be non-empty")


@dataclass
class VerificationReport:
    """Output from AUDITOR agent after verification."""
    id: str
    task_id: str
    auditor_id: str
    timestamp: datetime
    overall_status: VerificationStatus
    findings: list[Finding]
    recommendations: list[str] = field(default_factory=list)
    retry_count: int = 0
    evidence: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate verification report fields."""
        if not self.findings:
            raise ValueError("Findings cannot be empty")
        if self.retry_count < 0:
            raise ValueError("Retry count must be non-negative")
        if not self.auditor_id.lower().startswith("auditor"):
            raise ValueError("Auditor ID must be AUDITOR type agent")

    def add_finding(self, subtask_id: str, criterion: str, passed: bool, details: str) -> Finding:
        """Add a new finding to this report."""
        finding = Finding(
            subtask_id=subtask_id,
            criterion=criterion,
            passed=passed,
            details=details
        )
        self.findings.append(finding)
        return finding

    def is_passed(self) -> bool:
        """Check if all findings passed."""
        return all(finding.passed for finding in self.findings)

    def get_failed_findings(self) -> list[Finding]:
        """Get all failed findings."""
        return [finding for finding in self.findings if not finding.passed]
