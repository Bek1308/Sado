from fastapi.testclient import TestClient

from sado.domain.language import Language
from sado.main import create_app
from tests.fakes import fake_language_pack, fake_voice_catalog


def _client() -> TestClient:
    pack, _ = fake_language_pack(Language.TAJIK)
    return TestClient(
        create_app(language_packs={Language.TAJIK: pack}, voice_catalog=fake_voice_catalog())
    )


def test_transcribes_an_uploaded_recording() -> None:
    response = _client().post(
        "/transcriptions",
        files={"audio": ("speech.webm", "салом".encode(), "audio/webm")},
        data={"language": "tg"},
    )

    assert response.status_code == 200
    assert response.json() == {"text": "салом", "language": "tg"}


def test_rejects_an_empty_recording() -> None:
    response = _client().post(
        "/transcriptions",
        files={"audio": ("speech.webm", b"", "audio/webm")},
        data={"language": "tg"},
    )

    assert response.status_code == 422


def test_requires_a_known_language() -> None:
    response = _client().post(
        "/transcriptions",
        files={"audio": ("speech.webm", b"x", "audio/webm")},
        data={"language": "xx"},
    )

    assert response.status_code == 422
