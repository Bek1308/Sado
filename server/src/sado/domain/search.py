from typing import Protocol


class WebSearch(Protocol):
    def search(self, query: str) -> str:
        """Looks `query` up on the live web and returns a short grounded summary."""
        ...
