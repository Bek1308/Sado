import httpx
import pytest

from sado.domain.errors import SpeechRecognitionUnavailableError
from sado.domain.language import Language
from sado.domain.recording import Recording, Transcript
from sado.infrastructure.asr.muse_listener import FallbackRecognizer, MuseListener

_WAV = Recording(b"RIFF....WAVE", "audio/wav")


def _listener(*answers: str) -> tuple[MuseListener, list[int]]:
    calls: list[int] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        answer = answers[min(len(calls), len(answers)) - 1]
        return httpx.Response(200, json={"choices": [{"message": {"content": answer}}]})

    http = httpx.Client(base_url="http://muse.test", transport=httpx.MockTransport(respond))
    return MuseListener(http, "muse-spark-1.3", Language.UZBEK), calls


def test_muse_writes_down_what_it_heard() -> None:
    listener, _ = _listener("\"Onamga qo'ng'iroq qil\"")

    assert listener.transcribe(_WAV) == Transcript("Onamga qo'ng'iroq qil")


def test_a_missed_recording_is_asked_again() -> None:
    listener, calls = _listener("No audio provided.", "", "Salom")

    assert listener.transcribe(_WAV).text == "Salom"
    assert len(calls) == 3


def test_muse_that_never_hears_counts_as_unavailable() -> None:
    listener, _ = _listener("I don't have access to any audio.")

    with pytest.raises(SpeechRecognitionUnavailableError):
        listener.transcribe(_WAV)


class _Away:
    def transcribe(self, recording: Recording) -> Transcript:
        raise SpeechRecognitionUnavailableError


def test_muse_listens_when_the_worker_is_away() -> None:
    listener, _ = _listener("Salom")

    assert FallbackRecognizer(_Away(), listener).transcribe(_WAV).text == "Salom"
