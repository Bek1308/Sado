from collections.abc import Sequence

from sado.application.persona import persona_instructions
from sado.domain.conversation import Message, ReasoningModel, Speaker
from sado.domain.errors import NothingToAnswerError
from sado.domain.language import Language


class Converse:
    def __init__(self, reasoning_model: ReasoningModel) -> None:
        self._reasoning_model = reasoning_model

    def execute(self, conversation: Sequence[Message], language: Language) -> str:
        if not conversation:
            raise NothingToAnswerError
        last = conversation[-1]
        if last.speaker is not Speaker.USER or not last.text.strip():
            raise NothingToAnswerError

        reply = self._reasoning_model.reply(persona_instructions(language), conversation)
        return reply.strip()
