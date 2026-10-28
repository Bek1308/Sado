from sado.application.persona import persona_instructions
from sado.application.transcribe_speech import TranscribeSpeech
from sado.domain.errors import EmptyPaperError, UnsupportedPaperError
from sado.domain.language import Language
from sado.domain.recording import Recording
from sado.domain.vision import (
    DocumentExplainer,
    DocumentReader,
    Explanation,
    Paper,
    PaperKind,
    paper_kind,
)


def explain_instructions(language: Language, kind: PaperKind) -> str:
    subject = {
        PaperKind.PHOTO: "The user photographed a paper.",
        PaperKind.SPOKEN: "The user shared a recording.",
        PaperKind.TEXT: "The user shared a text file.",
        PaperKind.DOCUMENT: "The user shared a document file.",
    }[kind]
    return (
        f"{persona_instructions(language)}\n\n"
        f"{subject} Read it and explain in plain words what it is, "
        "its key names, dates and amounts, and what to do next."
    )


class ExplainDocument:
    def __init__(
        self,
        explainer: DocumentExplainer,
        documents: DocumentReader,
        transcribe: TranscribeSpeech,
    ) -> None:
        self._explainer = explainer
        self._documents = documents
        self._transcribe = transcribe

    def execute(self, paper: Paper, language: Language) -> Explanation:
        if not paper.data:
            raise EmptyPaperError
        kind = paper_kind(paper.media_type)
        if kind in (PaperKind.PHOTO, PaperKind.TEXT):
            explanation = self._explainer.explain(paper, explain_instructions(language, kind))
        elif kind is PaperKind.DOCUMENT:
            text = self._documents.read(paper)
            explanation = self._explainer.explain(
                _text_paper(text), explain_instructions(language, kind)
            )
        elif kind is PaperKind.SPOKEN:
            recording = Recording(data=paper.data, media_type=paper.media_type)
            transcript = self._transcribe.execute(recording, language)
            explanation = self._explainer.explain(
                _text_paper(transcript.text), explain_instructions(language, kind)
            )
        else:
            raise UnsupportedPaperError(paper.media_type)
        return Explanation(text=explanation.text.strip())


def _text_paper(text: str) -> Paper:
    return Paper(data=text.encode("utf-8"), media_type="text/plain")
