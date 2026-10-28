from sado.domain.errors import EmptyMemoryError, UnknownMemoryError
from sado.domain.memory import Memory, MemoryStore


class Memories:
    """What the user has asked Sado to remember."""

    _RECALL_LIMIT = 8
    _LIST_LIMIT = 500

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    def remember(self, text: str) -> Memory:
        cleaned = " ".join(text.split())
        if not cleaned:
            raise EmptyMemoryError
        return self._store.add(cleaned)

    def saved(self) -> list[Memory]:
        return self._store.recent(self._LIST_LIMIT)

    def forget(self, memory_id: str) -> None:
        if not self._store.delete(memory_id):
            raise UnknownMemoryError(memory_id)

    def recall(self, about: str) -> list[Memory]:
        # Word endings in Tajik and Uzbek often defeat the search, and a personal store is
        # small, so the newest memories fill whatever room the search leaves.
        found = self._store.search(about, self._RECALL_LIMIT)
        seen = {memory.id for memory in found}
        for memory in self._store.recent(self._RECALL_LIMIT):
            if len(found) >= self._RECALL_LIMIT:
                break
            if memory.id not in seen:
                found.append(memory)
        return found
