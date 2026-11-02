from collections.abc import Callable, Iterator, Sequence
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sado.application.desktop_tools import LIST_WINDOWS
from sado.application.phone_tools import PHONE_ALARM
from sado.domain.conversation import (
    Answer,
    Message,
    ModelTurn,
    ToolCall,
    ToolRequest,
    ToolSpec,
    ToolStep,
)
from sado.domain.errors import InvalidIdentityError
from sado.domain.identity import Person
from sado.domain.language import Language
from sado.main import create_app
from tests.fakes import fake_language_pack, fake_voice_catalog
from tests.test_desktop import _FakeDesktop

_TOKEN = "desk-secret"
_PEOPLE = {
    "owner-phone": Person("owner1", "Owner@Example.com"),
    "judge-phone": Person("judge1", "judge@example.com"),
}


class _Google:
    def verify(self, token: str) -> Person:
        if token not in _PEOPLE:
            raise InvalidIdentityError
        return _PEOPLE[token]


class _Model:
    def __init__(self, *turns: ModelTurn) -> None:
        self._turns = list(turns)
        self.tools: list[Sequence[ToolSpec]] = []

    def respond(
        self,
        instructions: str,
        conversation: Sequence[Message],
        tools: Sequence[ToolSpec],
        steps: Sequence[ToolStep],
    ) -> ModelTurn:
        self.tools.append(tools)
        return self._turns.pop(0) if self._turns else Answer("Salom")


_MakeApp = Callable[[_Model], FastAPI]


@pytest.fixture
def app_with(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[_MakeApp]:
    monkeypatch.setenv("SADO_PEOPLE_DIR", str(tmp_path))
    monkeypatch.setenv("SADO_OWNER_EMAILS", "owner@example.com")
    from sado.infrastructure.settings import get_settings  # noqa: PLC0415

    get_settings.cache_clear()
    yield lambda model: create_app(
        language_packs={Language.UZBEK: fake_language_pack(Language.UZBEK)[0]},
        voice_catalog=fake_voice_catalog(),
        reasoning_model=model,
        desktop=_FakeDesktop(),
        desktop_token=_TOKEN,
        identity=_Google(),
    )
    get_settings.cache_clear()


def _as(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _hello(client: TestClient) -> None:
    client.post(
        "/replies", json={"language": "uz", "messages": [{"speaker": "user", "text": "Salom"}]}
    )


def test_each_google_account_has_its_own_memory(app_with: _MakeApp) -> None:
    client = TestClient(app_with(_Model()))

    client.post("/memories", json={"text": "Judge likes tea."}, headers=_as("judge-phone"))
    client.post("/memories", json={"text": "Owner likes coffee."}, headers=_as("owner-phone"))

    def texts(headers: dict[str, str]) -> list[str]:
        return [m["text"] for m in client.get("/memories", headers=headers).json()]

    assert texts(_as("judge-phone")) == ["Judge likes tea."]
    assert texts(_as("owner-phone")) == ["Owner likes coffee."]
    assert texts({"X-Sado-Desktop-Token": _TOKEN}) == ["Owner likes coffee."]
    assert texts({}) == []


def test_only_the_owners_phone_may_drive_the_computer(app_with: _MakeApp) -> None:
    model = _Model()
    client = TestClient(app_with(model))

    _hello(TestClient(client.app, headers=_as("owner-phone")))
    _hello(TestClient(client.app, headers=_as("judge-phone")))

    assert LIST_WINDOWS.name in {tool.name for tool in model.tools[0]}
    assert LIST_WINDOWS.name not in {tool.name for tool in model.tools[1]}


def test_a_forged_sign_in_is_refused(app_with: _MakeApp) -> None:
    client = TestClient(app_with(_Model()))

    assert client.get("/memories", headers=_as("made-up")).status_code == 401


def test_the_computer_sends_phone_actions_to_the_owners_phone(app_with: _MakeApp) -> None:
    alarm = ToolRequest(calls=(ToolCall("c1", PHONE_ALARM.name, {"time": "06:30"}),))
    model = _Model(alarm, Answer("Telefoningizga yubordim."))
    app = app_with(model)
    computer = TestClient(app, headers={"X-Sado-Desktop-Token": _TOKEN})

    said = computer.post(
        "/replies",
        json={"language": "uz", "messages": [{"speaker": "user", "text": "6:30 ga budilnik"}]},
    ).json()

    assert said["phone_actions"] == []
    assert TestClient(app, headers=_as("judge-phone")).get("/phone/actions").status_code == 403
    owner_phone = TestClient(app, headers=_as("owner-phone"))
    assert owner_phone.get("/phone/actions").json() == [
        {"kind": "alarm", "details": {"hour": "6", "minute": "30", "label": ""}}
    ]
    assert owner_phone.get("/phone/actions").json() == []
