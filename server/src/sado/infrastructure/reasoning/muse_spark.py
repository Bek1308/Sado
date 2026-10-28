"""Sado's thinking with Meta's Muse Spark, through the Model API's Chat Completions endpoint."""

import base64
import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import httpx

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
from sado.domain.errors import ReasoningUnavailableError, UnsupportedPaperError
from sado.domain.vision import Explanation, Paper, PaperKind, decode_text, paper_kind

MODEL_API_URL = "https://api.meta.ai/v1"

_ROLES = {Speaker.USER: "user", Speaker.SADO: "assistant"}


@dataclass(frozen=True, slots=True)
class MuseSparkReasoner:
    http: httpx.Client
    """Already pointed at the Model API and carrying the API key."""
    model: str = "muse-spark-1.3"
    reasoning_effort: str = "low"
    """Short spoken replies need little deliberation, and every second of it is heard."""

    def respond(
        self,
        instructions: str,
        conversation: Sequence[Message],
        tools: Sequence[ToolSpec],
        steps: Sequence[ToolStep],
    ) -> ModelTurn:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": _messages(instructions, conversation, steps),
            "reasoning_effort": self.reasoning_effort,
        }
        if tools:
            payload["tools"] = [_tool(spec) for spec in tools]

        message = self._complete(payload)
        calls = message.get("tool_calls") or []
        if calls:
            return ToolRequest(calls=tuple(_tool_call(call) for call in calls))
        return Answer(text=message.get("content") or "")

    def explain(self, paper: Paper, instructions: str) -> Explanation:
        message = self._complete(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": instructions},
                    {"role": "user", "content": _user_content(paper)},
                ],
                "reasoning_effort": self.reasoning_effort,
            }
        )
        return Explanation(text=message.get("content") or "")

    def _complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self.http.post("/chat/completions", json=payload)
            response.raise_for_status()
            message: dict[str, Any] = response.json()["choices"][0]["message"]
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as error:
            raise ReasoningUnavailableError from error
        return message


_MAX_TEXT_CHARS = 12_000


def _user_content(paper: Paper) -> str | list[dict[str, Any]]:
    match paper_kind(paper.media_type):
        case PaperKind.PHOTO:
            image = base64.b64encode(paper.data).decode("ascii")
            return [
                {"type": "text", "text": "What is this paper?"},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{paper.media_type};base64,{image}"},
                },
            ]
        case PaperKind.TEXT:
            return f"What is this paper?\n\n{_clip(decode_text(paper.data))}"
        case PaperKind.DOCUMENT | PaperKind.SPOKEN | None:
            raise UnsupportedPaperError(paper.media_type)


def _clip(text: str) -> str:
    # Contracts hide key dates at the end, so a long file keeps its head
    # and its tail instead of only its head.
    if len(text) <= _MAX_TEXT_CHARS:
        return text
    half = _MAX_TEXT_CHARS // 2
    return f"{text[:half]}\n[…]\n{text[-half:]}"


def _messages(
    instructions: str, conversation: Sequence[Message], steps: Sequence[ToolStep]
) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = [{"role": "system", "content": instructions}]
    messages += [
        {"role": _ROLES[message.speaker], "content": message.text} for message in conversation
    ]
    for step in steps:
        messages.append(
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": result.call.id,
                        "type": "function",
                        "function": {
                            "name": result.call.name,
                            "arguments": json.dumps(result.call.arguments, ensure_ascii=False),
                        },
                    }
                    for result in step.results
                ],
            }
        )
        messages += [
            {"role": "tool", "tool_call_id": result.call.id, "content": result.output}
            for result in step.results
        ]
    return messages


def _tool(spec: ToolSpec) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": spec.name,
            "description": spec.description,
            "parameters": spec.parameters,
        },
    }


def _tool_call(call: dict[str, Any]) -> ToolCall:
    function = call["function"]
    # The model's arguments follow the schema only loosely; a broken payload becomes an
    # empty one, and the tool reports what is missing.
    try:
        arguments = json.loads(function.get("arguments") or "{}")
    except json.JSONDecodeError:
        arguments = {}
    if not isinstance(arguments, dict):
        arguments = {}
    return ToolCall(id=str(call["id"]), name=str(function["name"]), arguments=arguments)
