from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

IMAGE_MEDIA_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
TEXT_MEDIA_TYPES = frozenset({"text/plain", "text/markdown"})


@dataclass(frozen=True, slots=True)
class Paper:
    """A paper Sado should read: a photograph or a text file."""

    data: bytes
    media_type: str


@dataclass(frozen=True, slots=True)
class Explanation:
    text: str


class PaperKind(StrEnum):
    PHOTO = "photo"
    TEXT = "text"


def paper_kind(media_type: str) -> PaperKind | None:
    """How Sado reads this upload, or `None` when it cannot read it at all."""
    if media_type in IMAGE_MEDIA_TYPES:
        return PaperKind.PHOTO
    if media_type in TEXT_MEDIA_TYPES:
        return PaperKind.TEXT
    return None


class DocumentExplainer(Protocol):
    def explain(self, paper: Paper, instructions: str) -> Explanation:
        """Reads the paper and explains it following `instructions`."""
        ...
