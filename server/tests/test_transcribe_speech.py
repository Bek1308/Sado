from typing import cast

import pytest

from sado.application.transcribe_speech import TranscribeSpeech
from sado.domain.errors import EmptyRecordingError, UnsupportedLanguageError
from sado.domain.language import Language
from sado.domain.recording import Recording
from tests.fakes import EchoRecognizer, fake_language_pack


def _transcribe_speech() -> TranscribeSpeech:
    pack, _ = fake_language_pack(Language.UZBEK)
    return TranscribeSpeech({Language.UZBEK: pack})


def test_returns_what_the_language_recognizer_heard() -> None:
    transcript = _transcribe_speech().execute(
        Recording(b"salom dunyo", "audio/wav"), Language.UZBEK
    )

    assert transcript.text == "salom dunyo"


def test_rejects_an_empty_recording() -> None:
    with pytest.raises(EmptyRecordingError):
        _transcribe_speech().execute(Recording(b"", "audio/wav"), Language.UZBEK)


def test_rejects_a_language_without_pack() -> None:
    with pytest.raises(UnsupportedLanguageError):
        _transcribe_speech().execute(Recording(b"hello", "audio/wav"), Language.ENGLISH)


def test_auto_detects_the_spoken_language() -> None:
    pack_en, _ = fake_language_pack(Language.ENGLISH)
    pack_uz, _ = fake_language_pack(Language.UZBEK)
    speech = TranscribeSpeech({Language.ENGLISH: pack_en, Language.UZBEK: pack_uz})

    transcript, language = speech.execute_auto(Recording(b"salom sen yaxshimisan", "audio/wav"))

    assert (transcript.text, language) == ("salom sen yaxshimisan", Language.UZBEK)


def test_auto_remembers_the_last_language_first() -> None:
    pack_en, _ = fake_language_pack(Language.ENGLISH)
    pack_uz, _ = fake_language_pack(Language.UZBEK)
    speech = TranscribeSpeech({Language.ENGLISH: pack_en, Language.UZBEK: pack_uz})
    recording = Recording(b"salom sen yaxshimisan", "audio/wav")

    speech.execute_auto(recording)
    english = cast(EchoRecognizer, pack_en.recognizer)
    heard_before = len(english.heard)
    speech.execute_auto(recording)

    assert len(english.heard) == heard_before


def test_auto_falls_back_to_the_detected_language() -> None:
    pack, _ = fake_language_pack(Language.TAJIK)
    speech = TranscribeSpeech({Language.TAJIK: pack})

    transcript, language = speech.execute_auto(Recording("привет как дела".encode(), "audio/wav"))

    assert (transcript.text, language) == ("привет как дела", Language.RUSSIAN)


def test_auto_rejects_an_empty_recording() -> None:
    with pytest.raises(EmptyRecordingError):
        _transcribe_speech().execute_auto(Recording(b"", "audio/wav"))
