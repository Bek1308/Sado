import pytest

from sado.application.explain_document import ExplainDocument
from sado.domain.errors import EmptyPaperError, UnsupportedPaperError
from sado.domain.language import Language
from sado.domain.vision import Explanation, Paper
from tests.fakes import CannedExplainer


def test_explains_a_photo_in_the_requested_language() -> None:
    explainer = CannedExplainer()
    paper = Paper(data=b"paper", media_type="image/jpeg")

    explanation = ExplainDocument(explainer).execute(paper, Language.TAJIK)

    assert explanation == Explanation("This is a work permit notice.")
    seen_paper, instructions = explainer.seen[0]
    assert seen_paper == paper
    assert "Tajik" in instructions
    assert "photographed" in instructions


def test_explains_a_text_file() -> None:
    explainer = CannedExplainer()
    paper = Paper(data=b"Work permit notice", media_type="text/plain")

    explanation = ExplainDocument(explainer).execute(paper, Language.UZBEK)

    assert explanation == Explanation("This is a work permit notice.")
    _, instructions = explainer.seen[0]
    assert "text file" in instructions


def test_rejects_an_empty_upload() -> None:
    explainer = CannedExplainer()
    paper = Paper(data=b"", media_type="image/jpeg")

    with pytest.raises(EmptyPaperError):
        ExplainDocument(explainer).execute(paper, Language.TAJIK)

    assert explainer.seen == []


def test_rejects_an_unreadable_file_type() -> None:
    explainer = CannedExplainer()
    paper = Paper(data=b"sound", media_type="audio/mpeg")

    with pytest.raises(UnsupportedPaperError):
        ExplainDocument(explainer).execute(paper, Language.TAJIK)

    assert explainer.seen == []


def test_trims_the_explanation() -> None:
    explainer = CannedExplainer(text="  Notice. \n")
    paper = Paper(data=b"paper", media_type="image/jpeg")

    explanation = ExplainDocument(explainer).execute(paper, Language.ENGLISH)

    assert explanation == Explanation("Notice.")
