"""The user's Windows computer, driven through Windows UI Automation.

Windows Terminal exposes each tab's text through UI Automation, so Sado can read what an
agent in a terminal just answered and type it a new task like a person would.
"""

import ctypes
import os
import subprocess
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from ctypes import wintypes
from typing import Any

import uiautomation as auto

from sado.domain.desktop import WindowInfo
from sado.domain.errors import DesktopUnavailableError

_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_COMMAND_TIMEOUT_SECONDS = 60
_COMMAND_OUTPUT_LIMIT = 3000
_SEARCH_DEPTH = 14
_TERMINAL_CLASS = "TermControl"
# Gives the target window time to take focus before keys arrive.
_FOCUS_SETTLE_SECONDS = 0.25


class WindowsDesktop:
    def windows(self) -> list[WindowInfo]:
        with _automation():
            return [
                WindowInfo(id=window.NativeWindowHandle, title=window.Name, app=_app(window))
                for window in auto.GetRootControl().GetChildren()
                if window.Name and window.ControlTypeName == "WindowControl"
            ]

    def read(self, window_id: int, max_chars: int) -> str:
        with _automation():
            text = _visible_text(_window(window_id))
        lines = [line.rstrip() for line in text.splitlines()]
        while lines and not lines[-1]:
            lines.pop()
        return "\n".join(lines)[-max_chars:]

    def focus(self, window_id: int) -> None:
        with _automation():
            _window(window_id).SetActive()

    def type_text(self, window_id: int, text: str, submit: bool) -> None:
        with _automation():
            window = _window(window_id)
            window.SetActive()
            time.sleep(_FOCUS_SETTLE_SECONDS)
            previous = auto.GetClipboardText()
            # Pasting is instant and keeps every character intact; a terminal would
            # warn about a multi-line paste, so the text travels as one line.
            auto.SetClipboardText(" ".join(text.splitlines()))
            try:
                auto.SendKeys("{Ctrl}v", waitTime=0.1)
                if submit:
                    auto.SendKeys("{Enter}", waitTime=0.1)
            finally:
                auto.SetClipboardText(previous or "")

    def close(self, window_id: int) -> None:
        with _automation():
            _window(window_id).GetWindowPattern().Close()

    def open(self, target: str) -> None:
        # The shell's own "open", not a command line: nothing in `target` can run as code.
        try:
            os.startfile(target)  # type: ignore[attr-defined, unused-ignore]
        except OSError as error:
            raise DesktopUnavailableError(f"could not open {target}") from error

    def run_command(self, command: str) -> str:
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=_COMMAND_TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise DesktopUnavailableError("the command took too long") from error
        output = (result.stdout + result.stderr).strip()
        if result.returncode:
            output = f"Exit code {result.returncode}.\n{output}"
        return output[-_COMMAND_OUTPUT_LIMIT:]


@contextmanager
def _automation() -> Iterator[None]:
    # FastAPI runs each request on its own worker thread; UI Automation is COM and must be
    # set up on every thread that uses it.
    with auto.UIAutomationInitializerInThread():
        try:
            yield
        except DesktopUnavailableError:
            raise
        except Exception as error:
            raise DesktopUnavailableError(str(error) or type(error).__name__) from error


# The library types every element as a plain Control; windows carry more methods.
def _window(window_id: int) -> Any:  # noqa: ANN401
    window = auto.ControlFromHandle(window_id)
    if window is None or not window.Exists(0, 0):
        raise DesktopUnavailableError("that window is no longer open")
    return window


def _visible_text(window: auto.Control) -> str:
    """Text a person would read in the window: a terminal's buffer, or its labels."""
    texts: list[tuple[bool, str]] = []
    for control, _ in auto.WalkControl(window, maxDepth=_SEARCH_DEPTH):
        pattern = _text_pattern(control)
        if pattern is not None:
            # Tabs and title bars expose text too; the terminal buffer is the one to read.
            is_terminal = control.ClassName == _TERMINAL_CLASS
            texts.append((is_terminal, str(pattern.DocumentRange.GetText(-1))))
    if texts:
        return max(texts, key=lambda found: (found[0], len(found[1])))[1]
    names = [
        control.Name
        for control, _ in auto.WalkControl(window, maxDepth=_SEARCH_DEPTH)
        if control.Name and control.ControlTypeName in {"TextControl", "EditControl"}
    ]
    return "\n".join(names)


def _text_pattern(control: Any) -> auto.TextPattern | None:  # noqa: ANN401
    # Only some control classes have GetTextPattern; GetPattern works on every element.
    get_pattern: Callable[[int], auto.TextPattern | None] = control.GetPattern
    try:
        return get_pattern(auto.PatternId.TextPattern)
    except (LookupError, ValueError, OSError):
        return None


def _app(window: auto.Control) -> str:
    """The program behind a window, e.g. "WindowsTerminal" or "chrome"."""
    handle = ctypes.windll.kernel32.OpenProcess(
        _PROCESS_QUERY_LIMITED_INFORMATION, False, window.ProcessId
    )
    if not handle:
        return window.ClassName
    try:
        size = wintypes.DWORD(260)
        buffer = ctypes.create_unicode_buffer(size.value)
        if ctypes.windll.kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            return os.path.splitext(os.path.basename(buffer.value))[0]
        return window.ClassName
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)
