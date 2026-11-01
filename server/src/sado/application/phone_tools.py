"""Tools that let Sado act on the phone the user is talking to.

Each tool only checks its arguments and returns a PhoneAction; the app performs it with
the phone's own screens. Calls and messages open the dialer or the composer ready to go,
so nothing reaches another person without the user's tap.
"""

import re
from collections.abc import Callable

from sado.domain.conversation import ToolCall, ToolResult, ToolSpec
from sado.domain.phone import PhoneAction

_MAX_TEXT = 1_000
_MAX_NAME = 100
_MAX_TIMER_MINUTES = 24 * 60
_TIME = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")
_MESSAGE_APPS = ("sms", "whatsapp", "telegram")

_CONTACT = {
    "type": "string",
    "description": (
        "A phone number, or the person as the user would have saved them in their "
        "contacts, in the base form without suffixes, e.g. 'Onam' or 'Aziz', not 'Onamga'."
    ),
}


def _spec(name: str, description: str, required: tuple[str, ...], **properties: object) -> ToolSpec:
    return ToolSpec(
        name=name,
        description=description,
        parameters={"type": "object", "properties": properties, "required": list(required)},
    )


PHONE_CALL = _spec(
    "phone_call",
    "Call someone from the user's phone. The phone opens its dialer with the number "
    "ready, and the user presses call.",
    ("contact",),
    contact=_CONTACT,
)
PHONE_MESSAGE = _spec(
    "phone_message",
    "Write a message to someone from the user's phone. The phone opens the app with the "
    "text filled in, and the user presses send.",
    ("contact", "text"),
    contact=_CONTACT,
    text={"type": "string", "description": "The message, in the language the user wants."},
    app={
        "type": "string",
        "enum": list(_MESSAGE_APPS),
        "description": "Which app; SMS unless the user names another.",
    },
)
PHONE_ALARM = _spec(
    "phone_alarm",
    "Set an alarm in the phone's clock, e.g. to wake the user up. For things Sado "
    "should say later, use remind instead.",
    ("time",),
    time={"type": "string", "description": "24-hour local time, e.g. '06:30'."},
    label={"type": "string", "description": "Optional short label."},
)
PHONE_TIMER = _spec(
    "phone_timer",
    "Start a countdown timer in the phone's clock.",
    ("minutes",),
    minutes={"type": "number", "description": "How long, in minutes, e.g. 10 or 0.5."},
    label={"type": "string", "description": "Optional short label, e.g. 'Plov'."},
)
PHONE_OPEN = _spec(
    "phone_open",
    "Open an app or a web address on the user's phone, e.g. 'Telegram', 'Camera', "
    "'Settings' or 'https://youtube.com'.",
    ("target",),
    target={
        "type": "string",
        "description": "The app's name as phones show it, in English, or a web address.",
    },
)
PHONE_NAVIGATE = _spec(
    "phone_navigate",
    "Show the way to a place in the phone's maps app.",
    ("destination",),
    destination={"type": "string", "description": "The place, e.g. 'Dushanbe airport'."},
)
PHONE_FLASHLIGHT = _spec(
    "phone_flashlight",
    "Turn the phone's flashlight on or off.",
    ("on",),
    on={"type": "boolean", "description": "True to turn it on, false to turn it off."},
)

PHONE_TOOLS = (
    PHONE_CALL,
    PHONE_MESSAGE,
    PHONE_ALARM,
    PHONE_TIMER,
    PHONE_OPEN,
    PHONE_NAVIGATE,
    PHONE_FLASHLIGHT,
)
PHONE_TOOL_NAMES = frozenset(tool.name for tool in PHONE_TOOLS)


class _BadArgumentError(Exception):
    pass


def run_phone_tool(call: ToolCall) -> tuple[ToolResult, PhoneAction | None]:
    """Checks a phone tool call and turns it into the action the app will perform."""
    build = _BUILDERS.get(call.name)
    if build is None:
        return ToolResult(call, f"Unknown tool '{call.name}'."), None
    try:
        action, said = build(call)
    except _BadArgumentError as error:
        return ToolResult(call, f"Nothing done: {error}."), None
    return ToolResult(call, f"{said} Tell the user in a few words."), action


