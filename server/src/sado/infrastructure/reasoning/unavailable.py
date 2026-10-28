from collections.abc import Sequence

from sado.domain.conversation import Message
from sado.domain.errors import ReasoningUnavailableError


class UnavailableReasoner:
    """Used when no reasoning model is configured, so the rest of Sado keeps working."""

    def reply(self, instructions: str, conversation: Sequence[Message]) -> str:
        raise ReasoningUnavailableError
