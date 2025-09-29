"""Models module for Synapse agent workflow system."""

from .project import AgentConfig, InitResult, ProjectConfig, ValidationResult
from .task import (
    AgentTemplate,
    Finding,
    Subtask,
    SubtaskStatus,
    Task,
    TaskLogEntry,
    TaskStatus,
    TaskType,
    VerificationReport,
    VerificationStatus,
    WorkflowState,
    WorkflowStatus,
)

__all__ = [
    # Project models
    "AgentConfig",
    "ProjectConfig",
    "InitResult",
    "ValidationResult",
    # Task models
    "AgentTemplate",
    "Task",
    "Subtask",
    "WorkflowState",
    "TaskLogEntry",
    "Finding",
    "VerificationReport",
    # Enums
    "TaskType",
    "TaskStatus",
    "SubtaskStatus",
    "WorkflowStatus",
    "VerificationStatus",
]
