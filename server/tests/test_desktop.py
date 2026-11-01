from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from sado.application.converse import Converse
from sado.application.desktop_tools import (
    CLOSE_WINDOW,
    LIST_WINDOWS,
    OPEN,
    READ_WINDOW,
    RUN_COMMAND,
    TYPE_INTO_WINDOW,
    DesktopTools,
    PendingActions,
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
from sado.domain.desktop import WindowInfo
from sado.domain.errors import UnknownActionError
from sado.domain.language import Language
from sado.main import create_app
from tests.fakes import fake_language_pack, fake_voice_catalog

_TERMINAL = WindowInfo(id=11, title="Muse Code - Sado", app="WindowsTerminal")
_BROWSER = WindowInfo(id=22, title="YouTube - Google Chrome", app="chrome")


@dataclass
class _FakeDesktop:
    typed: list[tuple[int, str]] = field(default_factory=list)
    closed: list[int] = field(default_factory=list)
    opened: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)

    def windows(self) -> list[WindowInfo]:
        return [_TERMINAL, _BROWSER]

    def read(self, window_id: int, max_chars: int) -> str:
        return "Agent: I added the tests. All 12 pass." if window_id == _TERMINAL.id else ""

    def focus(self, window_id: int) -> None:
        pass

    def type_text(self, window_id: int, text: str, submit: bool) -> None:
        self.typed.append((window_id, text))

    def close(self, window_id: int) -> None:
        self.closed.append(window_id)

    def open(self, target: str) -> None:
        self.opened.append(target)

    def run_command(self, command: str) -> str:
        self.commands.append(command)
        return "ok"


def _call(spec: ToolSpec, **arguments: object) -> ToolCall:
    return ToolCall("c1", spec.name, arguments)


def _tools() -> tuple[DesktopTools, _FakeDesktop, PendingActions]:
    desktop = _FakeDesktop()
    pending = PendingActions()
    return DesktopTools(desktop, pending), desktop, pending


def test_looking_needs_no_permission() -> None:
    tools, desktop, _ = _tools()

    listed, waiting = tools.run(_call(LIST_WINDOWS))
    read, _ = tools.run(_call(READ_WINDOW, window="muse code"))
    tools.run(_call(OPEN, target="https://youtube.com"))

    assert waiting is None
    assert "id 11: Muse Code - Sado (WindowsTerminal)" in listed.output
    assert read.output == "Agent: I added the tests. All 12 pass."
    assert desktop.opened == ["https://youtube.com"]


@pytest.mark.parametrize(
    "call",
    [
        _call(TYPE_INTO_WINDOW, window="Muse", text="write the README"),
        _call(CLOSE_WINDOW, window="chrome"),
        _call(RUN_COMMAND, command="Get-Date"),
    ],
)
def test_changing_things_only_waits_for_a_yes(call: ToolCall) -> None:
    tools, desktop, _ = _tools()

    result, waiting = tools.run(call)

    assert waiting is not None
    assert "Do not say it is done" in result.output
    assert desktop.typed == desktop.closed == desktop.commands == []


def test_a_confirmed_action_runs_once() -> None:
    tools, desktop, pending = _tools()
    _, waiting = tools.run(_call(TYPE_INTO_WINDOW, window="Muse", text="write the README"))
    assert waiting is not None

    assert pending.take(waiting.id).run() == "Typed into 'Muse Code - Sado'."
    assert desktop.typed == [(11, "write the README")]
    with pytest.raises(UnknownActionError):
        pending.take(waiting.id)


def test_an_old_action_can_no_longer_be_confirmed() -> None:
    pending = PendingActions()
    action = pending.add("Run: Get-Date", lambda: "ok")
    stale = datetime.now(UTC) - timedelta(minutes=10)
    pending._actions[action.id] = action.__class__(action.id, action.description, action.run, stale)

    with pytest.raises(UnknownActionError):
        pending.take(action.id)


