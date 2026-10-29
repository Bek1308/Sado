"""The user's lists in the same local SQLite file as memories and reminders."""

import sqlite3
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sado.domain.lists import ListItem

_IN_MEMORY = ":memory:"


class SqliteListStore:
    def __init__(self, path: Path | str) -> None:
        if str(path) != _IN_MEMORY:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(path), check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock, self._connection:
            self._connection.execute(
                "CREATE TABLE IF NOT EXISTS list_items "
                "(id TEXT PRIMARY KEY, list_name TEXT, text TEXT, created_at TEXT)"
            )

    def add(self, list_name: str, text: str) -> ListItem:
        item = ListItem(id=uuid.uuid4().hex, list_name=list_name, text=text)
        with self._lock, self._connection:
            self._connection.execute(
                "INSERT INTO list_items (id, list_name, text, created_at) VALUES (?, ?, ?, ?)",
                (item.id, item.list_name, item.text, datetime.now(UTC).isoformat()),
            )
        return item

    def items(self, list_name: str) -> list[ListItem]:
        return self._select(
            "SELECT id, list_name, text FROM list_items WHERE list_name = ? ORDER BY rowid",
            (list_name,),
        )

    def everything(self) -> list[ListItem]:
        return self._select(
            "SELECT id, list_name, text FROM list_items ORDER BY list_name, rowid", ()
        )

    def remove(self, item_id: str) -> bool:
        with self._lock, self._connection:
            cursor = self._connection.execute("DELETE FROM list_items WHERE id = ?", (item_id,))
        return cursor.rowcount > 0

    def _select(self, sql: str, parameters: tuple[object, ...]) -> list[ListItem]:
        with self._lock:
            rows = self._connection.execute(sql, parameters).fetchall()
        return [ListItem(id=row[0], list_name=row[1], text=row[2]) for row in rows]
