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

    def screenshot(self) -> bytes:
        """The whole screen as a PNG, for Sado to look at."""
        ...

    def press_media_key(self, key: str) -> None:
        """One of: play_pause, next, previous, volume_up, volume_down, mute."""
        ...

    def press_keys(self, window_id: int, keys: str) -> None:
        """Brings the window to the front and presses a shortcut, e.g. "{Ctrl}s"."""
        ...

    def set_window_state(self, window_id: int, state: str) -> None:
        """One of: minimize, maximize, restore."""
        ...

    def lock(self) -> None: ...

    def status(self) -> str:
        """Battery, memory, disk and processor load in a few lines."""
        ...

    def find_files(self, name: str, limit: int) -> list[str]:
        """Paths of the user's files whose name contains `name`, newest first."""
        ...

    def clipboard(self) -> str: ...

    def copy(self, text: str) -> None: ...
