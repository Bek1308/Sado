from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

IMAGE_MEDIA_TYPES = frozenset({"image/jpeg", "image/png", "image/gif", "image/webp"})
TEXT_MEDIA_TYPES = frozenset({"application/json", "application/xml"})
DOCUMENT_MEDIA_TYPES = frozenset(
    {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.oasis.opendocument.text",
        "application/vnd.oasis.opendocument.spreadsheet",
        "application/vnd.oasis.opendocument.presentation",
        "text/html",
    }
)
# Cyrillic before Western European: Sado's first languages use Cyrillic scripts.
TEXT_ENCODINGS = ("utf-8-sig", "windows-1251", "latin-1")


def decode_text(data: bytes) -> str:
    """Best-effort text of raw bytes; latin-1 never fails, so this always answers."""
    for encoding in TEXT_ENCODINGS:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise AssertionError("latin-1 decodes any bytes")  # Unreachable by construction.


@dataclass(frozen=True, slots=True)
class Paper:
    """Anything Sado should read: a photo, a recording, or a document file."""

    data: bytes
    media_type: str


@dataclass(frozen=True, slots=True)
class Explanation:
    text: str


class PaperKind(StrEnum):
    PHOTO = "photo"
    SPOKEN = "spoken"
    TEXT = "text"
    DOCUMENT = "document"


def paper_kind(media_type: str) -> PaperKind | None:
    """How Sado reads this upload, or `None` when it cannot read it at all."""
    if media_type in DOCUMENT_MEDIA_TYPES:
        return PaperKind.DOCUMENT
    if media_type in TEXT_MEDIA_TYPES or media_type.startswith("text/"):
        return PaperKind.TEXT
    if media_type in IMAGE_MEDIA_TYPES:
        return PaperKind.PHOTO
    if media_type.startswith(("audio/", "video/")):
        return PaperKind.SPOKEN
    return None


class DocumentExplainer(Protocol):
    def explain(self, paper: Paper, instructions: str) -> Explanation:
        """Reads the paper and explains it following `instructions`."""
        ...


class DocumentReader(Protocol):
    def read(self, paper: Paper) -> str:
        """Plain text of a document paper.

        Raises UnreadablePaperError when the file holds no readable text.
        """
        ...
