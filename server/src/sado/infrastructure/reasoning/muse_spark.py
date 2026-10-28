"""Sado's thinking with Meta's Muse Spark, through the Model API's Chat Completions endpoint."""

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
from sado.domain.errors import ReasoningUnavailableError

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

        try:
            response = self.http.post("/chat/completions", json=payload)
            response.raise_for_status()
            message = response.json()["choices"][0]["message"]
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as error:
            raise ReasoningUnavailableError from error

        calls = message.get("tool_calls") or []
        if calls:
            return ToolRequest(calls=tuple(_tool_call(call) for call in calls))
        return Answer(text=message.get("content") or "")


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
