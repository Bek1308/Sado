import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sado.domain.phone import PhoneAction


@dataclass(slots=True)
class PhoneInbox:
    """Phone actions the owner asked for at the computer, waiting for their phone.

    The phone picks them up while Sado is open on it. An action nobody picks up soon is
    dropped: an alarm or a call asked for an hour ago is no longer what the user wants.
    """

    keep_for: timedelta = timedelta(minutes=2)
    now: Callable[[], datetime] = field(default=lambda: datetime.now(UTC))
    _waiting: list[tuple[datetime, PhoneAction]] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def post(self, actions: Sequence[PhoneAction]) -> None:
        with self._lock:
            self._waiting.extend((self.now(), action) for action in actions)

    def take(self) -> list[PhoneAction]:
        with self._lock:
            fresh = [action for at, action in self._waiting if self.now() - at < self.keep_for]
            self._waiting.clear()
        return fresh
