"""Emotional cues written inline in text, e.g. "Voy! [surprise] Rostdanmi? [laugh]".

The cues are language-neutral, so Sado's agent can use them in any language; each speech
engine decides how (or whether) it can perform them.
"""

import re
from enum import StrEnum


class Expression(StrEnum):
    LAUGH = "laugh"
    SIGH = "sigh"
    SURPRISE = "surprise"
    QUESTION = "question"
    HMM = "hmm"


EXPRESSION_CUE = re.compile(
    r"\[(" + "|".join(expression.value for expression in Expression) + r")\]"
)


def split_expression_cues(text: str) -> list[str | Expression]:
    """Splits text into plain fragments and the expression cues between them."""
    parts: list[str | Expression] = []
    position = 0
    for match in EXPRESSION_CUE.finditer(text):
        if match.start() > position:
            parts.append(text[position : match.start()])
        parts.append(Expression(match[1]))
        position = match.end()
    if position < len(text):
        parts.append(text[position:])
    return parts


def remove_expression_cues(text: str) -> str:
    return re.sub(r"\s{2,}", " ", EXPRESSION_CUE.sub("", text)).strip()
