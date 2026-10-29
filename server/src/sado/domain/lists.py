from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ListItem:
    """One line on one of the user's lists, e.g. "bread" on the shopping list."""

    id: str
    list_name: str
    text: str


class ListStore(Protocol):
    def add(self, list_name: str, text: str) -> ListItem: ...

    def items(self, list_name: str) -> list[ListItem]:
        """Oldest first."""
        ...

    def everything(self) -> list[ListItem]:
        """Every item on every list, grouped by list, oldest first within a list."""
        ...

    def remove(self, item_id: str) -> bool:
        """False when no item has that id."""
        ...
