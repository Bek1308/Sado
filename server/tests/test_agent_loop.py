from collections.abc import Sequence

import pytest

from sado.application.converse import REMEMBER, Converse
from sado.application.memories import Memories
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
from sado.infrastructure.memory.sqlite_store import SqliteMemoryStore

_QUESTION = [Message(Speaker.USER, "Qizim Malika 12-mayda tug'ilgan, eslab qol")]


class _ScriptedModel:
    """Plays back turns in order and records what it was shown."""

    def __init__(self, *turns: ModelTurn) -> None:
        self._turns = list(turns)
        self.tools: list[Sequence[ToolSpec]] = []
        self.steps: list[list[ToolStep]] = []

    def respond(
        self,
        instructions: str,
        conversation: Sequence[Message],
        tools: Sequence[ToolSpec],
        steps: Sequence[ToolStep],
    ) -> ModelTurn:
        self.tools.append(tools)
        self.steps.append(list(steps))
        return self._turns.pop(0)


def _memories() -> Memories:
    return Memories(SqliteMemoryStore(":memory:"))


def _remember(fact: object, call_id: str = "call_1") -> ToolRequest:
    return ToolRequest(calls=(ToolCall(call_id, REMEMBER.name, {"fact": fact}),))


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
