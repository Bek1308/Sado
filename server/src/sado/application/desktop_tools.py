"""Tools that let Sado see and control the user's computer.

Looking is free: listing windows, reading a window, focusing it or opening an app. Anything
that types, closes or runs a command only becomes a pending action, and runs once the user
says yes through the app. The model can describe the action but can never confirm it.
"""

import secrets
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sado.domain.conversation import ToolCall, ToolResult, ToolSpec
from sado.domain.desktop import Desktop, WindowInfo
from sado.domain.errors import SadoError, UnknownActionError

_WINDOW = {
    "type": "string",
    "description": (
        "Which window: part of its title as list_windows showed it, e.g. 'Terminal' or "
        "'Chrome', or its id."
    ),
}


# Asking twice, once in words and once in the app, annoys people; only the app asks.
_CONFIRM = (
    "Call it as soon as the user asks: Sado's app then asks them to confirm before "
    "anything happens, so do not ask for permission yourself first."
)


def _spec(name: str, description: str, **properties: object) -> ToolSpec:
    return ToolSpec(
        name=name,
        description=description.replace("{confirm}", _CONFIRM),
        parameters={
            "type": "object",
            "properties": properties,
            "required": list(properties),
        },
    )


LIST_WINDOWS = _spec(
    "list_windows",
    "List the windows open on the user's computer, with their ids and titles.",
)
READ_WINDOW = _spec(
    "read_window",
    "Read the latest text a window shows, e.g. what an agent in a terminal just answered.",
    window=_WINDOW,
)
FOCUS_WINDOW = _spec("focus_window", "Bring a window to the front.", window=_WINDOW)
OPEN = _spec(
    "open",
    "Open an app, a file or a web address on the computer, e.g. 'notepad' or "
    "'https://youtube.com'.",
    target={"type": "string", "description": "App name, file path or web address."},
)
TYPE_INTO_WINDOW = _spec(
    "type_into_window",
    "Type text into a window and press Enter, e.g. give an agent in a terminal a new task. "
    "{confirm}",
    window=_WINDOW,
    text={"type": "string", "description": "Exactly what to type."},
)
CLOSE_WINDOW = _spec("close_window", "Close a window. {confirm}", window=_WINDOW)
RUN_COMMAND = _spec(
    "run_command",
    "Run a PowerShell command on the computer and get its output; prefer the other tools "
    "when they can do the job. {confirm}",
    command={"type": "string", "description": "The PowerShell command."},
)

DESKTOP_TOOLS = (
    LIST_WINDOWS,
    READ_WINDOW,
    FOCUS_WINDOW,
    OPEN,
    TYPE_INTO_WINDOW,
    CLOSE_WINDOW,
    RUN_COMMAND,
)


@dataclass(frozen=True, slots=True)
class PendingAction:
    id: str
    description: str
    run: Callable[[], str]
    created_at: datetime


class PendingActions:
    """Actions waiting for the user's yes. Each runs at most once, and only if it is fresh."""

    _LIFETIME = timedelta(minutes=5)

    def __init__(self) -> None:
        self._actions: dict[str, PendingAction] = {}
        self._lock = threading.Lock()

    def add(self, description: str, run: Callable[[], str]) -> PendingAction:
        action = PendingAction(
            # Unguessable, so only the app that received it can confirm it.
            id=secrets.token_urlsafe(16),
            description=description,
            run=run,
            created_at=datetime.now(UTC),
        )
        with self._lock:
            self._drop_stale()
            self._actions[action.id] = action
        return action

    def take(self, action_id: str) -> PendingAction:
        with self._lock:
            self._drop_stale()
            action = self._actions.pop(action_id, None)
        if action is None:
            raise UnknownActionError(action_id)
        return action

    def _drop_stale(self) -> None:
        oldest = datetime.now(UTC) - self._LIFETIME
        for action_id in [
            key for key, action in self._actions.items() if action.created_at < oldest
        ]:
            del self._actions[action_id]


