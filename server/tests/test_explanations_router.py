from fastapi.testclient import TestClient

from sado.domain.language import Language
from sado.main import create_app
from tests.fakes import CannedExplainer, fake_language_pack, fake_voice_catalog
from tests.test_readers import sample_pdf_bytes


def _client() -> TestClient:
    pack, _ = fake_language_pack(Language.TAJIK)
    return TestClient(
        create_app(
            language_packs={Language.TAJIK: pack},
            voice_catalog=fake_voice_catalog(),
            document_explainer=CannedExplainer(),
        )
    )


def test_explains_an_uploaded_photo() -> None:
    response = _client().post(
        "/explanations",
        files={"file": ("notice.jpg", b"paper", "image/jpeg")},
        data={"language": "tg"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "explanation": "This is a work permit notice.",
        "language": "tg",
    }


def test_explains_an_uploaded_text_file() -> None:
    response = _client().post(
        "/explanations",
        files={"file": ("notice.txt", b"Permit 42", "text/plain")},
        data={"language": "tg"},
    )

    assert response.status_code == 200
    assert response.json()["language"] == "tg"


def test_explains_an_uploaded_pdf() -> None:
    response = _client().post(
        "/explanations",
        files={"file": ("notice.pdf", sample_pdf_bytes(), "application/pdf")},
        data={"language": "tg"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "explanation": "This is a work permit notice.",
        "language": "tg",
    }


def test_explains_an_uploaded_recording() -> None:
    response = _client().post(
        "/explanations",
        files={"file": ("voice.webm", b"salom", "audio/webm")},
        data={"language": "tg"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "explanation": "This is a work permit notice.",
        "language": "tg",
    }


def test_rejects_an_empty_upload() -> None:
    response = _client().post(
        "/explanations",
        files={"file": ("notice.jpg", b"", "image/jpeg")},
        data={"language": "tg"},
    )

    assert response.status_code == 422


def test_rejects_a_file_type_sado_cannot_read() -> None:
    response = _client().post(
        "/explanations",
        files={"file": ("archive.zip", b"archived", "application/zip")},
        data={"language": "tg"},
    )

    assert response.status_code == 422


def test_requires_a_known_language() -> None:
    response = _client().post(
        "/explanations",
        files={"file": ("notice.jpg", b"paper", "image/jpeg")},
        data={"language": "xx"},
    )

    assert response.status_code == 422
