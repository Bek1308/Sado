from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, timezone, tzinfo

from sado.application.list_tools import LIST_TOOLS, run_list_tool
from sado.application.lists import Lists
from sado.application.memories import Memories
from sado.application.persona import persona_instructions
from sado.application.reminders import Reminders
from sado.domain.conversation import (
    Answer,
    Message,
    ReasoningModel,
    Speaker,
    ToolCall,
    ToolResult,
    ToolSpec,
    ToolStep,
)
from sado.domain.errors import NothingToAnswerError, ReasoningUnavailableError, SadoError
from sado.domain.language import Language
from sado.domain.mode import Mode
from sado.domain.reminder import Reminder
from sado.domain.search import WebSearch

REMEMBER = ToolSpec(
    name="remember",
    description=(
        "Save a fact for later: a name, date, preference, plan or anything the user asks "
        "you to remember. Use it when the user asks you to remember something or shares a "
        "lasting personal fact. Do not save small talk."
    ),
    parameters={
        "type": "object",
        "properties": {
            "fact": {
                "type": "string",
                "description": (
                    "The fact as one short standalone sentence in the user's language, "
                    "e.g. 'The user's daughter Malika was born on 12 May.'"
                ),
            }
        },
        "required": ["fact"],
    },
)


REMIND = ToolSpec(
    name="remind",
    description=(
        "Set a reminder: Sado will tell the user `text` at `due`. Use it when the user "
        "asks to be reminded of something. Compute `due` from the user's local time above "
        "and keep the user's UTC offset; never ask what time it is now."
    ),
    parameters={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "What to tell the user, e.g. 'Call mother'.",
            },
            "due": {
                "type": "string",
                "description": (
                    "When, as ISO 8601 with the user's offset, e.g. '2026-10-30T09:00:00+05:00'."
                ),
            },
        },
        "required": ["text", "due"],
    },
)


SEARCH_WEB = ToolSpec(
    name="search_web",
    description=(
        "Look something up on the live web: weather, news, prices, opening hours, "
        "exchange rates or any fact that may have changed since you were trained. "
        "Do not search for things you already know or for the user's own memories."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "A short search query, best in English, e.g. 'weather Dushanbe today'."
                ),
            }
        },
        "required": ["query"],
    },
)


def reminder_label(reminder: Reminder, zone: tzinfo = UTC) -> str:
    """How a reminder is shown to the user and back to the model, on the user's clock."""
    return f"{reminder.text} ({reminder.due_at.astimezone(zone):%d %b, %H:%M})"


_DONE = {
    Language.UZBEK: "Bo'ldi.",
    Language.TAJIK: "Шуд.",
    Language.RUSSIAN: "Готово.",
    Language.ENGLISH: "Done.",
}


@dataclass(frozen=True, slots=True)
class Reply:
    text: str
    remembered: tuple[str, ...] = field(default=())
    """Facts Sado saved while answering, so the app can show them."""
    reminded: tuple[str, ...] = field(default=())
    """Reminders Sado set while answering, so the app can show them."""
    lists_changed: bool = False
    """Whether Sado changed a list while answering, so the app can refresh it."""


@dataclass(slots=True)
class _Outcome:
    """What one answer's tool calls changed; fresh per request, never shared."""

    remembered: list[str] = field(default_factory=list)
    reminded: list[str] = field(default_factory=list)
    lists_changed: bool = False

    @property
    def acted(self) -> bool:
        return bool(self.remembered or self.reminded or self.lists_changed)