def _text(call: ToolCall, name: str, limit: int, *, required: bool = True) -> str:
    value = call.arguments.get(name, "")
    if not isinstance(value, str):
        raise _BadArgumentError(f"'{name}' must be text")
    value = value.strip()
    if required and not value:
        raise _BadArgumentError(f"'{name}' is missing")
    if len(value) > limit:
        raise _BadArgumentError(f"'{name}' is too long")
    return value


def _call(call: ToolCall) -> tuple[PhoneAction, str]:
    contact = _text(call, "contact", _MAX_NAME)
    return (
        PhoneAction("call", {"contact": contact}),
        f"The phone opens the dialer for {contact}; the user presses call. If {contact} "
        "is not in their contacts, the app tells them.",
    )


def _message(call: ToolCall) -> tuple[PhoneAction, str]:
    contact = _text(call, "contact", _MAX_NAME)
    text = _text(call, "text", _MAX_TEXT)
    app = _text(call, "app", _MAX_NAME, required=False).lower() or "sms"
    if app not in _MESSAGE_APPS:
        raise _BadArgumentError(f"'app' must be one of {', '.join(_MESSAGE_APPS)}")
    return (
        PhoneAction("message", {"contact": contact, "text": text, "app": app}),
        f"The phone opens {app} with the message to {contact} filled in; the user presses send.",
    )


def _alarm(call: ToolCall) -> tuple[PhoneAction, str]:
    time = _text(call, "time", 5)
    match = _TIME.match(time)
    if match is None:
        raise _BadArgumentError("'time' must look like 06:30")
    hour, minute = match.groups()
    label = _text(call, "label", _MAX_NAME, required=False)
    return (
        PhoneAction("alarm", {"hour": str(int(hour)), "minute": minute, "label": label}),
        f"The alarm is set for {int(hour):02d}:{minute}.",
    )


def _timer(call: ToolCall) -> tuple[PhoneAction, str]:
    minutes = call.arguments.get("minutes")
    # bool is an int in Python, but "true minutes" is not a duration.
    if isinstance(minutes, bool) or not isinstance(minutes, int | float):
        raise _BadArgumentError("'minutes' must be a number")
    if not 0 < minutes <= _MAX_TIMER_MINUTES:
        raise _BadArgumentError("'minutes' must be more than 0 and at most a day")
    seconds = max(1, round(minutes * 60))
    label = _text(call, "label", _MAX_NAME, required=False)
    return (
        PhoneAction("timer", {"seconds": str(seconds), "label": label}),
        f"A timer for {minutes:g} minutes is running.",
    )


def _open(call: ToolCall) -> tuple[PhoneAction, str]:
    target = _text(call, "target", _MAX_TEXT)
    return (
        PhoneAction("open", {"target": target}),
        f"The phone opens {target}. If no such app is installed, the app tells them.",
    )


def _navigate(call: ToolCall) -> tuple[PhoneAction, str]:
    destination = _text(call, "destination", _MAX_TEXT)
    return (
        PhoneAction("navigate", {"destination": destination}),
        f"The maps app shows the way to {destination}.",
    )


def _flashlight(call: ToolCall) -> tuple[PhoneAction, str]:
    on = call.arguments.get("on")
    if not isinstance(on, bool):
        raise _BadArgumentError("'on' must be true or false")
    return (
        PhoneAction("flashlight", {"on": "true" if on else "false"}),
        f"The flashlight is {'on' if on else 'off'}.",
    )


_BUILDERS: dict[str, Callable[[ToolCall], tuple[PhoneAction, str]]] = {
    PHONE_CALL.name: _call,
    PHONE_MESSAGE.name: _message,
    PHONE_ALARM.name: _alarm,
    PHONE_TIMER.name: _timer,
    PHONE_OPEN.name: _open,
    PHONE_NAVIGATE.name: _navigate,
    PHONE_FLASHLIGHT.name: _flashlight,
}
