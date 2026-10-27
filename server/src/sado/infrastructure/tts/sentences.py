import re

_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+")
_CLAUSE_END = re.compile(r"(?<=[,;:])\s+")


def split_into_sentences(text: str, max_chars: int = 220) -> list[str]:
    """Splits text into sentences, breaking overly long ones at commas.

    OmniVoice keeps its voice and rhythm best on sentence-sized inputs.
    """
    sentences: list[str] = []
    for sentence in _SENTENCE_END.split(text.strip()):
        if len(sentence) <= max_chars:
            sentences.append(sentence)
            continue
        current = ""
        for clause in _CLAUSE_END.split(sentence):
            if current and len(current) + len(clause) + 1 > max_chars:
                sentences.append(current)
                current = clause
            else:
                current = f"{current} {clause}".strip()
        sentences.append(current)
    return [sentence for sentence in sentences if sentence]
