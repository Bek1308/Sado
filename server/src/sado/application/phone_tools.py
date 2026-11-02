"""Tools that let Sado act on the phone the user is talking to.

Each tool only checks its arguments and returns a PhoneAction; the app carries it out. Calls
and text messages are placed and sent by the phone itself, but only after the app has asked
the user and heard a yes, so nothing reaches another person without their consent.
"""

import re
from collections.abc import Callable

from sado.domain.conversation import ToolCall, ToolResult, ToolSpec
from sado.domain.phone import PhoneAction

_MAX_TEXT = 1_000
_MAX_NAME = 100
_MAX_TIMER_MINUTES = 24 * 60
_MAX_EVENT_MINUTES = 24 * 60
_TIME = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")
_MOMENT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?([+-]\d{2}:\d{2}|Z)$")
_MESSAGE_APPS = ("sms", "whatsapp", "telegram")
_VOLUME = ("up", "down", "mute", "unmute", "max")
_MEDIA = ("play_pause", "next", "previous")
_SETTINGS = ("wifi", "bluetooth", "display", "sound", "battery", "location", "airplane", "all")
# Only these wait for the user's yes in the app; everything else just happens.
_ASKED_FIRST = "The app asks the user to confirm before it happens; do not ask yourself."

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
    f"Call someone from the user's phone. {_ASKED_FIRST}",
    ("contact",),
    contact=_CONTACT,
)
PHONE_MESSAGE = _spec(
    "phone_message",
    "Send a message to someone from the user's phone. An SMS is sent by the phone itself; "
    "WhatsApp and Telegram open with the text ready and the user presses send. "
    f"{_ASKED_FIRST}",
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
    "Show the way to a place, or places nearby such as 'pharmacy', in the phone's maps.",
    ("destination",),
    destination={"type": "string", "description": "The place, e.g. 'Dushanbe airport'."},
)
PHONE_FLASHLIGHT = _spec(
    "phone_flashlight",
    "Turn the phone's flashlight on or off.",
    ("on",),
    on={"type": "boolean", "description": "True to turn it on, false to turn it off."},
)
PHONE_VOLUME = _spec(
    "phone_volume",
    "Change the phone's sound volume.",
    ("change",),
    change={"type": "string", "enum": list(_VOLUME)},
)
PHONE_MEDIA = _spec(
    "phone_media",
    "Pause, resume or skip the music or video playing on the phone.",
    ("key",),
    key={"type": "string", "enum": list(_MEDIA)},
)
PHONE_PLAY = _spec(
    "phone_play",
    "Play music, a song, an artist, a podcast or a video on the phone.",
    ("query",),
    query={"type": "string", "description": "What to play, e.g. 'Sherali Jo'rayev'."},
)
PHONE_CALENDAR = _spec(
    "phone_calendar",
    "Add an event to the phone's calendar; the calendar opens with it filled in.",
    ("title", "start"),
    title={"type": "string", "description": "What the event is."},
    start={
        "type": "string",
        "description": (
            "When, as ISO 8601 with the user's offset, e.g. '2026-11-03T15:00:00+05:00'."
        ),
    },
    minutes={"type": "number", "description": "How long, in minutes; 60 if not said."},
)
PHONE_EMAIL = _spec(
    "phone_email",
    "Write an email on the phone; the mail app opens with it ready to send.",
    ("to", "subject", "body"),
    to={"type": "string", "description": "The email address."},
    subject={"type": "string"},
    body={"type": "string"},
)
PHONE_SETTINGS = _spec(
    "phone_settings",
    "Open a page of the phone's settings, e.g. Wi-Fi or Bluetooth, for the user to switch.",
    ("page",),
    page={"type": "string", "enum": list(_SETTINGS)},
)
PHONE_SEARCH = _spec(
    "phone_search",
    "Search the web on the phone and show the results there.",
    ("query",),
    query={"type": "string"},
)

