from collections.abc import Sequence

import pytest
from fastapi.testclient import TestClient

from sado.application.converse import Converse
from sado.application.memories import Memories
from sado.domain.conversation import Answer, Message, ModelTurn, Speaker, ToolSpec, ToolStep
from sado.domain.errors import EmptyMemoryError, UnknownMemoryError
from sado.domain.language import Language
from sado.infrastructure.memory.sqlite_store import SqliteMemoryStore
from sado.main import create_app
from tests.fakes import fake_language_pack, fake_voice_catalog


def _store() -> SqliteMemoryStore:
    return SqliteMemoryStore(":memory:")


class _ListeningModel:
    def __init__(self) -> None:
        self.instructions = ""

    def respond(
        self,
        instructions: str,
        conversation: Sequence[Message],
        tools: Sequence[ToolSpec],
        steps: Sequence[ToolStep],
    ) -> ModelTurn:
        self.instructions = instructions
        return Answer("OK")


def test_store_lists_newest_first_and_forgets() -> None:
    store = _store()
    first = store.add("Mening ismim Aziz")
    second = store.add("Qizimning tug'ilgan kuni 12-mayda")

    assert [memory.id for memory in store.recent(10)] == [second.id, first.id]
    assert store.delete(first.id)
    assert not store.delete(first.id)
    assert [memory.id for memory in store.recent(10)] == [second.id]


def test_store_finds_words_despite_their_endings() -> None:
    store = _store()
    books = store.add("Men tarixiy kitoblarni yaxshi ko'raman")
    store.add("Ертага соат 9 да маҷлис дорам")

    assert [memory.id for memory in store.search("Qanday kitob o'qiy?", 5)] == [books.id]


def test_store_treats_user_text_as_words_not_query_syntax() -> None:
    store = _store()
    store.add("Choy ichishni yaxshi ko'raman")

    assert store.search('choy" OR * NEAR(', 5)[0].text == "Choy ichishni yaxshi ko'raman"
    assert store.search("?!", 5) == []


def test_remember_tidies_the_text_and_rejects_nothing() -> None:
    memories = Memories(_store())

    assert memories.remember("  Ismim   Aziz \n").text == "Ismim Aziz"
    with pytest.raises(EmptyMemoryError):
        memories.remember("   ")


def test_forgetting_an_unknown_memory_is_an_error() -> None:
    with pytest.raises(UnknownMemoryError):
        Memories(_store()).forget("missing")


def test_recall_puts_matches_first_then_fills_with_recent() -> None:
    memories = Memories(_store())
    match = memories.remember("Mening itim Rex deb ataladi")
    other = memories.remember("Ish soat 9 da boshlanadi")

    recalled = memories.recall("Itimning ismi nima?")

    assert [memory.id for memory in recalled] == [match.id, other.id]


def test_sado_hears_what_it_was_asked_to_remember() -> None:
    memories = Memories(_store())
    memories.remember("Foydalanuvchining ismi Aziz")
    model = _ListeningModel()

    Converse(model, memories).execute([Message(Speaker.USER, "Ismim nima?")], Language.UZBEK)

    assert "never invent others" in model.instructions
    assert "- Foydalanuvchining ismi Aziz" in model.instructions


def test_memories_endpoints_save_list_and_forget() -> None:
    pack, _ = fake_language_pack(Language.UZBEK)
    client = TestClient(
        create_app(
            language_packs={Language.UZBEK: pack},
            voice_catalog=fake_voice_catalog(),
            reasoning_model=_ListeningModel(),
            memory_store=_store(),
        )
    )

    created = client.post("/memories", json={"text": "Ismim Aziz"})
    assert created.status_code == 201
    memory_id = created.json()["id"]

    listed = client.get("/memories").json()
    assert [(memory["id"], memory["text"]) for memory in listed] == [(memory_id, "Ismim Aziz")]

    assert client.delete(f"/memories/{memory_id}").status_code == 204
    assert client.delete(f"/memories/{memory_id}").status_code == 404
    assert client.post("/memories", json={"text": "  "}).status_code == 422
