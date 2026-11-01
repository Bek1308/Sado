from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class WindowInfo:
    """An open window on the user's computer, as Sado can refer to it."""

    id: int
    title: str
    app: str


class Desktop(Protocol):
    """The user's computer: its windows, keyboard and shell."""

    def windows(self) -> list[WindowInfo]: ...

    def read(self, window_id: int, max_chars: int) -> str:
        """The latest text the window shows, e.g. a terminal agent's last answer."""
        ...

    def focus(self, window_id: int) -> None: ...

    def type_text(self, window_id: int, text: str, submit: bool) -> None:
        """Types into the window, pressing Enter afterwards when `submit` is set."""
        ...

    def close(self, window_id: int) -> None: ...

    def open(self, target: str) -> None:
        """Opens an app, file or web address the way Windows' Run box would."""
        ...

    def run_command(self, command: str) -> str:
        """Runs a PowerShell command and returns what it printed."""
        ...
