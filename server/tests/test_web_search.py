import json
from collections.abc import Sequence
from typing import Any

import httpx
import pytest

from sado.application.converse import SEARCH_WEB, Converse
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
from sado.domain.errors import WebSearchUnavailableError
from sado.domain.language import Language
from sado.infrastructure.reasoning.muse_search import MuseWebSearch

_ANSWER = {
    "output": [
        {"type": "web_search_call", "status": "completed"},
        {
            "type": "message",
            "content": [{"type": "output_text", "text": "Dushanbe: 14°C, sunny."}],
        },
    ]
}


def _search(reply: httpx.Response, sent: list[dict[str, Any]]) -> MuseWebSearch:
    def handle(request: httpx.Request) -> httpx.Response:
        sent.append(json.loads(request.content))
        return reply

    http = httpx.Client(base_url="https://api.test/v1", transport=httpx.MockTransport(handle))
    return MuseWebSearch(http=http, location={"country": "TJ", "city": "Dushanbe"})


def test_asks_the_responses_api_to_search_near_the_user() -> None:
    sent: list[dict[str, Any]] = []

    text = _search(httpx.Response(200, json=_ANSWER), sent).search("weather today")

    assert text == "Dushanbe: 14°C, sunny."
    tool = sent[0]["tools"][0]
    assert tool["type"] == "web_search"
    assert tool["user_location"] == {"type": "approximate", "country": "TJ", "city": "Dushanbe"}
    assert sent[0]["input"].startswith("weather today")


@pytest.mark.parametrize(
    "reply",
    [
        httpx.Response(503, json={"error": "down"}),
        httpx.Response(200, json={"output": []}),
        httpx.Response(200, text="<html>tunnel error</html>"),
    ],
)
def test_reports_when_the_web_cannot_be_searched(reply: httpx.Response) -> None:
    with pytest.raises(WebSearchUnavailableError):
        _search(reply, []).search("weather today")


class _Model:
    def __init__(self, *turns: ModelTurn) -> None:
        self._turns = list(turns)
        self.tools: list[Sequence[ToolSpec]] = []
        self.steps: list[list[ToolStep]] = []

    def respond(
        self,
        instructions: str,
        conversation: Sequence[Message],
        tools: Sequence[ToolSpec],
        steps: Sequence[ToolStep],
    ) -> ModelTurn:
        self.tools.append(tools)
        self.steps.append(list(steps))
        return self._turns.pop(0)


class _FakeSearch:
    def __init__(self, answer: str | None) -> None:
        self.answer = answer
        self.queries: list[str] = []

    def search(self, query: str) -> str:
        self.queries.append(query)
        if self.answer is None:
            raise WebSearchUnavailableError
        return self.answer


_QUESTION = [Message(Speaker.USER, "Bugun havo qanday?")]


def _ask(search: _FakeSearch) -> tuple[_Model, str]:
    model = _Model(
        ToolRequest(calls=(ToolCall("c1", SEARCH_WEB.name, {"query": " weather Dushanbe "}),)),
        Answer("Bugun quyoshli."),
    )
    reply = Converse(model, web_search=search).execute(_QUESTION, Language.UZBEK)
    return model, reply.text


def test_sado_searches_and_answers_from_the_result() -> None:
    search = _FakeSearch("Dushanbe: 14°C, sunny.")

    model, text = _ask(search)

    assert model.tools[0] == [SEARCH_WEB]
    assert search.queries == ["weather Dushanbe"]
    assert model.steps[1][0].results[0].output == "Dushanbe: 14°C, sunny."
    assert text == "Bugun quyoshli."


def test_a_failed_search_is_told_to_the_model_not_the_user() -> None:
    model, _ = _ask(_FakeSearch(None))

    assert model.steps[1][0].results[0].output.startswith("Search failed")
