"""Custom exceptions for the Daily Task Manager."""


class TaskManagerError(Exception):
    """Base class for all errors raised by this application."""


class InvalidTaskInputError(TaskManagerError):
    """Empty title, bad date, bad priority, or bad status."""


class TaskNotFoundError(TaskManagerError):
    """Raised when a task ID does not exist."""


class DuplicateTaskError(TaskManagerError):
    """Raised when a pending task with the same title already exists."""


class StorageError(TaskManagerError):
    """Raised when the data file is corrupted or can't be read or written."""