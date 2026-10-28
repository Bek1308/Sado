from datetime import UTC, datetime

from sado.domain.errors import (
    EmptyReminderError,
    InvalidReminderDueError,
    UnknownReminderError,
)
from sado.domain.reminder import Reminder, ReminderStore


class Reminders:
    """What Sado promised to tell the user later."""

    _LIST_LIMIT = 500
    _DUE_LIMIT = 5

    def __init__(self, store: ReminderStore) -> None:
        self._store = store

    def remind(self, text: str, due: str) -> Reminder:
        cleaned = " ".join(text.split())
        if not cleaned:
            raise EmptyReminderError
        try:
            due_at = datetime.fromisoformat(due)
        except ValueError:
            raise InvalidReminderDueError(due) from None
        if due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=UTC)
        # One zone keeps the store's text comparison chronological.
        return self._store.add(cleaned, due_at.astimezone(UTC))

    def saved(self) -> list[Reminder]:
        return self._store.upcoming(self._LIST_LIMIT)

    def due(self, now: datetime) -> list[Reminder]:
        return self._store.due_before(now, self._DUE_LIMIT)

    def forget(self, reminder_id: str) -> None:
        if not self._store.delete(reminder_id):
            raise UnknownReminderError(reminder_id)
