"""Speech recognition with Meta's Omnilingual ASR.

The model runs in a separate worker process (see `workers/omnilingual_asr_worker.py`) because
its fairseq2 runtime only ships for Linux. Sado talks to it over HTTP, so the worker can live
in WSL during development and on a cloud GPU in production without changing this adapter.
"""

from dataclasses import dataclass

import httpx

from sado.domain.errors import SpeechRecognitionUnavailableError, UnreadableRecordingError
from sado.domain.recording import Recording, Transcript


@dataclass(frozen=True, slots=True)
class OmnilingualRecognizer:
    http: httpx.Client
    language_code: str
    """Omnilingual language and script, e.g. "uzb_Latn" or "tgk_Cyrl"."""

    def transcribe(self, recording: Recording) -> Transcript:
        try:
            response = self.http.post(
                "/transcribe",
                files={"audio": ("recording", recording.data, recording.media_type)},
                data={"language": self.language_code},
            )
        except httpx.HTTPError as error:
            raise SpeechRecognitionUnavailableError from error
        # The worker answers 4xx for audio it cannot decode or that runs too long: the
        # recording is at fault, not the service.
        if response.is_client_error:
            raise UnreadableRecordingError(_detail(response))
        try:
            response.raise_for_status()
            return Transcript(text=str(response.json()["text"]))
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as error:
            raise SpeechRecognitionUnavailableError from error


def _detail(response: httpx.Response) -> str:
    try:
        detail = response.json().get("detail")
    except (ValueError, AttributeError):
        detail = None
    return detail if isinstance(detail, str) else f"rejected with status {response.status_code}"
