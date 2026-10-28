from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Reminder:
    """Something Sado must tell the user at a later time, in the user's words."""

    id: str
    text: str
    due_at: datetime
    created_at: datetime


class ReminderStore(Protocol):
    def add(self, text: str, due_at: datetime) -> Reminder: ...

    def upcoming(self, limit: int) -> list[Reminder]:
        """Soonest first."""
        ...

    def due_before(self, moment: datetime, limit: int) -> list[Reminder]:
        """Undelivered reminders due at or before `moment`, soonest first."""
        ...

    def mark_delivered(self, reminder_ids: Sequence[str], moment: datetime) -> None:
        """Sado has told the user about these, so they stop coming back."""
        ...

    def delete(self, reminder_id: str) -> bool:
        """False when no reminder has that id."""
        ...
