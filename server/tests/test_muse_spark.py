import json
from typing import Any

import httpx
import pytest

from sado.application.converse import REMEMBER
from sado.domain.conversation import (
    Answer,
    Message,
    Speaker,
    ToolCall,
    ToolRequest,
    ToolResult,
    ToolStep,
)
from sado.domain.errors import ReasoningUnavailableError, UnsupportedPaperError
from sado.domain.vision import Explanation, Paper
from sado.infrastructure.reasoning.muse_spark import MuseSparkReasoner

_CONVERSATION = [
    Message(Speaker.USER, "Salom"),
    Message(Speaker.SADO, "Salom!"),
    Message(Speaker.USER, "Ismim Aziz, eslab qol"),
]


def _reasoner(
    reply: dict[str, Any], sent: list[dict[str, Any]], status: int = 200
) -> MuseSparkReasoner:
    def handle(request: httpx.Request) -> httpx.Response:
        sent.append(json.loads(request.content))
        return httpx.Response(status, json=reply)

    http = httpx.Client(base_url="https://api.test/v1", transport=httpx.MockTransport(handle))
    return MuseSparkReasoner(http=http, model="muse-spark-1.3", reasoning_effort="low")


def _message(**message: object) -> dict[str, Any]:
    return {"choices": [{"message": {"role": "assistant", **message}}]}


def test_sends_the_conversation_and_returns_the_answer() -> None:
    sent: list[dict[str, Any]] = []
    reasoner = _reasoner(_message(content="Salom, Aziz!"), sent)

    turn = reasoner.respond("Be Sado.", _CONVERSATION, [REMEMBER], [])

    assert turn == Answer("Salom, Aziz!")
    request = sent[0]
    assert request["model"] == "muse-spark-1.3"
    assert request["reasoning_effort"] == "low"
    assert [(m["role"], m["content"]) for m in request["messages"]] == [
        ("system", "Be Sado."),
        ("user", "Salom"),
        ("assistant", "Salom!"),
        ("user", "Ismim Aziz, eslab qol"),
    ]
    assert request["tools"][0]["function"]["name"] == "remember"


def test_returns_the_tools_the_model_wants_to_use() -> None:
    reply = _message(
        content=None,
        tool_calls=[
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "remember", "arguments": '{"fact": "Ismi Aziz"}'},
            },
            {
                "id": "call_2",
                "type": "function",
                "function": {"name": "remember", "arguments": "not json"},
            },
        ],
    )

    turn = _reasoner(reply, []).respond("Be Sado.", _CONVERSATION, [REMEMBER], [])

    assert turn == ToolRequest(
        calls=(
            ToolCall("call_1", "remember", {"fact": "Ismi Aziz"}),
            ToolCall("call_2", "remember", {}),
        )
    )


def test_replays_earlier_tool_calls_and_their_results() -> None:
    sent: list[dict[str, Any]] = []
    call = ToolCall("call_1", "remember", {"fact": "Ismi Aziz"})
    step = ToolStep(results=(ToolResult(call, "Saved."),))

    _reasoner(_message(content="Eslab qoldim."), sent).respond(
        "Be Sado.", _CONVERSATION, [REMEMBER], [step]
    )

    *_, assistant, tool = sent[0]["messages"]
    assert assistant["tool_calls"][0]["function"] == {
        "name": "remember",
        "arguments": '{"fact": "Ismi Aziz"}',
    }
    assert tool == {"role": "tool", "tool_call_id": "call_1", "content": "Saved."}


def test_sends_no_tools_when_there_are_none() -> None:
    sent: list[dict[str, Any]] = []

    _reasoner(_message(content="Salom!"), sent).respond("Be Sado.", _CONVERSATION, [], [])

    assert "tools" not in sent[0]


@pytest.mark.parametrize(
    ("reply", "status"),
    [({"error": "rate limited"}, 429), ({"unexpected": True}, 200), ({"choices": []}, 200)],
)
def test_reports_that_sado_cannot_think_when_the_api_fails(
    reply: dict[str, Any], status: int
) -> None:
    with pytest.raises(ReasoningUnavailableError):
        _reasoner(reply, [], status).respond("Be Sado.", _CONVERSATION, [], [])


def test_explains_a_photographed_paper() -> None:
    sent: list[dict[str, Any]] = []
    reasoner = _reasoner(_message(content="This is a notice."), sent)
    paper = Paper(data=b"paper", media_type="image/jpeg")

    explanation = reasoner.explain(paper, "Be Sado.")

    assert explanation == Explanation("This is a notice.")
    request = sent[0]
    assert request["model"] == "muse-spark-1.3"
    system, user = request["messages"]
    assert (system["role"], system["content"]) == ("system", "Be Sado.")
    assert user["role"] == "user"
    text, image = user["content"]
    assert text == {"type": "text", "text": "What is this paper?"}
    assert image == {
        "type": "image_url",
        "image_url": {"url": "data:image/jpeg;base64,cGFwZXI="},
    }


def test_explains_a_text_file() -> None:
    sent: list[dict[str, Any]] = []
    reasoner = _reasoner(_message(content="This is a notice."), sent)
    paper = Paper(data=b"Permit 42 expires soon", media_type="text/plain")

    explanation = reasoner.explain(paper, "Be Sado.")

    assert explanation == Explanation("This is a notice.")
    *_, user = sent[0]["messages"]
    assert user["content"] == "What is this paper?\n\nPermit 42 expires soon"


def test_reads_a_text_file_in_a_local_encoding() -> None:
    sent: list[dict[str, Any]] = []
    reasoner = _reasoner(_message(content="ok"), sent)
    paper = Paper(data="Салом".encode("windows-1251"), media_type="text/plain")

    reasoner.explain(paper, "Be Sado.")

    *_, user = sent[0]["messages"]
    assert user["content"].endswith("Салом")


def test_keeps_the_head_and_tail_of_a_long_text_file() -> None:
    sent: list[dict[str, Any]] = []
    reasoner = _reasoner(_message(content="ok"), sent)
    paper = Paper(data=b"x" * 5000 + b"y" * 20000, media_type="text/plain")

    reasoner.explain(paper, "Be Sado.")

    *_, user = sent[0]["messages"]
    content = user["content"]
    assert "[…]" in content
    assert len(content) < len(paper.data)
    assert content.endswith("y" * 6000)


def test_rejects_a_file_type_sado_cannot_read() -> None:
    paper = Paper(data=b"sound", media_type="audio/mpeg")

    with pytest.raises(UnsupportedPaperError):
        _reasoner(_message(content="ok"), []).explain(paper, "Be Sado.")


def test_reports_that_sado_cannot_read_when_the_api_fails() -> None:
    paper = Paper(data=b"paper", media_type="image/jpeg")

    with pytest.raises(ReasoningUnavailableError):
        _reasoner({"error": "down"}, [], 503).explain(paper, "Be Sado.")
