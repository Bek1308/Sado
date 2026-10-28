from datetime import UTC, datetime

from sado.application.persona import persona_instructions
from sado.domain.language import Language


def test_names_the_current_time_for_planning() -> None:
    now = datetime(2026, 10, 28, 14, 30, tzinfo=UTC)

    instructions = persona_instructions(Language.UZBEK, now=now)

    assert "The current time is Wednesday, 28 October 2026 at 14:30 UTC." in instructions


def test_lists_due_reminders_for_the_model() -> None:
    instructions = persona_instructions(
        Language.TAJIK, due_reminders=["Call mother (28 Oct, 09:00 UTC)"]
    )

    assert "now due" in instructions
    assert "- Call mother (28 Oct, 09:00 UTC)" in instructions
