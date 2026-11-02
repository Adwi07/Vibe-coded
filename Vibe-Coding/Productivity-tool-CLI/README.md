# Productivity-tool-CLI

A command-line **Daily Task Manager** written in Python, built step by step with an
AI coding assistant ("vibe coding") instead of a single giant prompt.

## Features
- Add, list, edit, complete, delete, and search tasks
- Priorities (low / medium / high), due dates, and automatic overdue detection
- Sorting by id, priority, due date, or creation time
- Productivity stats: total, done, pending, overdue, completion rate
- JSON persistence with atomic saves, so a crash cannot corrupt the data file
- Custom exception hierarchy with clean, traceback-free error messages
- Rotating file logging to `logs/app.log`
- 22 unit tests using the standard library `unittest`

## Requirements
- Python 3.9 or newer
- No external dependencies (standard library only)

## Setup
```bash
git clone <your-repo-url>
cd Productivity-tool-CLI
python main.py --help
```

## Usage
```bash
python main.py add "Finish OS lab" -p high -d 2026-10-25
python main.py add "Revise DBMS notes" --desc "Unit 3 and 4"
python main.py list
python main.py list --status pending --sort priority
python main.py done 1
python main.py edit 2 --title "Revise DBMS unit 3" -p high
python main.py search "dbms"
python main.py stats
python main.py delete 2
```

| Command | Options |
|---|---|
| `add <title>` | `-p/--priority`, `-d/--due YYYY-MM-DD`, `--desc` |
| `list` | `--status pending\|done`, `--sort id\|priority\|due\|created` |
| `done <id>` | |
| `edit <id>` | `--title`, `--desc`, `-p/--priority`, `-d/--due` |
| `delete <id>` | |
| `search <keyword>` | |
| `stats` | |

## Sample Output
```
$ python main.py list --sort priority
ID  Title              Priority  Due         Status
--  -----------------  --------  ----------  -------
1   Finish OS lab      high      2026-10-25  pending
2   Revise DBMS notes  medium    -           pending
3   Old assignment     low       2026-10-01  overdue

$ python main.py stats
Total: 3  Done: 1  Pending: 2  Overdue: 1  Completion: 33.3%

$ python main.py done 99
[ERROR] Task 99 not found
```

## Run the Tests
```bash
python -m unittest discover -s tests -t . -v
```
Each test uses its own temporary directory, so real data is never touched.

## Project Structure
```
Productivity-tool-CLI/
├── main.py                  # entry point: sets up logging, calls cli.run()
├── README.md
├── requirements.txt
├── .gitignore
├── taskmanager/             # the package
│   ├── __init__.py          # package marker and __version__
│   ├── models.py            # Task dataclass, Priority and Status enums
│   ├── exceptions.py        # custom exception hierarchy
│   ├── logger_config.py     # RotatingFileHandler setup
│   ├── storage.py           # JSON load/save with try/except/finally
│   ├── manager.py           # business logic and validation
│   └── cli.py               # argparse subcommands and output formatting
├── tests/
│   ├── __init__.py
│   └── test_manager.py      # 22 unit tests
├── data/                    # tasks.json is created at runtime
└── logs/                    # app.log is created at runtime
```

## Architecture
```
main.py -> cli.py -> manager.py -> storage.py -> data/tasks.json
                         |             |
                     models.py    exceptions.py
(logger_config.py is configured once by main.py; every module logs through it)
```
Imports only flow downward. `storage.py` never imports `manager.py` or `cli.py`, which
prevents circular imports and lets the manager be tested without the terminal.

## Exception Hierarchy
```
TaskManagerError
├── InvalidTaskInputError   empty title, bad date / priority / status / sort
├── TaskNotFoundError       task ID does not exist
├── DuplicateTaskError      a pending task with the same title already exists
└── StorageError            corrupted JSON or file I/O failure
```
`cli.py` catches `TaskManagerError` once and prints `[ERROR] <message>`.
Anything else is a genuine bug: `main.py` logs the full traceback and exits with code 2.

Exit codes: `0` success, `1` handled user error, `2` unexpected error, `130` Ctrl+C.

## Logging
Logs go to `logs/app.log` (1 MB per file, 3 backups).
```
2026-10-23 02:02:55 | INFO     | taskmanager.manager | Task added: id=1 title='Study OS'
2026-10-23 02:02:55 | WARNING  | taskmanager.manager | Task not found: id=99
2026-10-23 02:10:41 | ERROR    | taskmanager.storage | Corrupted JSON in data/test.json: ...
```
INFO is normal operation, WARNING is a user mistake, ERROR is a system failure.

## Requirements Checklist
| Requirement | Where |
|---|---|
| Command-line Python app | Daily Task Manager |
| At least 4 Python modules | models, exceptions, logger_config, storage, manager, cli, main |
| At least 1 package | `taskmanager/` |
| try / except / finally | `storage.py`: `save_tasks` writes a temp file, swaps it in with `os.replace`, and cleans up in `finally` |
| At least 1 custom exception | `exceptions.py` (5 classes) |
| Logging to a file | `logger_config.py` -> `logs/app.log` |
| Imports between modules | see Architecture |
| README with 5+ prompts | below (11 prompts) |

## Vibe Coding Process: Prompts Used

**Prompt 1 (requirements):**
"I want to build a command-line Daily Task Manager in Python for a college challenge. Before writing any code, restate the requirements in your own words and ask me clarifying questions. Do not generate code yet."

