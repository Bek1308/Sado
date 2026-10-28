from collections.abc import Sequence

import pytest
from fastapi.testclient import TestClient

from sado.application.converse import Converse
from sado.domain.conversation import Answer, Message, ModelTurn, Speaker, ToolSpec, ToolStep
from sado.domain.errors import NothingToAnswerError
from sado.domain.language import Language
from sado.main import create_app
from tests.fakes import fake_language_pack, fake_voice_catalog


class _ParrotModel:
    def __init__(self) -> None:
        self.instructions: list[str] = []

    def respond(
        self,
        instructions: str,
        conversation: Sequence[Message],
        tools: Sequence[ToolSpec],
        steps: Sequence[ToolStep],
    ) -> ModelTurn:
        self.instructions.append(instructions)
        return Answer(f"  You said: {conversation[-1].text}  ")


def test_answers_the_last_user_message_in_the_requested_language() -> None:
    model = _ParrotModel()

    reply = Converse(model).execute([Message(Speaker.USER, "salom")], Language.UZBEK)

    assert reply.text == "You said: salom"
    assert "Uzbek, written in the Latin alphabet" in model.instructions[0]


@pytest.mark.parametrize(
    "conversation",
    [
        [],
        [Message(Speaker.USER, "   ")],
        [Message(Speaker.USER, "salom"), Message(Speaker.SADO, "Salom!")],
    ],
)
def test_needs_a_user_message_to_answer(conversation: list[Message]) -> None:
    with pytest.raises(NothingToAnswerError):
        Converse(_ParrotModel()).execute(conversation, Language.UZBEK)


def test_replies_endpoint_returns_sado_answer() -> None:
    pack, _ = fake_language_pack(Language.TAJIK)
    client = TestClient(
        create_app(
            language_packs={Language.TAJIK: pack},
            voice_catalog=fake_voice_catalog(),
            reasoning_model=_ParrotModel(),
        )
    )

    response = client.post(
        "/replies",
        json={"language": "tg", "messages": [{"speaker": "user", "text": "салом"}]},
    )

    assert response.status_code == 200
    assert response.json() == {
        "reply": "You said: салом",
        "remembered": [],
        "reminded": [],
    }
