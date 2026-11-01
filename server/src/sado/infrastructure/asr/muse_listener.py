"""Speech recognition by Muse Spark itself, for when the Omnilingual worker is away.

Muse hears audio through the Model API's chat completions. It recognises Uzbek and Tajik
about as well as Omnilingual, but more slowly, and now and then it answers that it got no
audio at all; such answers are retried rather than taken for what the user said.
"""

import base64
import logging
import re
import subprocess
from dataclasses import dataclass

import httpx

from sado.domain.errors import SpeechRecognitionUnavailableError, UnreadableRecordingError
from sado.domain.language import Language
from sado.domain.recording import Recording, Transcript
from sado.domain.speech import SpeechRecognizer

logger = logging.getLogger(__name__)

_SPEECH = {
    Language.UZBEK: "Uzbek speech, in Uzbek Latin script",
    Language.TAJIK: "Tajik speech, in Tajik Cyrillic",
    Language.RUSSIAN: "Russian speech",
    Language.ENGLISH: "English speech",
}
# "No audio provided", "I can't access the audio", "[Audio not available]" …
_MISSED = re.compile(
    r"\baudio\b.*\b(no|not|unable|can't|cannot|don't|unavailable)\b"
    r"|\b(no|not|unable|can't|cannot|don't)\b.*\baudio\b",
    re.IGNORECASE,
)
_DECODE_TIMEOUT_SECONDS = 20
# Any recording in on stdin, 16 kHz mono wav out on stdout.
_TO_WAV = [
    "ffmpeg",
    "-loglevel",
    "error",
    "-i",
    "pipe:0",
    "-ac",
    "1",
    "-ar",
    "16000",
    "-f",
    "wav",
    "pipe:1",
]


@dataclass(frozen=True, slots=True)
class MuseListener:
    http: httpx.Client
    model: str
    language: Language
    attempts: int = 3

    def transcribe(self, recording: Recording) -> Transcript:
        audio = base64.b64encode(_as_wav(recording)).decode()
        for _ in range(self.attempts):
            heard = self._ask(audio)
            if heard and not _MISSED.search(heard):
                return Transcript(text=heard)
            logger.info("Muse did not hear the recording (%r); asking again", heard[:80])
        raise SpeechRecognitionUnavailableError

    def _ask(self, audio: str) -> str:
        instruction = (
            f"Transcribe the {_SPEECH[self.language]} in this audio word for word. "
            "Reply with the transcript only."
        )
        body = {
            "model": self.model,
            "temperature": 0,
            # With more reasoning Muse tends to decide it was given no audio.
            "reasoning_effort": "low",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": instruction},
                        {"type": "input_audio", "input_audio": {"data": audio, "format": "wav"}},
                    ],
                }
            ],
        }
        try:
            response = self.http.post("/chat/completions", json=body)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as error:
            raise SpeechRecognitionUnavailableError from error
        return str(content or "").strip().strip('"«»').strip()


@dataclass(frozen=True, slots=True)
class FallbackRecognizer:
    """Listens with the preferred recognizer, and with the fallback when it is away."""

    primary: SpeechRecognizer
    fallback: SpeechRecognizer

    def transcribe(self, recording: Recording) -> Transcript:
        try:
            return self.primary.transcribe(recording)
        except SpeechRecognitionUnavailableError:
            logger.warning("Speech recognizer unavailable; listening with the fallback")
            return self.fallback.transcribe(recording)


def _as_wav(recording: Recording) -> bytes:
    """Muse takes wav; phones record m4a, so other formats go through ffmpeg."""
    if recording.media_type in {"audio/wav", "audio/x-wav", "audio/wave"}:
        return recording.data
    try:
        done = subprocess.run(
            _TO_WAV,
            input=recording.data,
            capture_output=True,
            timeout=_DECODE_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise SpeechRecognitionUnavailableError from error
    if done.returncode != 0 or not done.stdout:
        raise UnreadableRecordingError("the recording could not be decoded")
    return done.stdout
