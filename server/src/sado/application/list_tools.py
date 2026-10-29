"""Tools that let Sado keep the user's lists while talking."""

from sado.application.lists import Lists
from sado.domain.conversation import ToolCall, ToolResult, ToolSpec
from sado.domain.errors import SadoError

_LIST_NAME = {
    "type": "string",
    "description": (
        "Which list, as a short name in the user's language, e.g. 'xarid' or 'shopping'. "
        "Reuse the name the user already has for that list."
    ),
}
_ENTRIES = {
    "type": "array",
    "items": {"type": "string"},
    "description": "One entry per item, short, in the user's language, e.g. ['non', 'sut'].",
}

ADD_TO_LIST = ToolSpec(
    name="add_to_list",
    description="Add items to one of the user's lists, such as shopping or to-do.",
    parameters={
        "type": "object",
        "properties": {"list": _LIST_NAME, "items": _ENTRIES},
        "required": ["list", "items"],
    },
)
REMOVE_FROM_LIST = ToolSpec(
    name="remove_from_list",
    description="Remove items the user bought, did or no longer wants from a list.",
    parameters={
        "type": "object",
        "properties": {"list": _LIST_NAME, "items": _ENTRIES},
        "required": ["list", "items"],
    },
)
READ_LIST = ToolSpec(
    name="read_list",
    description="Read what is on one of the user's lists.",
    parameters={
        "type": "object",
        "properties": {"list": _LIST_NAME},
        "required": ["list"],
    },
)

LIST_TOOLS = (ADD_TO_LIST, REMOVE_FROM_LIST, READ_LIST)


def run_list_tool(lists: Lists, call: ToolCall) -> tuple[ToolResult, bool]:
    """Runs one list tool; also says whether any list changed, so the app can refresh."""
    name = call.arguments.get("list")
    if not isinstance(name, str):
        return ToolResult(call, "Nothing done: 'list' must be text."), False
    try:
        if call.name == READ_LIST.name:
            items = lists.read(name)
            return ToolResult(call, _contents(items)), False
        entries = _entries(call)
        if call.name == ADD_TO_LIST.name:
            added = lists.add(name, entries)
            done = f"Added: {', '.join(item.text for item in added) or 'nothing new'}."
            return ToolResult(call, f"{done} {_contents(lists.read(name))}"), bool(added)
        removed = lists.remove(name, entries)
        done = f"Removed: {', '.join(removed) or 'nothing matched'}."
        return ToolResult(call, f"{done} {_contents(lists.read(name))}"), bool(removed)
    except SadoError as error:
        return ToolResult(call, f"Nothing done: {error}."), False


def _entries(call: ToolCall) -> list[str]:
    items = call.arguments.get("items")
    if isinstance(items, str):
        return [items]
    if isinstance(items, list):
        return [item for item in items if isinstance(item, str)]
    return []


def _contents(items: list[str]) -> str:
    return f"The list now has: {', '.join(items)}." if items else "The list is empty."
