from fastapi.testclient import TestClient

from sado.domain.language import Language
from sado.main import create_app
from tests.fakes import fake_language_pack, fake_voice_catalog


def _client() -> TestClient:
    pack, _ = fake_language_pack(Language.UZBEK)
    return TestClient(
        create_app(language_packs={Language.UZBEK: pack}, voice_catalog=fake_voice_catalog())
    )


def test_speak_returns_wav_audio_in_the_default_voice() -> None:
    response = _client().post("/speech", json={"text": "salom", "language": "uz"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content == b"wav:sado:SALOM"


def test_speak_uses_the_requested_voice() -> None:
    response = _client().post("/speech", json={"text": "salom", "language": "uz", "voice": "opa"})

    assert response.content == b"wav:opa:SALOM"


def test_speak_rejects_unknown_mood() -> None:
    response = _client().post("/speech", json={"text": "salom", "language": "uz", "mood": "angry"})

    assert response.status_code == 422


def test_speak_rejects_unknown_voice() -> None:
    response = _client().post("/speech", json={"text": "salom", "language": "uz", "voice": "robot"})

    assert response.status_code == 422
    assert "robot" in response.json()["detail"]


def test_speak_rejects_blank_text() -> None:
    response = _client().post("/speech", json={"text": "   ", "language": "uz"})

    assert response.status_code == 422


def test_speak_rejects_unknown_language_code() -> None:
    response = _client().post("/speech", json={"text": "hello", "language": "xx"})

    assert response.status_code == 422


def test_speak_rejects_language_without_pack() -> None:
    response = _client().post("/speech", json={"text": "hello", "language": "en"})

    assert response.status_code == 422


def test_lists_voices_and_marks_the_default() -> None:
    response = _client().get("/voices")

    assert response.json() == [
        {"id": "sado", "name": "Sado", "description": "", "is_default": True},
        {"id": "opa", "name": "Opa", "description": "", "is_default": False},
    ]