def test_unclear_windows_are_explained_to_the_model() -> None:
    tools, _, _ = _tools()

    nothing, _ = tools.run(_call(READ_WINDOW, window="Telegram"))
    several, _ = tools.run(_call(READ_WINDOW, window="-"))

    assert "no window matches 'Telegram'" in nothing.output
    assert "several windows match '-'" in several.output


class _Model:
    def __init__(self, *turns: ModelTurn) -> None:
        self._turns = list(turns)
        self.instructions: list[str] = []

    def respond(
        self,
        instructions: str,
        conversation: Sequence[Message],
        tools: Sequence[ToolSpec],
        steps: Sequence[ToolStep],
    ) -> ModelTurn:
        self.instructions.append(instructions)
        return self._turns.pop(0)


def _ask_to_type() -> ToolRequest:
    return ToolRequest(
        calls=(
            ToolCall("c1", TYPE_INTO_WINDOW.name, {"window": "Muse", "text": "write the README"}),
        )
    )


def test_sado_asks_before_typing_and_reports_after_the_yes() -> None:
    desktop = _FakeDesktop()
    model = _Model(
        _ask_to_type(),
        Answer("Agentga README yozishni aytaymi?"),
        Answer("Bo'ldi, agent ishga tushdi."),
    )
    pack, _ = fake_language_pack(Language.UZBEK)
    client = TestClient(
        create_app(
            language_packs={Language.UZBEK: pack},
            voice_catalog=fake_voice_catalog(),
            reasoning_model=model,
            desktop=desktop,
        )
    )
    ask = {"speaker": "user", "text": "Agentga README yozishni ayt"}

    first = client.post("/replies", json={"language": "uz", "messages": [ask]}).json()

    assert first["reply"] == "Agentga README yozishni aytaymi?"
    assert (
        first["pending_action"]["description"] == "Type into 'Muse Code - Sado': write the README"
    )
    assert desktop.typed == []

    conversation = [
        ask,
        {"speaker": "sado", "text": first["reply"]},
        {"speaker": "user", "text": "Ha"},
    ]
    action_id = first["pending_action"]["id"]
    done = client.post(
        f"/actions/{action_id}/confirm", json={"language": "uz", "messages": conversation}
    )

    assert done.status_code == 200
    assert done.json()["reply"] == "Bo'ldi, agent ishga tushdi."
    assert desktop.typed == [(11, "write the README")]
    assert "Typed into 'Muse Code - Sado'." in model.instructions[-1]
    again = client.post(
        f"/actions/{action_id}/confirm", json={"language": "uz", "messages": conversation}
    )
    assert again.status_code == 404


def test_a_cancelled_action_never_runs() -> None:
    desktop = _FakeDesktop()
    pack, _ = fake_language_pack(Language.UZBEK)
    client = TestClient(
        create_app(
            language_packs={Language.UZBEK: pack},
            voice_catalog=fake_voice_catalog(),
            reasoning_model=_Model(_ask_to_type(), Answer("Yozaymi?")),
            desktop=desktop,
        )
    )
    first = client.post(
        "/replies",
        json={"language": "uz", "messages": [{"speaker": "user", "text": "Yoz"}]},
    ).json()

    assert client.post(f"/actions/{first['pending_action']['id']}/cancel").status_code == 204
    assert desktop.typed == []


def test_without_desktop_control_sado_has_no_hands() -> None:
    model = _Model(Answer("Salom"))
    seen: list[Sequence[ToolSpec]] = []
    original = model.respond

    def spy(
        instructions: str,
        conversation: Sequence[Message],
        tools: Sequence[ToolSpec],
        steps: Sequence[ToolStep],
    ) -> ModelTurn:
        seen.append(tools)
        return original(instructions, conversation, tools, steps)

    model.respond = spy  # type: ignore[method-assign]

    Converse(model).execute([Message(Speaker.USER, "salom")], Language.UZBEK)

    assert all(tool.name != LIST_WINDOWS.name for tool in seen[0])
