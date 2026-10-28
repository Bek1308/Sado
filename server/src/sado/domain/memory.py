from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Memory:
    """A fact the user asked Sado to keep, in the user's own words."""

    id: str
    text: str
    created_at: datetime


class MemoryStore(Protocol):
    def add(self, text: str) -> Memory: ...

    def recent(self, limit: int) -> list[Memory]:
        """Newest first."""
        ...

    def search(self, query: str, limit: int) -> list[Memory]:
        """Best matches first; empty when nothing matches."""
        ...

    def delete(self, memory_id: str) -> bool:
        """False when no memory has that id."""
        ...