PHONE_TOOLS = (
    PHONE_CALL,
    PHONE_MESSAGE,
    PHONE_ALARM,
    PHONE_TIMER,
    PHONE_OPEN,
    PHONE_NAVIGATE,
    PHONE_FLASHLIGHT,
    PHONE_VOLUME,
    PHONE_MEDIA,
    PHONE_PLAY,
    PHONE_CALENDAR,
    PHONE_EMAIL,
    PHONE_SETTINGS,
    PHONE_SEARCH,
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


def _choice(call: ToolCall, name: str, allowed: tuple[str, ...]) -> str:
    value = _text(call, name, _MAX_NAME).lower()
    if value not in allowed:
        raise _BadArgumentError(f"'{name}' must be one of {', '.join(allowed)}")
    return value


def _minutes(call: ToolCall, name: str, limit: int, default: float | None = None) -> float:
    value = call.arguments.get(name, default)
    # bool is an int in Python, but "true minutes" is not a duration.
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise _BadArgumentError(f"'{name}' must be a number")
    if not 0 < value <= limit:
        raise _BadArgumentError(f"'{name}' must be more than 0 and at most a day")
    return float(value)


def _call(call: ToolCall) -> tuple[PhoneAction, str]:
    contact = _text(call, "contact", _MAX_NAME)
    return (
        PhoneAction("call", {"contact": contact}),
        f"The app asks the user whether to call {contact}, and calls once they say yes. If "
        f"{contact} is not in their contacts, the app tells them. Say you will call once "
        "they confirm; do not say the call has started.",
    )


def _message(call: ToolCall) -> tuple[PhoneAction, str]:
    contact = _text(call, "contact", _MAX_NAME)
    text = _text(call, "text", _MAX_TEXT)
    app = _text(call, "app", _MAX_NAME, required=False).lower() or "sms"
    if app not in _MESSAGE_APPS:
        raise _BadArgumentError(f"'app' must be one of {', '.join(_MESSAGE_APPS)}")
    sent = "sends the SMS" if app == "sms" else f"opens {app} with the text ready"
    return (
        PhoneAction("message", {"contact": contact, "text": text, "app": app}),
        f"The app reads the message back, asks the user to confirm, then {sent}. Do not say "
        "it has been sent.",
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
    minutes = _minutes(call, "minutes", _MAX_TIMER_MINUTES)
    label = _text(call, "label", _MAX_NAME, required=False)
    return (
        PhoneAction("timer", {"seconds": str(max(1, round(minutes * 60))), "label": label}),
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


def _volume(call: ToolCall) -> tuple[PhoneAction, str]:
    change = _choice(call, "change", _VOLUME)
    return PhoneAction("volume", {"change": change}), f"The volume is changed: {change}."


def _media(call: ToolCall) -> tuple[PhoneAction, str]:
    key = _choice(call, "key", _MEDIA)
    return PhoneAction("media", {"key": key}), f"Pressed {key.replace('_', '/')}."


def _play(call: ToolCall) -> tuple[PhoneAction, str]:
    query = _text(call, "query", _MAX_NAME)
    return PhoneAction("play", {"query": query}), f"The phone starts playing {query}."


def _calendar(call: ToolCall) -> tuple[PhoneAction, str]:
    title = _text(call, "title", _MAX_NAME)
    start = _text(call, "start", 40)
    if not _MOMENT.match(start):
        raise _BadArgumentError("'start' must look like 2026-11-03T15:00:00+05:00")
    minutes = _minutes(call, "minutes", _MAX_EVENT_MINUTES, default=60)
    return (
        PhoneAction("calendar", {"title": title, "start": start, "minutes": str(round(minutes))}),
        f"The calendar opens with '{title}' filled in; the user presses save.",
    )


def _email(call: ToolCall) -> tuple[PhoneAction, str]:
    to = _text(call, "to", _MAX_NAME)
    if "@" not in to:
        raise _BadArgumentError("'to' must be an email address")
    return (
        PhoneAction(
            "email",
            {
                "to": to,
                "subject": _text(call, "subject", _MAX_NAME, required=False),
                "body": _text(call, "body", _MAX_TEXT, required=False),
            },
        ),
        f"The mail app opens with the email to {to} ready; the user presses send.",
    )


def _settings(call: ToolCall) -> tuple[PhoneAction, str]:
    page = _choice(call, "page", _SETTINGS)
    return PhoneAction("settings", {"page": page}), f"The {page} settings are open."


def _search(call: ToolCall) -> tuple[PhoneAction, str]:
    query = _text(call, "query", _MAX_TEXT)
    return PhoneAction("search", {"query": query}), f"The phone shows results for {query}."


_BUILDERS: dict[str, Callable[[ToolCall], tuple[PhoneAction, str]]] = {
    PHONE_CALL.name: _call,
    PHONE_MESSAGE.name: _message,
    PHONE_ALARM.name: _alarm,
    PHONE_TIMER.name: _timer,
    PHONE_OPEN.name: _open,
    PHONE_NAVIGATE.name: _navigate,
    PHONE_FLASHLIGHT.name: _flashlight,
    PHONE_VOLUME.name: _volume,
    PHONE_MEDIA.name: _media,
    PHONE_PLAY.name: _play,
    PHONE_CALENDAR.name: _calendar,
    PHONE_EMAIL.name: _email,
    PHONE_SETTINGS.name: _settings,
    PHONE_SEARCH.name: _search,
}
