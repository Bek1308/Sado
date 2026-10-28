import pytest

from sado.domain.conversation import Message, Speaker
from sado.domain.errors import ReasoningUnavailableError
from sado.domain.vision import Paper
from sado.infrastructure.reasoning.unavailable import UnavailableReasoner


def test_reports_that_sado_cannot_think() -> None:
    with pytest.raises(ReasoningUnavailableError):
        UnavailableReasoner().respond("instructions", [Message(Speaker.USER, "salom")], [], [])


def test_reports_that_sado_cannot_read_papers() -> None:
    paper = Paper(data=b"image", media_type="image/jpeg")

    with pytest.raises(ReasoningUnavailableError):
        UnavailableReasoner().explain(paper, "instructions")
