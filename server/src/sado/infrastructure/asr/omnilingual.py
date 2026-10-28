"""Speech recognition with Meta's Omnilingual ASR.

The model runs in a separate worker process (see `workers/omnilingual_asr_worker.py`) because
its fairseq2 runtime only ships for Linux. Sado talks to it over HTTP, so the worker can live
in WSL during development and on a cloud GPU in production without changing this adapter.
"""

from dataclasses import dataclass

import httpx

from sado.domain.errors import SpeechRecognitionUnavailableError
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
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise SpeechRecognitionUnavailableError from error
        return Transcript(text=str(response.json()["text"]))
