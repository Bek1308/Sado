import threading
from dataclasses import dataclass, field


@dataclass(slots=True)
class WakeSignal:
    """Counts the times the user called "Sado", so the computer app can answer each call.

    The app asks with the count it last saw and waits; a new call wakes it at once.
    """

    _count: int = 0
    _changed: threading.Condition = field(default_factory=threading.Condition)

    def ring(self) -> None:
        with self._changed:
            self._count += 1
            self._changed.notify_all()

    def wait(self, after: int, timeout: float) -> int:
        """The count once it is past `after`, or as it stands when `timeout` runs out."""
        with self._changed:
            self._changed.wait_for(lambda: self._count > after, timeout)
            return self._count
