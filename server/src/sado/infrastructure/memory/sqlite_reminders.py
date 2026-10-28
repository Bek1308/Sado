"""Reminders in a local SQLite file, ordered by when they are due."""

import sqlite3
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sado.domain.reminder import Reminder

_IN_MEMORY = ":memory:"


class SqliteReminderStore:
    def __init__(self, path: Path | str) -> None:
        if str(path) != _IN_MEMORY:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        # FastAPI runs sync endpoints on a thread pool; one guarded connection is plenty for
        # a personal store.
        self._connection = sqlite3.connect(str(path), check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock, self._connection:
            self._connection.execute(
                "CREATE TABLE IF NOT EXISTS reminders "
                "(id TEXT PRIMARY KEY, text TEXT, due_at TEXT, created_at TEXT)"
            )

    def add(self, text: str, due_at: datetime) -> Reminder:
        reminder = Reminder(
            id=uuid.uuid4().hex, text=text, due_at=due_at, created_at=datetime.now(UTC)
        )
        with self._lock, self._connection:
            self._connection.execute(
                "INSERT INTO reminders (id, text, due_at, created_at) VALUES (?, ?, ?, ?)",
                (
                    reminder.id,
                    reminder.text,
                    reminder.due_at.isoformat(),
                    reminder.created_at.isoformat(),
                ),
            )
        return reminder

    def upcoming(self, limit: int) -> list[Reminder]:
        return self._select(
            "SELECT id, text, due_at, created_at FROM reminders "
            "ORDER BY due_at ASC, rowid ASC LIMIT ?",
            (limit,),
        )

    def due_before(self, moment: datetime, limit: int) -> list[Reminder]:
        return self._select(
            "SELECT id, text, due_at, created_at FROM reminders WHERE due_at <= ? "
            "ORDER BY due_at ASC, rowid ASC LIMIT ?",
            (moment.isoformat(), limit),
        )

    def delete(self, reminder_id: str) -> bool:
        with self._lock, self._connection:
            cursor = self._connection.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        return cursor.rowcount > 0

    def _select(self, sql: str, parameters: tuple[object, ...]) -> list[Reminder]:
        with self._lock:
            rows = self._connection.execute(sql, parameters).fetchall()
        return [
            Reminder(
                id=row[0],
                text=row[1],
                due_at=datetime.fromisoformat(row[2]),
                created_at=datetime.fromisoformat(row[3]),
            )
            for row in rows
        ]
