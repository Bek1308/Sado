from __future__ import annotations

import threading
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from sado.domain.audio import Audio
from sado.domain.voice import Voice
from sado.infrastructure.tts.wav import encode_pcm16_wav

if TYPE_CHECKING:
    from omnivoice import OmniVoice

_MODEL_ID = "k2-fsa/OmniVoice"
_SAMPLE_RATE = 24_000


class OmniVoiceEngine:
    """One OmniVoice model shared by every language, loaded on first use."""

    def __init__(self, device: str) -> None:
        self._device = device
        # The GPU runs one generation at a time; the lock also guards lazy loading.
        self._lock = threading.Lock()
        self._model: OmniVoice | None = None

    def generate(self, text: str, language: str, voice_description: str) -> list[float]:
        with self._lock:
            audio: Any = self._load().generate(
                text=text, language=language, instruct=voice_description
            )
        samples = audio[0] if isinstance(audio, list) else audio
        return [float(sample) for sample in samples]

    def _load(self) -> OmniVoice:
        if self._model is None:
            import torch  # noqa: PLC0415 - heavy optional dependency
            from omnivoice import OmniVoice  # noqa: PLC0415

            dtype = torch.float16 if self._device.startswith("cuda") else torch.float32
            self._model = OmniVoice.from_pretrained(_MODEL_ID, device_map=self._device, dtype=dtype)
        return self._model


@dataclass(frozen=True, slots=True)
class OmniVoiceSynthesizer:
    engine: OmniVoiceEngine
    language: str
    descriptions: Mapping[str, str]
    """OmniVoice voice-design description for each voice id."""

    def synthesize(self, text: str, voice: Voice) -> Audio:
        samples = self.engine.generate(text, self.language, self.descriptions[voice.id])
        return Audio(encode_pcm16_wav(samples, _SAMPLE_RATE))
