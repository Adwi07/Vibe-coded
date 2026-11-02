"""Data models for the Daily Task Manager.

This module only defines the *shape* of the data. It does no validation,
file I/O, or printing; those belong to manager.py, storage.py, and cli.py.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, Optional


class Priority(Enum):
    """Task urgency. Values are lowercase strings so the JSON stays readable."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @property
    def rank(self) -> int:
        """Numeric rank (0, 1, 2) used for sorting. Follows definition order."""
        return list(Priority).index(self)


class Status(Enum):
    """Lifecycle state of a task."""

    PENDING = "pending"
    DONE = "done"


def _now() -> str:
    """Current local time as an ISO string, e.g. '2026-10-22T11:47:03'."""
    return datetime.now().isoformat(timespec="seconds")


@dataclass
class Task:
    """A single to-do item."""

    id: int
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM
    due_date: Optional[str] = None          # ISO format: 'YYYY-MM-DD'
    status: Status = Status.PENDING
    created_at: str = field(default_factory=_now)
    completed_at: Optional[str] = None

    def mark_done(self) -> None:
        """Mark the task complete and stamp the completion time."""
        self.status = Status.DONE
        self.completed_at = _now()

    def is_overdue(self) -> bool:
        """True if the task is still pending and its due date has passed."""
        if self.status is Status.DONE or not self.due_date:
            return False
        return date.fromisoformat(self.due_date) < date.today()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dict (enums become plain strings)."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "due_date": self.due_date,
            "status": self.status.value,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Rebuild a Task from a dict (the reverse of to_dict)."""
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            priority=Priority(data["priority"]),
            due_date=data.get("due_date"),
            status=Status(data["status"]),
            created_at=data["created_at"],
            completed_at=data.get("completed_at"),
        )