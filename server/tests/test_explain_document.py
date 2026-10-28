import pytest

from sado.application.explain_document import ExplainDocument
from sado.application.transcribe_speech import TranscribeSpeech
from sado.domain.errors import EmptyPaperError, UnsupportedPaperError
from sado.domain.language import Language
from sado.domain.vision import Explanation, Paper
from sado.infrastructure.documents.readers import CompositeDocumentReader
from tests.fakes import CannedExplainer, fake_language_pack
from tests.test_readers import sample_docx_bytes

_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _use_case(explainer: CannedExplainer | None = None) -> ExplainDocument:
    pack, _ = fake_language_pack(Language.TAJIK)
    return ExplainDocument(
        explainer or CannedExplainer(),
        CompositeDocumentReader(),
        TranscribeSpeech({Language.TAJIK: pack}),
    )


def test_explains_a_photo_in_the_requested_language() -> None:
    explainer = CannedExplainer()
    paper = Paper(data=b"paper", media_type="image/jpeg")

    explanation = _use_case(explainer).execute(paper, Language.TAJIK)

    assert explanation == Explanation("This is a work permit notice.")
    seen_paper, instructions = explainer.seen[0]
    assert seen_paper == paper
    assert "Tajik" in instructions
    assert "photographed" in instructions


def test_explains_a_text_file() -> None:
    explainer = CannedExplainer()
    paper = Paper(data=b"Work permit notice", media_type="text/plain")

    explanation = _use_case(explainer).execute(paper, Language.UZBEK)

    assert explanation == Explanation("This is a work permit notice.")
    _, instructions = explainer.seen[0]
    assert "text file" in instructions


def test_explains_a_document_file_by_reading_its_text() -> None:
    explainer = CannedExplainer()
    paper = Paper(data=sample_docx_bytes(), media_type=_DOCX)

    explanation = _use_case(explainer).execute(paper, Language.UZBEK)

    assert explanation == Explanation("This is a work permit notice.")
    seen_paper, instructions = explainer.seen[0]
    assert seen_paper.media_type == "text/plain"
    assert seen_paper.data == b"Permit 42\nexpires soon"
    assert "document file" in instructions


def test_explains_a_recording_by_transcribing_it_first() -> None:
    explainer = CannedExplainer()
    paper = Paper(data=b"salom", media_type="audio/webm")

    explanation = _use_case(explainer).execute(paper, Language.TAJIK)

    assert explanation == Explanation("This is a work permit notice.")
    seen_paper, instructions = explainer.seen[0]
    assert seen_paper.data == b"salom"
    assert "recording" in instructions


def test_rejects_an_empty_upload() -> None:
    explainer = CannedExplainer()
    paper = Paper(data=b"", media_type="image/jpeg")

    with pytest.raises(EmptyPaperError):
        _use_case(explainer).execute(paper, Language.TAJIK)

    assert explainer.seen == []


def test_rejects_an_unreadable_file_type() -> None:
    explainer = CannedExplainer()
    paper = Paper(data=b"archived", media_type="application/zip")

    with pytest.raises(UnsupportedPaperError):
        _use_case(explainer).execute(paper, Language.TAJIK)

    assert explainer.seen == []


def test_trims_the_explanation() -> None:
    explainer = CannedExplainer(text="  Notice. \n")
    paper = Paper(data=b"paper", media_type="image/jpeg")

    explanation = _use_case(explainer).execute(paper, Language.ENGLISH)

    assert explanation == Explanation("Notice.")
