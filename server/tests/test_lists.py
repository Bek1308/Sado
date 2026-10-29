from collections.abc import Sequence

from fastapi.testclient import TestClient

from sado.application.converse import Converse
from sado.application.list_tools import ADD_TO_LIST, READ_LIST, REMOVE_FROM_LIST
from sado.application.lists import Lists
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
from sado.domain.language import Language
from sado.infrastructure.memory.sqlite_lists import SqliteListStore
from sado.main import create_app
from tests.fakes import fake_language_pack, fake_voice_catalog


def _lists() -> Lists:
    return Lists(SqliteListStore(":memory:"))


def test_adds_items_once_and_keeps_their_order() -> None:
    lists = _lists()

    lists.add("Xarid", ["non", "sut"])
    lists.add("  xarid ", ["Sut", "tuxum"])

    assert lists.read("XARID") == ["non", "sut", "tuxum"]


def test_removes_by_exact_word_or_by_part_of_an_item() -> None:
    lists = _lists()
    lists.add("xarid", ["non", "2 litr sut", "olma"])

    removed = lists.remove("xarid", ["sut", "OLMA", "go'sht"])

    assert removed == ["2 litr sut", "olma"]
    assert lists.read("xarid") == ["non"]


def test_lists_are_kept_apart() -> None:
    lists = _lists()
    lists.add("xarid", ["non"])
    lists.add("vazifalar", ["onaga qo'ng'iroq"])

    assert lists.read("xarid") == ["non"]
    assert [item.list_name for item in lists.everything()] == ["vazifalar", "xarid"]


class _Model:
    def __init__(self, *turns: ModelTurn) -> None:
        self._turns = list(turns)
        self.steps: list[list[ToolStep]] = []

    def respond(
        self,
        instructions: str,
        conversation: Sequence[Message],
        tools: Sequence[ToolSpec],
        steps: Sequence[ToolStep],
    ) -> ModelTurn:
        self.steps.append(list(steps))
        return self._turns.pop(0)


_QUESTION = [Message(Speaker.USER, "Xarid ro'yxatiga non va sut qo'sh")]


def test_sado_adds_to_a_list_and_tells_the_app() -> None:
    lists = _lists()
    model = _Model(
        ToolRequest(
            calls=(ToolCall("c1", ADD_TO_LIST.name, {"list": "xarid", "items": ["non", "sut"]}),)
        ),
        Answer("Qo'shdim."),
    )

    reply = Converse(model, lists=lists).execute(_QUESTION, Language.UZBEK)

    assert reply.lists_changed
    assert lists.read("xarid") == ["non", "sut"]
    assert model.steps[1][0].results[0].output == "Added: non, sut. The list now has: non, sut."


def test_reading_a_list_changes_nothing() -> None:
    lists = _lists()
    lists.add("xarid", ["non"])
    model = _Model(
        ToolRequest(calls=(ToolCall("c1", READ_LIST.name, {"list": "xarid"}),)),
        Answer("Ro'yxatda non bor."),
    )

    reply = Converse(model, lists=lists).execute(_QUESTION, Language.UZBEK)

    assert not reply.lists_changed
    assert model.steps[1][0].results[0].output == "The list now has: non."


def test_a_list_tool_without_a_name_is_reported_to_the_model() -> None:
    model = _Model(
        ToolRequest(calls=(ToolCall("c1", REMOVE_FROM_LIST.name, {"list": "  ", "items": ["x"]}),)),
        Answer("Qaysi ro'yxat?"),
    )

    Converse(model, lists=_lists()).execute(_QUESTION, Language.UZBEK)

    assert model.steps[1][0].results[0].output == "Nothing done: A list needs a name."


def test_lists_endpoints_show_and_remove_items() -> None:
    pack, _ = fake_language_pack(Language.UZBEK)
    store = SqliteListStore(":memory:")
    Lists(store).add("xarid", ["non", "sut"])
    client = TestClient(
        create_app(
            language_packs={Language.UZBEK: pack},
            voice_catalog=fake_voice_catalog(),
            reasoning_model=_Model(Answer("Ha.")),
            list_store=store,
        )
    )

    shown = client.get("/lists").json()
    assert [(group["name"], [item["text"] for item in group["items"]]) for group in shown] == [
        ("xarid", ["non", "sut"])
    ]

    item_id = shown[0]["items"][0]["id"]
    assert client.delete(f"/lists/items/{item_id}").status_code == 204
    assert client.delete(f"/lists/items/{item_id}").status_code == 404
