from collections.abc import Sequence

from sado.application.memories import Memories
from sado.application.persona import persona_instructions
from sado.domain.conversation import Message, ReasoningModel, Speaker
from sado.domain.errors import NothingToAnswerError
from sado.domain.language import Language


class Converse:
    def __init__(self, reasoning_model: ReasoningModel, memories: Memories | None = None) -> None:
        self._reasoning_model = reasoning_model
        self._memories = memories

    def execute(self, conversation: Sequence[Message], language: Language) -> str:
        if not conversation:
            raise NothingToAnswerError
        last = conversation[-1]
        if last.speaker is not Speaker.USER or not last.text.strip():
            raise NothingToAnswerError

        recalled = self._memories.recall(last.text) if self._memories else []
        instructions = persona_instructions(language, [memory.text for memory in recalled])
        reply = self._reasoning_model.reply(instructions, conversation)
        return reply.strip()
