from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from sado.domain.audio import Audio
from sado.infrastructure.tts.wav import encode_pcm16_wav

if TYPE_CHECKING:
    from transformers import PreTrainedTokenizerBase, VitsModel


class MmsSpeechSynthesizer:
    """Speech synthesis with Meta's MMS-TTS (VITS) models, one model per language."""

    def __init__(self, model_id: str, device: str = "cpu") -> None:
        self._model_id = model_id
        self._device = device
        self._load_lock = threading.Lock()
        self._loaded: tuple[VitsModel, PreTrainedTokenizerBase] | None = None

    def synthesize(self, text: str) -> Audio:
        import torch  # noqa: PLC0415 - heavy optional dependency, loaded only when speech is used

        model, tokenizer = self._load()
        inputs = tokenizer(text, return_tensors="pt").to(self._device)
        with torch.inference_mode():
            waveform = model(**inputs).waveform[0]
        return Audio(encode_pcm16_wav(waveform.cpu().tolist(), model.config.sampling_rate))

    def _load(self) -> tuple[VitsModel, PreTrainedTokenizerBase]:
        # Models load on first use so the server starts instantly and idle languages cost no memory.
        with self._load_lock:
            if self._loaded is None:
                from transformers import AutoTokenizer, VitsModel  # noqa: PLC0415

                tokenizer = AutoTokenizer.from_pretrained(self._model_id)
                model = VitsModel.from_pretrained(self._model_id)
                # transformers wraps `to` with a decorator whose type hints drop the bound `self`.
                model.to(self._device)  # type: ignore[arg-type, unused-ignore]
                self._loaded = (model, tokenizer)
            return self._loaded
