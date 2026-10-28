from collections.abc import Sequence
from dataclasses import dataclass, field

from sado.application.memories import Memories
from sado.application.persona import persona_instructions
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


@dataclass(frozen=True, slots=True)
class Reply:
    text: str
    remembered: tuple[str, ...] = field(default=())
    """Facts Sado saved while answering, so the app can show them."""


class Converse:
    # Sado only needs a couple of tool rounds; more means the model is stuck in a loop.
    _MAX_TOOL_STEPS = 3

    def __init__(self, reasoning_model: ReasoningModel, memories: Memories | None = None) -> None:
        self._reasoning_model = reasoning_model
        self._memories = memories

    def execute(self, conversation: Sequence[Message], language: Language) -> Reply:
        if not conversation:
            raise NothingToAnswerError
        last = conversation[-1]
        if last.speaker is not Speaker.USER or not last.text.strip():
            raise NothingToAnswerError

        recalled = self._memories.recall(last.text) if self._memories else []
        instructions = persona_instructions(language, [memory.text for memory in recalled])
        tools = [REMEMBER] if self._memories else []
        steps: list[ToolStep] = []
        remembered: list[str] = []

        for _ in range(self._MAX_TOOL_STEPS + 1):
            turn = self._reasoning_model.respond(instructions, conversation, tools, steps)
            if isinstance(turn, Answer):
                return Reply(text=turn.text.strip(), remembered=tuple(remembered))
            steps.append(
                ToolStep(results=tuple(self._run(call, remembered) for call in turn.calls))
            )
        raise ReasoningUnavailableError

    def _run(self, call: ToolCall, remembered: list[str]) -> ToolResult:
        if call.name != REMEMBER.name or self._memories is None:
            return ToolResult(call, f"Unknown tool '{call.name}'.")
        fact = call.arguments.get("fact")
        if not isinstance(fact, str):
            return ToolResult(call, "Nothing saved: 'fact' must be text.")
        try:
            memory = self._memories.remember(fact)
        except SadoError as error:
            return ToolResult(call, f"Nothing saved: {error}.")
        remembered.append(memory.text)
        return ToolResult(call, "Saved.")
