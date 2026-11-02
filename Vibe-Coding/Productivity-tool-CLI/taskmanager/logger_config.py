"""Logging setup: one call configures file logging for the whole app."""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FILE = str(Path(__file__).resolve().parent.parent / "logs" / "app.log")
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging(log_file=LOG_FILE, level=logging.INFO):
    """Send all log records to a size-limited rotating file."""
    os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)

    root = logging.getLogger()
    if any(isinstance(h, RotatingFileHandler) for h in root.handlers):
        return                                   # already configured; avoid duplicate lines

    handler = RotatingFileHandler(
        log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S"))
    root.setLevel(level)
    root.addHandler(handler)