"""Business logic layer: validation, task operations, and logging."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from taskmanager import storage
from taskmanager.exceptions import (
    DuplicateTaskError,
    InvalidTaskInputError,
    TaskNotFoundError,
)
from taskmanager.models import Priority, Status, Task

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = str(PROJECT_ROOT / "data" / "tasks.json")
MAX_TITLE_LENGTH = 100


# ---------- validation helpers ----------
def _invalid(message: str) -> InvalidTaskInputError:
    """Log a validation failure and return the exception to raise."""
    logger.warning("Rejected input: %s", message)
    return InvalidTaskInputError(message)


def _clean_title(title: Optional[str]) -> str:
    title = (title or "").strip()
    if not title:
        raise _invalid("Title cannot be empty.")
    if len(title) > MAX_TITLE_LENGTH:
        raise _invalid(f"Title is too long (max {MAX_TITLE_LENGTH} characters).")
    return title


def _parse_priority(value: str) -> Priority:
    try:
        return Priority(str(value).lower())
    except ValueError:
        valid = ", ".join(p.value for p in Priority)
        raise _invalid(f"Invalid priority '{value}'. Choose one of: {valid}.") from None


def _check_date(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise _invalid(f"Invalid date '{value}'. Use YYYY-MM-DD.") from None
    return value


class TaskManager:
    """Creates, updates, queries, and persists tasks."""

    def __init__(self, path: str = DATA_FILE) -> None:
        self.path = path
        self.tasks: List[Task] = storage.load_tasks(self.path)

    # ---------- internals ----------
    def _next_id(self) -> int:
        return max((t.id for t in self.tasks), default=0) + 1

    def _ensure_unique(self, title: str, ignore_id: Optional[int] = None) -> None:
        """Raise DuplicateTaskError if another pending task has this title."""
        for t in self.tasks:
            if (
                t.id != ignore_id
                and t.status is Status.PENDING
                and t.title.casefold() == title.casefold()
            ):
                logger.warning("Rejected task: duplicate of id=%d (%r)", t.id, title)
                raise DuplicateTaskError(
                    f"A pending task named '{title}' already exists (id {t.id})."
                )

    def _save(self) -> None:
        storage.save_tasks(self.tasks, self.path)

    # ---------- operations ----------
    def add_task(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        due_date: Optional[str] = None,
    ) -> Task:
        title = _clean_title(title)
        prio = _parse_priority(priority)
        due_date = _check_date(due_date)
        self._ensure_unique(title)

        task = Task(
            id=self._next_id(),
            title=title,
            description=description,
            priority=prio,
            due_date=due_date,
        )
        self.tasks.append(task)
        self._save()
        logger.info("Task added: id=%d title=%r", task.id, task.title)
        return task

    def list_tasks(
        self, status: Optional[str] = None, sort_by: str = "id"
    ) -> List[Task]:
        tasks = list(self.tasks)

        if status is not None:
            try:
                wanted = Status(str(status).lower())
            except ValueError:
                raise _invalid(
                    f"Invalid status '{status}'. Choose pending or done."
                ) from None
            tasks = [t for t in tasks if t.status is wanted]

        if sort_by == "priority":
            tasks.sort(key=lambda t: -t.priority.rank)        # high first
        elif sort_by == "due":
            tasks.sort(key=lambda t: (t.due_date is None, t.due_date or ""))
        elif sort_by == "created":
            tasks.sort(key=lambda t: t.created_at)
        elif sort_by != "id":
            raise _invalid(
                f"Invalid sort '{sort_by}'. Choose id, priority, due, or created."
            )
        return tasks

    def get_task(self, task_id: int) -> Task:
        for task in self.tasks:
            if task.id == task_id:
                return task
        logger.warning("Task not found: id=%s", task_id)
        raise TaskNotFoundError(f"Task {task_id} not found")

    def complete_task(self, task_id: int) -> Task:
        task = self.get_task(task_id)
        if task.status is Status.DONE:
            raise _invalid(f"Task {task_id} is already done.")
        task.mark_done()
        self._save()
        logger.info("Task completed: id=%d title=%r", task.id, task.title)
        return task

    def edit_task(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        due_date: Optional[str] = None,
    ) -> Task:
        task = self.get_task(task_id)
        if all(v is None for v in (title, description, priority, due_date)):
            raise _invalid("Nothing to update. Provide at least one field.")

        # Validate everything first so a bad value can't leave a half-edited task.
        new_title = _clean_title(title) if title is not None else None
        new_priority = _parse_priority(priority) if priority is not None else None
        new_due = _check_date(due_date) if due_date is not None else None
        if new_title is not None and task.status is Status.PENDING:
            self._ensure_unique(new_title, ignore_id=task_id)

        if new_title is not None:
            task.title = new_title
        if description is not None:
            task.description = description
        if new_priority is not None:
            task.priority = new_priority
        if new_due is not None:
            task.due_date = new_due

        self._save()
        logger.info("Task edited: id=%d", task.id)
        return task

    def delete_task(self, task_id: int) -> None:
        task = self.get_task(task_id)
        self.tasks.remove(task)
        self._save()
        logger.info("Task deleted: id=%d title=%r", task.id, task.title)

    def search(self, keyword: str) -> List[Task]:
        needle = keyword.lower()
        results = [t for t in self.tasks if needle in t.title.lower()]
        logger.info("Search %r returned %d result(s)", needle, len(results))
        return results

    def stats(self) -> Dict[str, Any]:
        total = len(self.tasks)
        done = sum(1 for t in self.tasks if t.status is Status.DONE)
        return {
            "total": total,
            "done": done,
            "pending": total - done,
            "overdue": sum(1 for t in self.tasks if t.is_overdue()),
            "completion_rate": round(done / total * 100, 1) if total else 0.0,
        }