from datetime import UTC, datetime

import pytest

from sado.application.reminders import Reminders
from sado.domain.errors import (
    EmptyReminderError,
    InvalidReminderDueError,
    UnknownReminderError,
)
from sado.infrastructure.memory.sqlite_reminders import SqliteReminderStore


def _reminders() -> Reminders:
    return Reminders(SqliteReminderStore(":memory:"))


def test_saves_and_lists_soonest_first() -> None:
    reminders = _reminders()
    reminders.remind("Later", "2026-10-30T18:00:00+00:00")
    reminders.remind("Sooner", "2026-10-29T09:00:00+00:00")

    assert [reminder.text for reminder in reminders.saved()] == ["Sooner", "Later"]


def test_assumes_utc_for_a_due_without_timezone() -> None:
    reminder = _reminders().remind("Call mother", "2026-10-29T18:00:00")

    assert reminder.due_at == datetime(2026, 10, 29, 18, 0, tzinfo=UTC)


def test_normalizes_other_timezones_to_utc() -> None:
    reminder = _reminders().remind("Call mother", "2026-10-29T18:00:00+02:00")

    assert reminder.due_at == datetime(2026, 10, 29, 16, 0, tzinfo=UTC)


def test_rejects_an_empty_reminder() -> None:
    with pytest.raises(EmptyReminderError):
        _reminders().remind("   ", "2026-10-29T18:00:00+00:00")


def test_rejects_a_due_that_is_not_a_date() -> None:
    with pytest.raises(InvalidReminderDueError):
        _reminders().remind("Call mother", "tomorrow-ish")


def test_reports_only_what_is_already_due() -> None:
    reminders = _reminders()
    reminders.remind("Overdue", "2000-01-01T09:00:00+00:00")
    reminders.remind("Later", "2100-01-01T09:00:00+00:00")

    due = reminders.due(datetime(2026, 10, 28, 14, 30, tzinfo=UTC))

    assert [reminder.text for reminder in due] == ["Overdue"]


def test_forgets_a_reminder_by_id() -> None:
    reminders = _reminders()
    reminder = reminders.remind("Call mother", "2026-10-29T18:00:00+00:00")

    reminders.forget(reminder.id)

    assert reminders.saved() == []


def test_forgetting_an_unknown_id_fails() -> None:
    with pytest.raises(UnknownReminderError):
        _reminders().forget("nope")