**Prompt 2 (structure):**
"For the Daily Task Manager CLI in Python (argparse subcommands, JSON storage, standard library only), suggest a package and module structure. Give each file exactly one responsibility, show which modules may import which, and list where I'll put custom exceptions, logging, and try/except/finally. Do not write any implementation code yet."

**Prompt 3 (models):**
"Write only `taskmanager/models.py` for my Daily Task Manager CLI. Include a `Task` dataclass, `Priority` and `Status` enums, and `to_dict()` / `from_dict()` methods. Standard library only, Python 3.9 compatible, with type hints and docstrings. No validation and no file I/O, because those belong in other modules."

**Prompt 4 (naive storage and manager):**
"Write `taskmanager/storage.py` and `taskmanager/manager.py` for my Daily Task Manager CLI. storage.py should load and save tasks as JSON using the Task model. manager.py should have a TaskManager class with add, list, get, complete, delete, and search. Keep it simple and minimal: no error handling, no logging, no validation. I'll add those in later steps."

**Prompt 5 (error: get_task returned None):**
"Pylance reports 2 problems in manager.py: `task.mark_done()` in complete_task and `self.tasks.remove(task)` in delete_task, because get_task can return None when the ID doesn't exist. Explain the cause and fix it properly by raising a custom TaskNotFoundError instead of returning None. Keep the change minimal."

**Prompt 6 (error: FileNotFoundError):**
"I ran my Daily Task Manager and got this error: `FileNotFoundError: [Errno 2] No such file or directory: 'data/tasks.json'`, raised in storage.load_tasks when TaskManager() starts. Explain the cause and fix it so a first run with no data file works and starts with an empty task list. Also make sure save_tasks creates the data folder if it's missing. Keep the change minimal."

**Prompt 7 (exception handling):**
"Add proper exception handling to my Daily Task Manager. In exceptions.py, build a hierarchy under TaskManagerError: InvalidTaskInputError, TaskNotFoundError, DuplicateTaskError, StorageError. In storage.py, use try/except/finally: catch corrupted JSON and OS errors and re-raise them as StorageError, and make save_tasks atomic by writing a temp file and using os.replace, with cleanup in finally. In manager.py, validate title, priority, due date and status, and reject duplicate pending titles. No logging yet."

**Prompt 8 (logging):**
"Add file logging to my Daily Task Manager. Create logger_config.py with a setup_logging() function using RotatingFileHandler that writes to logs/app.log with timestamp, level, module name and message. Use logging.getLogger(__name__) in storage.py and manager.py. Log INFO for successful operations (add, complete, delete, load, save), WARNING for validation failures and not-found errors, and ERROR for storage failures. Don't change any behavior."

**Prompt 9 (refactor):**
"Refactor manager.py without changing behavior: remove the repeated 'log a warning, then raise InvalidTaskInputError' pattern with one helper, add type hints and docstrings, and resolve the data file path relative to the project root instead of the current directory. Also add edit_task, a stats method, sorting in list_tasks (id, priority, due, created), and refuse to complete a task that's already done."

**Prompt 10 (CLI):**
"Now write cli.py with argparse subcommands: add, list, done, edit, delete, search, stats. Catch TaskManagerError once and print a clean message with no traceback. Then write main.py as a thin entry point that sets up logging and calls cli.run(). Do not use argparse `choices` for priority or status, because validation belongs in manager.py."

**Prompt 11 (tests):**
"Write unittest tests for my TaskManager in tests/test_manager.py. Use a temporary directory per test so real data is never touched. Cover add and persistence, ID reuse after delete, validation errors, duplicate handling, completing twice, not-found errors, edit atomicity, search, sorting, stats, and a corrupted JSON file. Silence logging during tests."

## Errors Hit and How They Were Fixed
1. **`get_task` returned `None`.** Pylance flagged `task.mark_done()` before the code even ran. Fix: raise `TaskNotFoundError`. (Prompt 5)
2. **Broken indentation after applying that fix.** The editor's problem count rose from 2 to 4 because the method body lost its indent. Re-indenting brought it back to 0.
3. **`FileNotFoundError` on first run.** `load_tasks` assumed `data/tasks.json` existed. Fix: a missing file means an empty task list. (Prompt 6)
4. **Corrupted JSON crashed with a raw `JSONDecodeError`.** Fix: re-raise it as `StorageError` naming the file, and log it at ERROR level. (Prompt 7)
5. **Relative paths.** Running the app from another folder would have created a second `data/` directory. Fix: resolve paths from the project root. (Prompt 9)
6. **Test code pasted into `manager.py` by mistake.** The editor showed 15 problems. Fix: reset `manager.py` to the clean version and move the tests into `tests/test_manager.py`.
7. **Type warning in a test.** Pylance flagged `add_task(None)`, which is intentional bad input. Fix: `# type: ignore[arg-type]` on that line instead of loosening the type hint.

## What I Learned
- <Rewrite these in your own words: the `except` order matters because `JSONDecodeError` is a subclass of `ValueError`, so the specific handler must come first.>
- <Writing to a temp file and swapping it in with `os.replace` means a crash mid-write cannot corrupt the real data file, and `finally` guarantees the temp file is cleaned up.>
- <Validation lives in one layer (`manager.py`), so every caller gets the same rules.>
- <Static analysis caught a real bug before I ran the code, and AI output must be read before it is pasted, because pasting into the wrong file cost me a debugging round.>

## Author
Adwi