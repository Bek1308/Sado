from collections.abc import Sequence

from sado.domain.errors import UnknownListItemError, UnnamedListError
from sado.domain.lists import ListItem, ListStore


def _key(text: str) -> str:
    return " ".join(text.casefold().split())


class Lists:
    """The user's shopping lists, to-do lists and any other list they keep with Sado."""

    def __init__(self, store: ListStore) -> None:
        self._store = store

    def add(self, list_name: str, entries: Sequence[str]) -> list[ListItem]:
        name = self._name(list_name)
        present = {_key(item.text) for item in self._store.items(name)}
        added: list[ListItem] = []
        for entry in entries:
            text = " ".join(entry.split())
            # Saying "add milk" twice should not put milk on the list twice.
            if text and _key(text) not in present:
                added.append(self._store.add(name, text))
                present.add(_key(text))
        return added

    def remove(self, list_name: str, entries: Sequence[str]) -> list[str]:
        items = self._store.items(self._name(list_name))
        removed: list[str] = []
        for entry in entries:
            wanted = _key(entry)
            if not wanted:
                continue
            # Exact words first; otherwise "milk" also finds "2 litres of milk".
            match = next((item for item in items if _key(item.text) == wanted), None) or next(
                (item for item in items if wanted in _key(item.text)), None
            )
            if match is not None and self._store.remove(match.id):
                items.remove(match)
                removed.append(match.text)
        return removed

    def read(self, list_name: str) -> list[str]:
        return [item.text for item in self._store.items(self._name(list_name))]

    def everything(self) -> list[ListItem]:
        return self._store.everything()

    def forget_item(self, item_id: str) -> None:
        if not self._store.remove(item_id):
            raise UnknownListItemError(item_id)

    @staticmethod
    def _name(list_name: str) -> str:
        name = _key(list_name)
        if not name:
            raise UnnamedListError
        return name
