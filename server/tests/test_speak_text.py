import pytest

from sado.application.speak_text import SpeakText
from sado.domain.errors import EmptyTextError, UnknownVoiceError, UnsupportedLanguageError
from sado.domain.language import Language
from tests.fakes import fake_language_pack, fake_voice_catalog


def _speak_text() -> tuple[SpeakText, list[tuple[str, str]]]:
    pack, synthesizer = fake_language_pack(Language.TAJIK)
    return SpeakText({Language.TAJIK: pack}, fake_voice_catalog()), synthesizer.spoken


def test_normalizes_text_and_uses_the_default_voice() -> None:
    speak_text, spoken = _speak_text()

    audio = speak_text.execute("  салом  ", Language.TAJIK)

    assert spoken == [("САЛОМ", "sado")]
    assert audio.wav_bytes == "wav:sado:САЛОМ".encode()


def test_speaks_with_the_requested_voice() -> None:
    speak_text, spoken = _speak_text()

    speak_text.execute("салом", Language.TAJIK, voice_id="opa")

    assert spoken == [("САЛОМ", "opa")]


def test_rejects_unknown_voice() -> None:
    speak_text, _ = _speak_text()

    with pytest.raises(UnknownVoiceError):
        speak_text.execute("салом", Language.TAJIK, voice_id="robot")


def test_rejects_blank_text() -> None:
    speak_text, _ = _speak_text()

    with pytest.raises(EmptyTextError):
        speak_text.execute("   ", Language.TAJIK)


def test_rejects_language_without_pack() -> None:
    speak_text, _ = _speak_text()

    with pytest.raises(UnsupportedLanguageError):
        speak_text.execute("hello", Language.ENGLISH)
