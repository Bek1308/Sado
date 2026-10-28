from sado.application.persona import persona_instructions
from sado.domain.errors import EmptyPaperError, UnsupportedPaperError
from sado.domain.language import Language
from sado.domain.vision import DocumentExplainer, Explanation, Paper, PaperKind, paper_kind


def explain_instructions(language: Language, kind: PaperKind) -> str:
    subject = (
        "The user photographed a paper."
        if kind is PaperKind.PHOTO
        else "The user shared a text file."
    )
    return (
        f"{persona_instructions(language)}\n\n"
        f"{subject} Read it and explain in plain words what it is, "
        "its key names, dates and amounts, and what to do next."
    )


class ExplainDocument:
    def __init__(self, explainer: DocumentExplainer) -> None:
        self._explainer = explainer

    def execute(self, paper: Paper, language: Language) -> Explanation:
        if not paper.data:
            raise EmptyPaperError
        kind = paper_kind(paper.media_type)
        if kind is None:
            raise UnsupportedPaperError(paper.media_type)

        explanation = self._explainer.explain(paper, explain_instructions(language, kind))
        return Explanation(text=explanation.text.strip())
