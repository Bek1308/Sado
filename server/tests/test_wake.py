import threading

from fastapi.testclient import TestClient

from sado.application.wake import WakeSignal
from sado.domain.conversation import Answer
from sado.domain.language import Language
from sado.main import create_app
from tests.fakes import fake_language_pack, fake_voice_catalog
from tests.test_desktop import _TOKEN, _FakeDesktop, _Model


def test_a_waiting_app_hears_the_call_at_once() -> None:
    signal = WakeSignal()
    threading.Timer(0.05, signal.ring).start()

    assert signal.wait(after=0, timeout=5) == 1


def test_nothing_called_means_the_wait_runs_out() -> None:
    assert WakeSignal().wait(after=0, timeout=0.01) == 0


def test_only_the_computers_app_may_listen_for_calls() -> None:
    app = create_app(
        language_packs={Language.UZBEK: fake_language_pack(Language.UZBEK)[0]},
        voice_catalog=fake_voice_catalog(),
        reasoning_model=_Model(Answer("Salom")),
        desktop=_FakeDesktop(),
        desktop_token=_TOKEN,
    )
    app.state.wake.ring()

    computer = TestClient(app, headers={"X-Sado-Desktop-Token": _TOKEN})

    assert computer.get("/desktop/wake").json() == {"count": 1}
    assert TestClient(app).get("/desktop/wake").status_code == 403
