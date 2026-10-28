"""Memories in a local SQLite file, searched with SQLite's built-in FTS5 index."""

import re
import sqlite3
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sado.domain.memory import Memory

_IN_MEMORY = ":memory:"
_WORD = re.compile(r"\w+")
# Tajik and Uzbek stack long suffixes onto a word, so only its start is matched:
# "kitoblarim" (my books) still finds "kitob" (book).
_STEM_LENGTH = 4
_MIN_WORD_LENGTH = 3


class SqliteMemoryStore:
    def __init__(self, path: Path | str) -> None:
        if str(path) != _IN_MEMORY:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        # FastAPI runs sync endpoints on a thread pool; one guarded connection is plenty for
        # a personal store.
        self._connection = sqlite3.connect(str(path), check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock, self._connection:
            self._connection.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS memories USING fts5("
                "id UNINDEXED, text, created_at UNINDEXED, "
                "tokenize = 'unicode61 remove_diacritics 2')"
            )

    def add(self, text: str) -> Memory:
        memory = Memory(id=uuid.uuid4().hex, text=text, created_at=datetime.now(UTC))
        with self._lock, self._connection:
            self._connection.execute(
                "INSERT INTO memories (id, text, created_at) VALUES (?, ?, ?)",
                (memory.id, memory.text, memory.created_at.isoformat()),
            )
        return memory

    def recent(self, limit: int) -> list[Memory]:
        return self._select(
            # The clock can repeat a timestamp, so insertion order breaks ties.
            "SELECT id, text, created_at FROM memories "
            "ORDER BY created_at DESC, rowid DESC LIMIT ?",
            (limit,),
        )

    def search(self, query: str, limit: int) -> list[Memory]:
        expression = _match_expression(query)
        if expression is None:
            return []
        return self._select(
            "SELECT id, text, created_at FROM memories WHERE memories MATCH ? "
            "ORDER BY rank LIMIT ?",
            (expression, limit),
        )

    def delete(self, memory_id: str) -> bool:
        with self._lock, self._connection:
            cursor = self._connection.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        return cursor.rowcount > 0

    def _select(self, sql: str, parameters: tuple[object, ...]) -> list[Memory]:
        with self._lock:
            rows = self._connection.execute(sql, parameters).fetchall()
        return [
            Memory(id=row[0], text=row[1], created_at=datetime.fromisoformat(row[2]))
            for row in rows
        ]


def _match_expression(query: str) -> str | None:
    stems = {
        word[:_STEM_LENGTH].lower()
        for word in _WORD.findall(query)
        if len(word) >= _MIN_WORD_LENGTH
    }
    if not stems:
        return None
    # Quoting every stem keeps FTS5 from reading the user's words as query syntax.
    return " OR ".join(f'"{stem}"*' for stem in sorted(stems))
