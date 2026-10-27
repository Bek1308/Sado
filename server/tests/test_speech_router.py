from fastapi.testclient import TestClient

from sado.domain.language import Language
from sado.main import create_app
from tests.fakes import fake_language_pack


def _client() -> TestClient:
    pack, _ = fake_language_pack(Language.UZBEK)
    return TestClient(create_app(language_packs={Language.UZBEK: pack}))


def test_speak_returns_wav_audio() -> None:
    response = _client().post("/speech", json={"text": "salom", "language": "uz"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content == b"wav:SALOM"


def test_speak_rejects_blank_text() -> None:
    response = _client().post("/speech", json={"text": "   ", "language": "uz"})

    assert response.status_code == 422


def test_speak_rejects_unknown_language_code() -> None:
    response = _client().post("/speech", json={"text": "hello", "language": "xx"})

    assert response.status_code == 422


def test_speak_rejects_language_without_pack() -> None:
    response = _client().post("/speech", json={"text": "hello", "language": "en"})

    assert response.status_code == 422
