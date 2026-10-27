from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sado.domain.audio import Audio
from sado.domain.mood import Mood
from sado.domain.voice import Voice
from sado.infrastructure.tts.wav import encode_pcm16_wav

if TYPE_CHECKING:
    from transformers import PreTrainedTokenizerBase, VitsModel


@dataclass(frozen=True, slots=True)
class VitsVoiceSettings:
    """Controls how much VITS improvises when it speaks.

    MMS ships with a duration noise of 0.8, which makes some words rush and others drag.
    Lower values give an even, predictable pace; a fixed seed makes the same text sound
    the same every time.
    """

    speaking_rate: float = 1.0
    pitch_variation: float = 0.5
    rhythm_variation: float = 0.0
    seed: int = 0


class MmsSpeechSynthesizer:
    """Speech synthesis with Meta's MMS-TTS (VITS) models.

    Each language has a single MMS speaker with a fixed delivery, so the requested voice and
    mood cannot change how it sounds.
    """

    def __init__(
        self,
        model_id: str,
        voice: VitsVoiceSettings | None = None,
        device: str = "cpu",
    ) -> None:
        self._model_id = model_id
        self._voice = voice or VitsVoiceSettings()
        self._device = device
        # One lock covers loading and inference: seeding torch is process-global.
        self._lock = threading.Lock()
        self._loaded: tuple[VitsModel, PreTrainedTokenizerBase] | None = None

    def synthesize(self, text: str, voice: Voice, mood: Mood) -> Audio:
        import torch  # noqa: PLC0415 - heavy optional dependency, loaded only when speech is used

        with self._lock:
            model, tokenizer = self._load()
            inputs = tokenizer(text, return_tensors="pt").to(self._device)
            torch.manual_seed(self._voice.seed)
            with torch.inference_mode():
                waveform = model(**inputs).waveform[0]
        return Audio(encode_pcm16_wav(waveform.cpu().tolist(), model.config.sampling_rate))

    def _load(self) -> tuple[VitsModel, PreTrainedTokenizerBase]:
        # Models load on first use so the server starts instantly and idle languages cost no memory.
        if self._loaded is None:
            from transformers import AutoTokenizer, VitsModel  # noqa: PLC0415

            tokenizer = AutoTokenizer.from_pretrained(self._model_id)
            model = VitsModel.from_pretrained(self._model_id)
            # transformers wraps `to` with a decorator whose type hints drop the bound `self`.
            model.to(self._device)  # type: ignore[arg-type, unused-ignore]
            model.speaking_rate = self._voice.speaking_rate
            model.noise_scale = self._voice.pitch_variation
            model.noise_scale_duration = self._voice.rhythm_variation
            self._loaded = (model, tokenizer)
        return self._loaded
