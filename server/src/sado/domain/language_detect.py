"""Guess which of Sado's languages a transcript is written in.

The speech recognizer needs an explicit language, so auto-detection transcribes
with each language and keeps the transcript whose own words match the requested
language. This module scores the words: Tajik-only letters decide immediately,
otherwise distinctive words vote, and bare Cyrillic falls back to Russian.
"""

import re

from sado.domain.language import Language

_TAJIK_LETTERS = frozenset("ғӣҷҳқӯҒӢҶҲҚӮ")

_WORDS: dict[Language, frozenset[str]] = {
    Language.TAJIK: frozenset(
        [
            "ман",
            "ту",
            "вай",
            "мо",
            "шумо",
            "ва",
            "дар",
            "ба",
            "бо",
            "аз",
            "ки",
            "ин",
            "он",
            "чӣ",
            "чист",
            "хуб",
            "бале",
            "не",
            "салом",
            "раҳмат",
            "хайр",
            "лутфан",
            "оё",
            "кадом",
            "чун",
            "агар",
            "лекин",
            "хеле",
            "ҳам",
            "куҷо",
            "кай",
            "чаро",
        ]
    ),
    Language.UZBEK: frozenset(
        [
            "men",
            "sen",
            "u",
            "biz",
            "siz",
            "ular",
            "va",
            "bu",
            "shu",
            "qanday",
            "nima",
            "bilan",
            "uchun",
            "kerak",
            "emas",
            "salom",
            "assalomu",
            "alaykum",
            "rahmat",
            "xayr",
            "iltimos",
            "ha",
            "yoq",
            "qayer",
            "qachon",
            "nega",
            "agar",
            "lekin",
            "juda",
            "ham",
            "mening",
            "sening",
            "menga",
            "senga",
            "мен",
            "сен",
            "у",
            "биз",
            "сиз",
            "улар",
            "бу",
            "шу",
            "қандай",
            "нима",
            "билан",
            "учун",
            "керак",
            "эмас",
            "салом",
            "раҳмат",
            "хайр",
            "илтимос",
            "қаер",
            "қачон",
            "нега",
        ]
    ),
    Language.RUSSIAN: frozenset(
        [
            "я",
            "ты",
            "он",
            "она",
            "мы",
            "вы",
            "они",
            "и",
            "в",
            "на",
            "что",
            "как",
            "это",
            "да",
            "нет",
            "привет",
            "здравствуй",
            "спасибо",
            "пожалуйста",
            "где",
            "когда",
            "почему",
            "если",
            "но",
            "очень",
            "меня",
            "тебя",
            "хорошо",
            "пока",
            "здравствуйте",
            "до",
        ]
    ),
    Language.ENGLISH: frozenset(
        [
            "i",
            "you",
            "he",
            "she",
            "we",
            "they",
            "the",
            "is",
            "are",
            "was",
            "and",
            "what",
            "how",
            "this",
            "that",
            "yes",
            "no",
            "hello",
            "hi",
            "thanks",
            "thank",
            "please",
            "where",
            "when",
            "why",
            "if",
            "but",
            "very",
            "my",
            "me",
        ]
    ),
}

_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)

_CYRILLIC_FALLBACK_FRACTION = 0.3


def _cyrillic_fraction(text: str) -> float:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return 0.0
    cyrillic = sum(1 for char in letters if "Ѐ" <= char <= "џ")
    return cyrillic / len(letters)


def detect_language(text: str) -> Language | None:
    """Detect the language of [text], or return `None` when it carries no signal."""
    votes = dict.fromkeys(Language, 0)
    for word in _WORD.findall(text.lower()):
        for language, known in _WORDS.items():
            if word in known:
                votes[language] += 1

    # Uzbek Cyrillic shares ғ/қ/ҳ with Tajik, so the letters alone only win
    # when Tajik words are at least as strong as Uzbek ones.
    if (
        any(char in _TAJIK_LETTERS for char in text)
        and votes[Language.TAJIK] >= votes[Language.UZBEK]
    ):
        return Language.TAJIK

    best = max(Language, key=lambda language: votes[language])
    if votes[best] > 0:
        return best
    if _cyrillic_fraction(text) > _CYRILLIC_FALLBACK_FRACTION:
        return Language.RUSSIAN
    return None
