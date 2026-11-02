"""JSON persistence layer with error handling, atomic saves, and logging."""

import json
import logging
import os

from taskmanager.exceptions import StorageError
from taskmanager.models import Task

logger = logging.getLogger(__name__)


def load_tasks(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        tasks = [Task.from_dict(d) for d in data]
        logger.info("Loaded %d tasks from %s", len(tasks), path)
        return tasks
    except FileNotFoundError:
        logger.info("No data file at %s; starting with an empty list", path)
        return []
    except json.JSONDecodeError as e:              # must come before ValueError
        logger.error("Corrupted JSON in %s: %s", path, e)
        raise StorageError(f"Corrupted JSON in {path}: {e}") from e
    except (KeyError, ValueError, TypeError) as e:
        logger.error("Invalid task data in %s: %r", path, e)
        raise StorageError(f"Invalid task data in {path}: {e!r}") from e
    except OSError as e:
        logger.error("Could not read %s: %s", path, e)
        raise StorageError(f"Could not read {path}: {e}") from e


def save_tasks(tasks, path):
    tmp_path = path + ".tmp"
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump([t.to_dict() for t in tasks], f, indent=2)
        os.replace(tmp_path, path)                 # atomic swap
        logger.info("Saved %d tasks to %s", len(tasks), path)
    except OSError as e:
        logger.error("Could not save tasks to %s: %s", path, e)
        raise StorageError(f"Could not save tasks to {path}: {e}") from e
    finally:
        if os.path.exists(tmp_path):               # leftover from a failed write
            os.remove(tmp_path)