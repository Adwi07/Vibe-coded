"""Unit tests for TaskManager. Every test uses its own temp directory."""

import logging
import os
import tempfile
import unittest

from taskmanager.exceptions import (
    DuplicateTaskError,
    InvalidTaskInputError,
    StorageError,
    TaskNotFoundError,
)
from taskmanager.manager import TaskManager
from taskmanager.models import Status


def setUpModule():
    logging.disable(logging.CRITICAL)      # keep test output clean


def tearDownModule():
    logging.disable(logging.NOTSET)


class TaskManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "tasks.json")
        self.m = TaskManager(path=self.path)

    def tearDown(self):
        self.tmp.cleanup()

    # ---------- add and persistence ----------
    def test_add_task_persists_to_disk(self):
        self.m.add_task("Finish OS lab", priority="high", due_date="2026-10-25")
        reloaded = TaskManager(path=self.path)
        self.assertEqual(len(reloaded.tasks), 1)
        self.assertEqual(reloaded.tasks[0].title, "Finish OS lab")

    def test_missing_file_starts_empty(self):
        self.assertEqual(self.m.tasks, [])

    def test_no_temp_file_left_behind(self):
        self.m.add_task("Study")
        self.assertFalse(os.path.exists(self.path + ".tmp"))

    def test_ids_are_not_reused_after_delete(self):
        for name in ("A", "B", "C"):
            self.m.add_task(name)
        self.m.delete_task(2)
        self.assertEqual(self.m.add_task("D").id, 4)

    # ---------- validation ----------
    def test_empty_title_rejected(self):
        for bad in ("", "   ", None):
            with self.assertRaises(InvalidTaskInputError):
                self.m.add_task(bad)  # type: ignore[arg-type]

    def test_invalid_priority_rejected(self):
        with self.assertRaises(InvalidTaskInputError):
            self.m.add_task("Lab", priority="urgent")

    def test_invalid_date_rejected(self):
        with self.assertRaises(InvalidTaskInputError):
            self.m.add_task("Lab", due_date="25-10-2026")

    def test_invalid_status_filter_rejected(self):
        with self.assertRaises(InvalidTaskInputError):
            self.m.list_tasks(status="finished")

    # ---------- duplicates ----------
    def test_duplicate_pending_title_rejected_case_insensitive(self):
        self.m.add_task("Study OS")
        with self.assertRaises(DuplicateTaskError):
            self.m.add_task("study os")

    def test_same_title_allowed_after_original_is_done(self):
        t = self.m.add_task("Study OS")
        self.m.complete_task(t.id)
        self.assertEqual(self.m.add_task("Study OS").id, 2)

    # ---------- complete / delete / not found ----------
    def test_complete_task_sets_status_and_timestamp(self):
        t = self.m.add_task("Lab")
        done = self.m.complete_task(t.id)
        self.assertIs(done.status, Status.DONE)
        self.assertIsNotNone(done.completed_at)

    def test_completing_twice_is_rejected(self):
        t = self.m.add_task("Lab")
        self.m.complete_task(t.id)
        with self.assertRaises(InvalidTaskInputError):
            self.m.complete_task(t.id)

    def test_missing_id_raises_not_found(self):
        with self.assertRaises(TaskNotFoundError):
            self.m.complete_task(99)
        with self.assertRaises(TaskNotFoundError):
            self.m.delete_task(99)

    def test_delete_removes_task(self):
        t = self.m.add_task("Lab")
        self.m.delete_task(t.id)
        self.assertEqual(TaskManager(path=self.path).tasks, [])

    # ---------- edit ----------
    def test_edit_updates_fields(self):
        t = self.m.add_task("Lab")
        self.m.edit_task(t.id, title="Lab report", priority="high")
        self.assertEqual(self.m.get_task(t.id).title, "Lab report")
        self.assertEqual(self.m.get_task(t.id).priority.value, "high")

    def test_edit_with_bad_value_changes_nothing(self):
        t = self.m.add_task("Lab")
        with self.assertRaises(InvalidTaskInputError):
            self.m.edit_task(t.id, title="New title", priority="urgent")
        self.assertEqual(self.m.get_task(t.id).title, "Lab")   # not half-edited

    def test_edit_with_no_fields_rejected(self):
        t = self.m.add_task("Lab")
        with self.assertRaises(InvalidTaskInputError):
            self.m.edit_task(t.id)

    # ---------- search, sort, stats ----------
    def test_search_is_case_insensitive(self):
        self.m.add_task("Revise DBMS")
        self.m.add_task("Gym")
        self.assertEqual([t.title for t in self.m.search("dbms")], ["Revise DBMS"])

    def test_sort_by_priority_puts_high_first(self):
        self.m.add_task("Low one", priority="low")
        self.m.add_task("High one", priority="high")
        self.m.add_task("Mid one", priority="medium")
        order = [t.priority.value for t in self.m.list_tasks(sort_by="priority")]
        self.assertEqual(order, ["high", "medium", "low"])

    def test_invalid_sort_rejected(self):
        with self.assertRaises(InvalidTaskInputError):
            self.m.list_tasks(sort_by="alphabetical")

    def test_stats(self):
        a = self.m.add_task("A", due_date="2000-01-01")     # overdue
        self.m.add_task("B")
        self.m.complete_task(a.id)
        self.m.add_task("C", due_date="2000-01-01")         # overdue
        s = self.m.stats()
        self.assertEqual((s["total"], s["done"], s["pending"]), (3, 1, 2))
        self.assertEqual(s["overdue"], 1)                   # A is done, so only C counts
        self.assertEqual(s["completion_rate"], 33.3)

    # ---------- storage failure ----------
    def test_corrupted_json_raises_storage_error(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("{ this is not json")
        with self.assertRaises(StorageError):
            TaskManager(path=self.path)


if __name__ == "__main__":
    unittest.main()