import pytest

from sado.application.speak_text import SpeakText
from sado.domain.errors import EmptyTextError, UnsupportedLanguageError
from sado.domain.language import Language
from tests.fakes import fake_language_pack


def test_normalizes_text_before_synthesizing_it() -> None:
    pack, synthesizer = fake_language_pack(Language.TAJIK)
    speak_text = SpeakText({Language.TAJIK: pack})

    audio = speak_text.execute("  салом  ", Language.TAJIK)

    assert synthesizer.spoken_texts == ["САЛОМ"]
    assert audio.wav_bytes == "wav:САЛОМ".encode()


def test_rejects_blank_text() -> None:
    pack, _ = fake_language_pack(Language.TAJIK)

    with pytest.raises(EmptyTextError):
        SpeakText({Language.TAJIK: pack}).execute("   ", Language.TAJIK)


def test_rejects_language_without_pack() -> None:
    pack, _ = fake_language_pack(Language.TAJIK)

    with pytest.raises(UnsupportedLanguageError):
        SpeakText({Language.TAJIK: pack}).execute("hello", Language.ENGLISH)
