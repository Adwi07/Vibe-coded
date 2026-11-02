"""Command-line interface: argparse parsing and output formatting."""

import argparse
import sys
from typing import List, Optional

from taskmanager import __version__
from taskmanager.exceptions import TaskManagerError
from taskmanager.manager import TaskManager
from taskmanager.models import Task


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py", description="Daily Task Manager (CLI)"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("add", help="add a new task")
    p.add_argument("title")
    p.add_argument("-p", "--priority", default="medium", help="low | medium | high")
    p.add_argument("-d", "--due", help="due date, YYYY-MM-DD")
    p.add_argument("--desc", default="", help="optional description")

    p = sub.add_parser("list", help="list tasks")
    p.add_argument("--status", help="pending | done")
    p.add_argument("--sort", default="id", help="id | priority | due | created")

    p = sub.add_parser("done", help="mark a task as done")
    p.add_argument("id", type=int)

    p = sub.add_parser("edit", help="edit a task")
    p.add_argument("id", type=int)
    p.add_argument("--title")
    p.add_argument("--desc")
    p.add_argument("-p", "--priority")
    p.add_argument("-d", "--due")

    p = sub.add_parser("delete", help="delete a task")
    p.add_argument("id", type=int)

    p = sub.add_parser("search", help="search task titles")
    p.add_argument("keyword")

    sub.add_parser("stats", help="show productivity statistics")
    return parser


def format_table(tasks: List[Task]) -> str:
    """Render tasks as a plain-text table."""
    if not tasks:
        return "No tasks found."
    rows = [("ID", "Title", "Priority", "Due", "Status")]
    for t in tasks:
        status = "overdue" if t.is_overdue() else t.status.value
        rows.append((str(t.id), t.title, t.priority.value, t.due_date or "-", status))
    widths = [max(len(r[i]) for r in rows) for i in range(5)]
    lines = []
    for n, row in enumerate(rows):
        lines.append("  ".join(cell.ljust(w) for cell, w in zip(row, widths)))
        if n == 0:
            lines.append("  ".join("-" * w for w in widths))
    return "\n".join(lines)


def _dispatch(manager: TaskManager, args: argparse.Namespace) -> None:
    cmd = args.command
    if cmd == "add":
        t = manager.add_task(args.title, args.desc, args.priority, args.due)
        print(f"[OK] Task #{t.id} added.")
    elif cmd == "list":
        print(format_table(manager.list_tasks(args.status, args.sort)))
    elif cmd == "done":
        t = manager.complete_task(args.id)
        print(f"[OK] Task #{t.id} marked as done.")
    elif cmd == "edit":
        t = manager.edit_task(args.id, args.title, args.desc, args.priority, args.due)
        print(f"[OK] Task #{t.id} updated.")
    elif cmd == "delete":
        manager.delete_task(args.id)
        print(f"[OK] Task #{args.id} deleted.")
    elif cmd == "search":
        print(format_table(manager.search(args.keyword)))
    elif cmd == "stats":
        s = manager.stats()
        print(f"Total: {s['total']}  Done: {s['done']}  Pending: {s['pending']}  "
              f"Overdue: {s['overdue']}  Completion: {s['completion_rate']}%")


def run(argv: Optional[List[str]] = None) -> int:
    """Parse arguments, run the command, and return a process exit code."""
    args = build_parser().parse_args(argv)
    try:
        _dispatch(TaskManager(), args)
        return 0
    except TaskManagerError as e:          # one catch for every custom error
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1