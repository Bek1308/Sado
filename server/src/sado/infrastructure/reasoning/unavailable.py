from collections.abc import Sequence

from sado.domain.conversation import Message, ModelTurn, ToolSpec, ToolStep
from sado.domain.errors import ReasoningUnavailableError


class UnavailableReasoner:
    """Used when no reasoning model is configured, so the rest of Sado keeps working."""

    def respond(
        self,
        instructions: str,
        conversation: Sequence[Message],
        tools: Sequence[ToolSpec],
        steps: Sequence[ToolStep],
    ) -> ModelTurn:
        raise ReasoningUnavailableError
