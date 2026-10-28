from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class Speaker(StrEnum):
    USER = "user"
    SADO = "sado"


@dataclass(frozen=True, slots=True)
class Message:
    speaker: Speaker
    text: str


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """Something Sado can do while answering, described so a model knows when to use it."""

    name: str
    description: str
    parameters: Mapping[str, object]
    """JSON Schema of the arguments."""


@dataclass(frozen=True, slots=True)
class ToolCall:
    id: str
    name: str
    arguments: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class ToolResult:
    call: ToolCall
    output: str


@dataclass(frozen=True, slots=True)
class ToolStep:
    """Tools the model asked for in one go, with what each of them returned."""

    results: tuple[ToolResult, ...]


@dataclass(frozen=True, slots=True)
class Answer:
    text: str


@dataclass(frozen=True, slots=True)
class ToolRequest:
    calls: tuple[ToolCall, ...]


type ModelTurn = Answer | ToolRequest


class ReasoningModel(Protocol):
    def respond(
        self,
        instructions: str,
        conversation: Sequence[Message],
        tools: Sequence[ToolSpec],
        steps: Sequence[ToolStep],
    ) -> ModelTurn:
        """Either answers as Sado or asks to use some of the tools first.

        `steps` holds the tool calls already made for this answer, oldest first.
        """
        ...