class Converse:
    # Sado only needs a couple of tool rounds; more means the model is stuck in a loop.
    _MAX_TOOL_STEPS = 3

    def __init__(
        self,
        reasoning_model: ReasoningModel,
        memories: Memories | None = None,
        reminders: Reminders | None = None,
        web_search: WebSearch | None = None,
        lists: Lists | None = None,
    ) -> None:
        self._reasoning_model = reasoning_model
        self._memories = memories
        self._reminders = reminders
        self._web_search = web_search
        self._lists = lists

    def execute(
        self,
        conversation: Sequence[Message],
        language: Language,
        mode: Mode = Mode.PERSONAL,
        utc_offset: timedelta = timedelta(0),
    ) -> Reply:
        if not conversation:
            raise NothingToAnswerError
        last = conversation[-1]
        if last.speaker is not Speaker.USER or not last.text.strip():
            raise NothingToAnswerError

        zone = timezone(utc_offset)
        moment = datetime.now(zone)
        recalled = self._memories.recall(last.text) if self._memories else []
        due = self._reminders.due(moment) if self._reminders else []
        instructions = persona_instructions(
            language,
            [memory.text for memory in recalled],
            [reminder_label(reminder, zone) for reminder in due],
            mode,
            moment,
        )
        tools = [
            *([REMEMBER] if self._memories else []),
            *([REMIND] if self._reminders else []),
            *([SEARCH_WEB] if self._web_search else []),
            *(LIST_TOOLS if self._lists else ()),
        ]
        steps: list[ToolStep] = []
        outcome = _Outcome()

        for _ in range(self._MAX_TOOL_STEPS + 1):
            turn = self._reasoning_model.respond(instructions, conversation, tools, steps)
            if isinstance(turn, Answer):
                text = turn.text.strip() or self._fallback_text(language, outcome)
                if self._reminders is not None:
                    self._reminders.delivered(due, moment)
                return Reply(
                    text=text,
                    remembered=tuple(outcome.remembered),
                    reminded=tuple(outcome.reminded),
                    lists_changed=outcome.lists_changed,
                )
            steps.append(
                ToolStep(results=tuple(self._run(call, outcome, zone) for call in turn.calls))
            )
        raise ReasoningUnavailableError

    @staticmethod
    def _fallback_text(language: Language, outcome: _Outcome) -> str:
        # Models often go quiet right after a tool call; a short confirmation beats silence.
        if outcome.acted:
            return _DONE[language]
        raise ReasoningUnavailableError

    def _run(self, call: ToolCall, outcome: _Outcome, zone: tzinfo) -> ToolResult:
        if call.name == REMEMBER.name and self._memories is not None:
            return self._save_memory(self._memories, call, outcome)
        if call.name == REMIND.name and self._reminders is not None:
            return self._set_reminder(self._reminders, call, outcome, zone)
        if call.name == SEARCH_WEB.name and self._web_search is not None:
            return self._search(self._web_search, call)
        if self._lists is not None and call.name in _LIST_TOOL_NAMES:
            result, changed = run_list_tool(self._lists, call)
            outcome.lists_changed = outcome.lists_changed or changed
            return result
        return ToolResult(call, f"Unknown tool '{call.name}'.")

    @staticmethod
    def _save_memory(memories: Memories, call: ToolCall, outcome: _Outcome) -> ToolResult:
        fact = call.arguments.get("fact")
        if not isinstance(fact, str):
            return ToolResult(call, "Nothing saved: 'fact' must be text.")
        try:
            memory = memories.remember(fact)
        except SadoError as error:
            return ToolResult(call, f"Nothing saved: {error}.")
        outcome.remembered.append(memory.text)
        return ToolResult(call, "Saved.")

    @staticmethod
    def _search(web_search: WebSearch, call: ToolCall) -> ToolResult:
        query = call.arguments.get("query")
        if not isinstance(query, str) or not query.strip():
            return ToolResult(call, "Nothing searched: 'query' must be text.")
        try:
            return ToolResult(call, web_search.search(query.strip()))
        except SadoError as error:
            return ToolResult(call, f"Search failed: {error}. Say you could not check it now.")

    @staticmethod
    def _set_reminder(
        reminders: Reminders, call: ToolCall, outcome: _Outcome, zone: tzinfo
    ) -> ToolResult:
        text = call.arguments.get("text")
        due = call.arguments.get("due")
        if not isinstance(text, str) or not isinstance(due, str):
            return ToolResult(call, "Nothing set: 'text' and 'due' must be text.")
        try:
            reminder = reminders.remind(text, due, zone)
        except SadoError as error:
            return ToolResult(call, f"Nothing set: {error}.")
        outcome.reminded.append(reminder_label(reminder, zone))
        return ToolResult(call, "Set.")


_LIST_TOOL_NAMES = frozenset(tool.name for tool in LIST_TOOLS)
