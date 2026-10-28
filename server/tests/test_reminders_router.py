from fastapi.testclient import TestClient

from sado.domain.language import Language
from sado.infrastructure.memory.sqlite_reminders import SqliteReminderStore
from sado.main import create_app
from tests.fakes import fake_language_pack, fake_voice_catalog


def _client() -> TestClient:
    pack, _ = fake_language_pack(Language.TAJIK)
    return TestClient(
        create_app(
            language_packs={Language.TAJIK: pack},
            voice_catalog=fake_voice_catalog(),
            reminder_store=SqliteReminderStore(":memory:"),
        )
    )


def test_reminders_endpoints_save_list_and_forget() -> None:
    client = _client()

    created = client.post(
        "/reminders",
        json={"text": "Call mother", "due": "2026-10-29T18:00:00+00:00"},
    )
    assert created.status_code == 201
    reminder_id = created.json()["id"]

    listed = client.get("/reminders")
    assert listed.status_code == 200
    assert [reminder["text"] for reminder in listed.json()] == ["Call mother"]

    forgotten = client.delete(f"/reminders/{reminder_id}")
    assert forgotten.status_code == 204
    assert client.get("/reminders").json() == []


def test_rejects_a_reminder_without_text() -> None:
    response = _client().post(
        "/reminders",
        json={"text": "   ", "due": "2026-10-29T18:00:00+00:00"},
    )

    assert response.status_code == 422


def test_forgetting_an_unknown_id_reports_not_found() -> None:
    response = _client().delete("/reminders/nope")

    assert response.status_code == 404