class DesktopTools:
    _READ_LIMIT = 4000

    def __init__(self, desktop: Desktop, pending: PendingActions) -> None:
        self._desktop = desktop
        self._pending = pending

    def run(self, call: ToolCall) -> tuple[ToolResult, PendingAction | None]:
        try:
            return self._run(call)
        except SadoError as error:
            return ToolResult(call, f"Could not do that: {error}."), None

    def _run(self, call: ToolCall) -> tuple[ToolResult, PendingAction | None]:
        handlers: dict[str, Callable[[ToolCall], tuple[ToolResult, PendingAction | None]]] = {
            LIST_WINDOWS.name: self._list,
            READ_WINDOW.name: self._read,
            FOCUS_WINDOW.name: self._focus,
            OPEN.name: self._open,
            TYPE_INTO_WINDOW.name: self._ask_to_type,
            CLOSE_WINDOW.name: self._ask_to_close,
            RUN_COMMAND.name: self._ask_to_run,
        }
        handler = handlers.get(call.name)
        if handler is None:
            return ToolResult(call, f"Unknown tool '{call.name}'."), None
        return handler(call)

    def _list(self, call: ToolCall) -> tuple[ToolResult, None]:
        return ToolResult(call, _describe(self._desktop.windows())), None

    def _read(self, call: ToolCall) -> tuple[ToolResult, None]:
        window = self._find(_text(call, "window"))
        text = self._desktop.read(window.id, self._READ_LIMIT)
        return ToolResult(call, text or "The window shows no text."), None

    def _focus(self, call: ToolCall) -> tuple[ToolResult, None]:
        window = self._find(_text(call, "window"))
        self._desktop.focus(window.id)
        return ToolResult(call, f"'{window.title}' is in front now."), None

    def _open(self, call: ToolCall) -> tuple[ToolResult, None]:
        target = _text(call, "target")
        self._desktop.open(target)
        return ToolResult(call, f"Opened {target}."), None

    def _ask_to_type(self, call: ToolCall) -> tuple[ToolResult, PendingAction]:
        window = self._find(_text(call, "window"))
        text = _text(call, "text")
        return self._ask(
            call, f"Type into '{window.title}': {text}", lambda: self._type(window, text)
        )

    def _ask_to_close(self, call: ToolCall) -> tuple[ToolResult, PendingAction]:
        window = self._find(_text(call, "window"))
        return self._ask(call, f"Close '{window.title}'", lambda: self._close(window))

    def _ask_to_run(self, call: ToolCall) -> tuple[ToolResult, PendingAction]:
        command = _text(call, "command")
        return self._ask(
            call, f"Run: {command}", lambda: self._desktop.run_command(command) or "Done."
        )

    def _ask(
        self, call: ToolCall, description: str, run: Callable[[], str]
    ) -> tuple[ToolResult, PendingAction]:
        action = self._pending.add(description, run)
        return (
            ToolResult(
                call,
                f"Waiting for the user's yes: {description}. Say briefly what you are about "
                "to do and ask them to confirm. Do not say it is done.",
            ),
            action,
        )

    def _type(self, window: WindowInfo, text: str) -> str:
        self._desktop.type_text(window.id, text, submit=True)
        return f"Typed into '{window.title}'."

    def _close(self, window: WindowInfo) -> str:
        self._desktop.close(window.id)
        return f"Closed '{window.title}'."

    def _find(self, query: str) -> WindowInfo:
        windows = self._desktop.windows()
        if query.strip().isdigit():
            match = next((window for window in windows if window.id == int(query)), None)
            if match is not None:
                return match
        wanted = query.casefold().strip()
        matches = [window for window in windows if wanted and wanted in window.title.casefold()]
        exact = [window for window in matches if window.title.casefold() == wanted]
        if len(exact) == 1 or len(matches) == 1:
            return (exact or matches)[0]
        if not matches:
            raise WindowNotFoundError(query, windows)
        raise WindowNotFoundError(query, matches, ambiguous=True)


class WindowNotFoundError(SadoError):
    def __init__(
        self, query: str, candidates: list[WindowInfo], *, ambiguous: bool = False
    ) -> None:
        problem = "several windows match" if ambiguous else "no window matches"
        super().__init__(f"{problem} '{query}'. Windows:\n{_describe(candidates)}")


def _text(call: ToolCall, key: str) -> str:
    value = call.arguments.get(key)
    if not isinstance(value, str) or not value.strip():
        raise MissingArgumentError(key)
    return value.strip()


class MissingArgumentError(SadoError):
    def __init__(self, key: str) -> None:
        super().__init__(f"'{key}' must be text")


def _describe(windows: list[WindowInfo]) -> str:
    if not windows:
        return "No windows are open."
    return "\n".join(f"- id {window.id}: {window.title} ({window.app})" for window in windows)


DESKTOP_TOOL_NAMES = frozenset(tool.name for tool in DESKTOP_TOOLS)
