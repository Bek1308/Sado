"""Measures how understandable Sado's voice is, without a human listener.

Each sentence is spoken by the running server (`/speech`), then heard again by Meta
Omnilingual ASR (`/transcriptions`). The word error rate between what Sado was asked
to say and what the recognizer heard is a proxy for how clearly Sado pronounces it:
numbers read the wrong way, swallowed endings or a foreign accent all show up here.

Usage (server and ASR worker running):
    uv run python scripts/check_pronunciation.py [--url http://localhost:8000] [--voice sado]
"""

import argparse
import re
import sys
from dataclasses import dataclass

import httpx

from sado.domain.speech import TextNormalizer
from sado.infrastructure.languages.english import build_english_normalizer
from sado.infrastructure.languages.russian import build_russian_normalizer
from sado.infrastructure.languages.tajik import build_tajik_normalizer
from sado.infrastructure.languages.uzbek import build_uzbek_normalizer

# Both sides go through Sado's own normalizer, so "245" and "ikki yuz qirq besh" count
# as the same words and only real mispronunciations remain.
NORMALIZERS: dict[str, TextNormalizer] = {
    "uz": build_uzbek_normalizer(),
    "tg": build_tajik_normalizer(),
    "ru": build_russian_normalizer(),
    "en": build_english_normalizer(),
}

SENTENCES = {
    "uz": [
        "Salom, bugun havo juda yaxshi.",
        "Ertaga soat 9 da shifokorga borishim kerak.",
        "Qizim Malika 12-mayda tug'ilgan.",
        "Elektr uchun 245 so'm to'lash kerak.",
        "Men o'zbek tilida gaplashaman.",
    ],
    "tg": [
        "Салом, имрӯз ҳаво хеле хуб аст.",
        "Пагоҳ соати 9 ба духтур меравам.",
        "Қарз барои барқ 245 сомонӣ аст.",
        "Ман бо забони тоҷикӣ гап мезанам.",
    ],
    "ru": [
        "Привет, сегодня отличная погода.",
        "Завтра в 9 часов мне нужно к врачу.",
        "Долг за электричество составляет 245 сомони.",
    ],
    "en": [
        "Hello, the weather is lovely today.",
        "Remind me to call my mother at 8 tonight.",
        "The bill is 245 dollars and is due on the 15th.",
    ],
}

_APOSTROPHES = re.compile(r"[ʻʼ‘’`´]")
_NOT_WORD = re.compile(r"[^\w']+")


def words(text: str, language: str) -> list[str]:
    spoken = NORMALIZERS[language].normalize(text)
    cleaned = _APOSTROPHES.sub("'", spoken.casefold()).replace("-", " ")
    return [word for word in _NOT_WORD.split(cleaned) if word]


def word_error_rate(expected: list[str], heard: list[str]) -> float:
    if not expected:
        return 0.0 if not heard else 1.0
    previous = list(range(len(heard) + 1))
    for i, expected_word in enumerate(expected, start=1):
        current = [i]
        for j, heard_word in enumerate(heard, start=1):
            cost = 0 if expected_word == heard_word else 1
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost))
        previous = current
    return previous[-1] / len(expected)


@dataclass(frozen=True)
class Check:
    language: str
    sentence: str
    heard: str
    error_rate: float


def check(client: httpx.Client, language: str, sentence: str, voice: str) -> Check:
    spoken = client.post("/speech", json={"text": sentence, "language": language, "voice": voice})
    spoken.raise_for_status()
    heard = client.post(
        "/transcriptions",
        files={"audio": ("sado.wav", spoken.content, "audio/wav")},
        data={"language": language},
    )
    heard.raise_for_status()
    text = str(heard.json()["text"])
    error_rate = word_error_rate(words(sentence, language), words(text, language))
    return Check(language, sentence, text, error_rate)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--voice", default="sado")
    args = parser.parse_args()

    with httpx.Client(base_url=args.url, timeout=180) as client:
        for language, sentences in SENTENCES.items():
            results = [check(client, language, sentence, args.voice) for sentence in sentences]
            average = sum(result.error_rate for result in results) / len(results)
            print(f"\n[{language}] word error rate {average:.0%}")
            for result in results:
                mark = "ok " if result.error_rate == 0 else f"{result.error_rate:.0%}"
                print(f"  {mark:>4}  {result.sentence}")
                if result.error_rate:
                    print(f"        heard: {result.heard}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
