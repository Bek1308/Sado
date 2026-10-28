from collections.abc import Sequence

from sado.domain.conversation import Message, ModelTurn, ToolSpec, ToolStep
from sado.domain.errors import ReasoningUnavailableError
from sado.domain.vision import Explanation, Paper


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

    def explain(self, paper: Paper, instructions: str) -> Explanation:
        raise ReasoningUnavailableError
