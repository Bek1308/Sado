from datetime import UTC, datetime, timedelta, timezone

from sado.application.persona import persona_instructions
from sado.domain.language import Language
from sado.domain.mode import Mode


def test_names_the_current_time_for_planning() -> None:
    now = datetime(2026, 10, 28, 14, 30, tzinfo=UTC)

    instructions = persona_instructions(Language.UZBEK, now=now)

    assert "The user's local time is Wednesday, 28 October 2026 at 14:30 (UTC+00:00)." in (
        instructions
    )


def test_names_the_time_on_the_users_own_clock() -> None:
    dushanbe = timezone(timedelta(hours=5))
    now = datetime(2026, 10, 29, 0, 35, tzinfo=dushanbe)

    instructions = persona_instructions(Language.UZBEK, now=now)

    assert "Thursday, 29 October 2026 at 00:35 (UTC+05:00)" in instructions


def test_lists_due_reminders_for_the_model() -> None:
    instructions = persona_instructions(
        Language.TAJIK, due_reminders=["Call mother (28 Oct, 09:00)"]
    )

    assert "now due" in instructions
    assert "- Call mother (28 Oct, 09:00)" in instructions


def test_names_the_conversation_mode() -> None:
    assert "Work mode" in persona_instructions(Language.ENGLISH, mode=Mode.WORK)
    assert "On-the-go mode" in persona_instructions(Language.ENGLISH, mode=Mode.ON_THE_GO)
    assert "Home mode" in persona_instructions(Language.ENGLISH, mode=Mode.HOME)


def test_personal_mode_is_the_default() -> None:
    assert "Personal mode" in persona_instructions(Language.ENGLISH)
