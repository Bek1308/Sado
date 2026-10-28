import httpx
import pytest

from sado.domain.errors import SpeechRecognitionUnavailableError
from sado.domain.recording import Recording
from sado.infrastructure.asr.omnilingual import OmnilingualRecognizer


def _client(handler: httpx.MockTransport) -> httpx.Client:
    return httpx.Client(base_url="http://asr.test", transport=handler)


def test_sends_audio_and_language_and_returns_the_transcript() -> None:
    seen: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"text": "salom"})

    recognizer = OmnilingualRecognizer(_client(httpx.MockTransport(respond)), "uzb_Latn")

    transcript = recognizer.transcribe(Recording(b"RIFF", "audio/wav"))

    assert transcript.text == "salom"
    assert seen[0].url.path == "/transcribe"
    body = seen[0].content
    assert b'name="language"' in body
    assert b"uzb_Latn" in body
    assert b"RIFF" in body


def test_reports_unavailable_when_the_worker_fails() -> None:
    recognizer = OmnilingualRecognizer(
        _client(httpx.MockTransport(lambda _: httpx.Response(500))), "uzb_Latn"
    )

    with pytest.raises(SpeechRecognitionUnavailableError):
        recognizer.transcribe(Recording(b"RIFF", "audio/wav"))


def test_reports_unavailable_when_the_worker_is_unreachable() -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    recognizer = OmnilingualRecognizer(_client(httpx.MockTransport(refuse)), "tgk_Cyrl")

    with pytest.raises(SpeechRecognitionUnavailableError):
        recognizer.transcribe(Recording(b"RIFF", "audio/wav"))
