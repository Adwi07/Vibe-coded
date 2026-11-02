"""Entry point: python main.py <command> [options]"""

import logging
import sys

from taskmanager.cli import run
from taskmanager.logger_config import setup_logging


def main() -> int:
    setup_logging()
    try:
        return run()
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 130
    except Exception:                       # last resort: log the traceback, hide it from the user
        logging.getLogger("main").exception("Unexpected error")
        print("[FATAL] Unexpected error. See logs/app.log for details.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())