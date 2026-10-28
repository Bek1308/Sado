from collections.abc import Sequence
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


class ReasoningModel(Protocol):
    def reply(self, instructions: str, conversation: Sequence[Message]) -> str:
        """Returns Sado's next message, following the instructions."""
        ...
