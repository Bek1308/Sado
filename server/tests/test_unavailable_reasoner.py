import pytest

from sado.domain.conversation import Message, Speaker
from sado.domain.errors import ReasoningUnavailableError
from sado.infrastructure.reasoning.unavailable import UnavailableReasoner


def test_reports_that_sado_cannot_think() -> None:
    with pytest.raises(ReasoningUnavailableError):
        UnavailableReasoner().reply("instructions", [Message(Speaker.USER, "salom")])
