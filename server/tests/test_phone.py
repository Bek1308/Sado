from collections.abc import Sequence

import pytest
from fastapi.testclient import TestClient

from sado.application.converse import Converse
from sado.application.phone_tools import (
    PHONE_ALARM,
    PHONE_CALL,
    PHONE_FLASHLIGHT,
    PHONE_MESSAGE,
    PHONE_TIMER,
    PHONE_TOOL_NAMES,
    run_phone_tool,
)
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
from sado.domain.language import Language
from sado.domain.phone import PhoneAction
from sado.main import create_app
from tests.fakes import fake_language_pack, fake_voice_catalog


def _call(spec: ToolSpec, **arguments: object) -> ToolCall:
    return ToolCall("c1", spec.name, arguments)


@pytest.mark.parametrize(
    ("call", "expected"),
    [
        (_call(PHONE_CALL, contact=" Onam "), PhoneAction("call", {"contact": "Onam"})),
        (
            _call(PHONE_MESSAGE, contact="Aziz", text="Kechikaman"),
            PhoneAction("message", {"contact": "Aziz", "text": "Kechikaman", "app": "sms"}),
        ),
        (
            _call(PHONE_MESSAGE, contact="Aziz", text="Salom", app="WhatsApp"),
            PhoneAction("message", {"contact": "Aziz", "text": "Salom", "app": "whatsapp"}),
        ),
        (
            _call(PHONE_ALARM, time="6:05"),
            PhoneAction("alarm", {"hour": "6", "minute": "05", "label": ""}),
        ),
        (
            _call(PHONE_TIMER, minutes=0.5, label="Choy"),
            PhoneAction("timer", {"seconds": "30", "label": "Choy"}),
        ),
        (_call(PHONE_FLASHLIGHT, on=True), PhoneAction("flashlight", {"on": "true"})),
    ],
)
def test_phone_tools_become_actions_for_the_app(call: ToolCall, expected: PhoneAction) -> None:
    result, action = run_phone_tool(call)

    assert action == expected
    assert "Tell the user" in result.output


@pytest.mark.parametrize(
    "call",
    [
        _call(PHONE_CALL, contact="  "),
        _call(PHONE_MESSAGE, contact="Aziz", text="Salom", app="pigeon"),
        _call(PHONE_ALARM, time="25:00"),
        _call(PHONE_TIMER, minutes=0),
        _call(PHONE_TIMER, minutes=True),
        _call(PHONE_FLASHLIGHT, on="yes"),
    ],
)
def test_bad_arguments_do_nothing_and_say_why(call: ToolCall) -> None:
    result, action = run_phone_tool(call)

    assert action is None
    assert result.output.startswith("Nothing done:")


class _Model:
    def __init__(self, *turns: ModelTurn) -> None:
        self._turns = list(turns)
        self.instructions: list[str] = []
        self.tools: list[Sequence[ToolSpec]] = []

    def respond(
        self,
        instructions: str,
        conversation: Sequence[Message],
        tools: Sequence[ToolSpec],
        steps: Sequence[ToolStep],
    ) -> ModelTurn:
        self.instructions.append(instructions)
        self.tools.append(tools)
        return self._turns.pop(0)


def test_phone_tools_are_only_offered_to_a_phone() -> None:
    model = _Model(Answer("Salom"), Answer("Salom"))
    converse = Converse(model)
    hello = [Message(Speaker.USER, "salom")]

    converse.execute(hello, Language.UZBEK)
    converse.execute(hello, Language.UZBEK, phone=True)

    assert not PHONE_TOOL_NAMES & {tool.name for tool in model.tools[0]}
    assert {tool.name for tool in model.tools[1]} >= PHONE_TOOL_NAMES
    assert "on their phone" in model.instructions[1]


def test_a_phone_gets_the_action_with_the_reply() -> None:
    model = _Model(
        ToolRequest(calls=(ToolCall("c1", PHONE_CALL.name, {"contact": "Onam"}),)),
        Answer("Onangizga qo'ng'iroq qilyapman."),
    )
    pack, _ = fake_language_pack(Language.UZBEK)
    client = TestClient(
        create_app(
            language_packs={Language.UZBEK: pack},
            voice_catalog=fake_voice_catalog(),
            reasoning_model=model,
        )
    )

    response = client.post(
        "/replies",
        json={
            "language": "uz",
            "phone": True,
            "messages": [{"speaker": "user", "text": "Onamga qo'ng'iroq qil"}],
        },
    )

    assert response.status_code == 200
    assert response.json()["phone_actions"] == [{"kind": "call", "details": {"contact": "Onam"}}]
