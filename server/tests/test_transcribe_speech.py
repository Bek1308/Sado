import pytest

from sado.application.transcribe_speech import TranscribeSpeech
from sado.domain.errors import EmptyRecordingError, UnsupportedLanguageError
from sado.domain.language import Language
from sado.domain.recording import Recording
from tests.fakes import fake_language_pack


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
