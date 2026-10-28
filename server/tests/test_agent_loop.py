from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

import pytest

from sado.application.converse import REMEMBER, REMIND, Converse
from sado.application.memories import Memories
from sado.application.reminders import Reminders
from sado.domain.conversation import (
    Answer,
    Message,
    ModelTurn,
    Speaker,
    ToolCall,
    ToolRequest,
    ToolSpec,
    ToolStep,
)
from sado.domain.errors import ReasoningUnavailableError
from sado.domain.language import Language
from sado.domain.mode import Mode
from sado.infrastructure.memory.sqlite_reminders import SqliteReminderStore
from sado.infrastructure.memory.sqlite_store import SqliteMemoryStore

_QUESTION = [Message(Speaker.USER, "Qizim Malika 12-mayda tug'ilgan, eslab qol")]


class _ScriptedModel:
    """Plays back turns in order and records what it was shown."""

    def __init__(self, *turns: ModelTurn) -> None:
        self._turns = list(turns)
        self.instructions: list[str] = []
        self.tools: list[Sequence[ToolSpec]] = []
        self.steps: list[list[ToolStep]] = []

    def respond(
        self,
        instructions: str,
        conversation: Sequence[Message],
        tools: Sequence[ToolSpec],
        steps: Sequence[ToolStep],
    ) -> ModelTurn:
        self.instructions.append(instructions)
        self.tools.append(tools)
        self.steps.append(list(steps))
        return self._turns.pop(0)


def _memories() -> Memories:
    return Memories(SqliteMemoryStore(":memory:"))


def _reminders() -> Reminders:
    return Reminders(SqliteReminderStore(":memory:"))


def _remember(fact: object, call_id: str = "call_1") -> ToolRequest:
    return ToolRequest(calls=(ToolCall(call_id, REMEMBER.name, {"fact": fact}),))


def _remind(text: object, due: object, call_id: str = "call_1") -> ToolRequest:
    return ToolRequest(calls=(ToolCall(call_id, REMIND.name, {"text": text, "due": due}),))


def test_saves_what_the_model_asks_to_remember_and_then_answers() -> None:
    memories = _memories()
    model = _ScriptedModel(_remember("Qizi Malika 12-mayda tug'ilgan"), Answer("Eslab qoldim!"))

    reply = Converse(model, memories).execute(_QUESTION, Language.UZBEK)

    assert reply.text == "Eslab qoldim!"
    assert reply.remembered == ("Qizi Malika 12-mayda tug'ilgan",)
    assert [memory.text for memory in memories.saved()] == ["Qizi Malika 12-mayda tug'ilgan"]
    assert model.tools[0] == [REMEMBER]
    assert model.steps[1][0].results[0].output == "Saved."


def test_tells_the_model_when_its_arguments_are_unusable() -> None:
    memories = _memories()
    model = _ScriptedModel(
        ToolRequest(
            calls=(
                ToolCall("a", REMEMBER.name, {"fact": 42}),
                ToolCall("b", REMEMBER.name, {"fact": "   "}),
                ToolCall("c", "send_email", {}),
            )
        ),
        Answer("Kechirasiz."),
    )

    reply = Converse(model, memories).execute(_QUESTION, Language.UZBEK)

    outputs = [result.output for result in model.steps[1][0].results]
    assert outputs == [
        "Nothing saved: 'fact' must be text.",
        "Nothing saved: There is nothing to remember.",
        "Unknown tool 'send_email'.",
    ]
    assert reply.remembered == ()
    assert memories.saved() == []


def test_offers_no_tools_without_a_memory() -> None:
    model = _ScriptedModel(Answer("Salom!"))

    Converse(model).execute(_QUESTION, Language.UZBEK)

    assert model.tools[0] == []


def test_gives_up_when_the_model_never_stops_calling_tools() -> None:
    model = _ScriptedModel(*[_remember("Bir narsa", f"call_{i}") for i in range(10)])

    with pytest.raises(ReasoningUnavailableError):
        Converse(model, _memories()).execute(_QUESTION, Language.UZBEK)


def test_sets_what_the_model_asks_to_remind_and_then_answers() -> None:
    reminders = _reminders()
    model = _ScriptedModel(_remind("Call mother", "2026-10-29T18:00:00+00:00"), Answer("Done!"))

    reply = Converse(model, None, reminders).execute(_QUESTION, Language.UZBEK)

    assert reply.text == "Done!"
    assert reply.reminded == ("Call mother (29 Oct, 18:00)",)
    assert [reminder.text for reminder in reminders.saved()] == ["Call mother"]
    assert model.tools[0] == [REMIND]
    assert model.steps[1][0].results[0].output == "Set."


def test_tells_the_model_when_its_reminder_is_unusable() -> None:
    model = _ScriptedModel(
        ToolRequest(
            calls=(
                ToolCall("a", REMIND.name, {"text": 42, "due": "2026-10-29T18:00:00+00:00"}),
                ToolCall("b", REMIND.name, {"text": "   ", "due": "2026-10-29T18:00:00+00:00"}),
                ToolCall("c", REMIND.name, {"text": "Call", "due": "tomorrow-ish"}),
            )
        ),
        Answer("Kechirasiz."),
    )

    reply = Converse(model, None, _reminders()).execute(_QUESTION, Language.UZBEK)

    outputs = [result.output for result in model.steps[1][0].results]
    assert outputs == [
        "Nothing set: 'text' and 'due' must be text.",
        "Nothing set: There is nothing to remind about.",
        "Nothing set: Cannot understand the due time 'tomorrow-ish'.",
    ]
    assert reply.reminded == ()


def test_offers_both_tools_when_both_stores_exist() -> None:
    model = _ScriptedModel(Answer("Salom!"))

    Converse(model, _memories(), _reminders()).execute(_QUESTION, Language.UZBEK)

    assert model.tools[0] == [REMEMBER, REMIND]


def test_speaks_in_the_requested_mode() -> None:
    model = _ScriptedModel(Answer("Done."))

    Converse(model).execute(_QUESTION, Language.UZBEK, Mode.WORK)

    assert "Work mode" in model.instructions[0]


def test_mentions_due_reminders_in_the_instructions() -> None:
    reminders = _reminders()
    reminders.remind("Call mother", "2000-01-01T09:00:00+00:00")
    reminders.remind("Far future", "2100-01-01T09:00:00+00:00")
    model = _ScriptedModel(Answer("Salom!"))

    Converse(model, None, reminders).execute(_QUESTION, Language.UZBEK)

    assert "Call mother (01 Jan, 09:00)" in model.instructions[0]
    assert "Far future" not in model.instructions[0]


def test_reads_reminder_times_on_the_users_clock() -> None:
    reminders = _reminders()
    model = _ScriptedModel(_remind("Bankka borish", "2026-10-30T09:00:00"), Answer("Bo'ldi!"))

    reply = Converse(model, None, reminders).execute(
        _QUESTION, Language.UZBEK, utc_offset=timedelta(hours=5)
    )

    assert reply.reminded == ("Bankka borish (30 Oct, 09:00)",)
    saved = reminders.saved()[0]
    assert saved.due_at == datetime(2026, 10, 30, 4, 0, tzinfo=UTC)
    assert "(UTC+05:00)" in model.instructions[0]
