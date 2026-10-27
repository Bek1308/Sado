from __future__ import annotations

import threading
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from sado.domain.audio import Audio
from sado.domain.expression import EXPRESSION_CUE, Expression
from sado.domain.mood import Mood
from sado.domain.voice import Voice
from sado.infrastructure.tts.mood_references import (
    MOOD_SCRIPTS,
    MoodReference,
    MoodReferenceLibrary,
)
from sado.infrastructure.tts.voice_presets import VoiceStyle
from sado.infrastructure.tts.wav import encode_pcm16_wav

if TYPE_CHECKING:
    from omnivoice import OmniVoice

_MODEL_ID = "k2-fsa/OmniVoice"
SAMPLE_RATE = 24_000

# OmniVoice performs these inline non-verbal tags as sounds rather than words.
_OMNIVOICE_TAGS = {
    Expression.LAUGH: "[laughter]",
    Expression.SIGH: "[sigh]",
    Expression.SURPRISE: "[surprise-oh]",
    Expression.QUESTION: "[question-ah]",
    Expression.HMM: "[dissatisfaction-hnn]",
}


def to_omnivoice_tags(text: str) -> str:
    return EXPRESSION_CUE.sub(lambda match: _OMNIVOICE_TAGS[Expression(match[1])], text)


@dataclass(frozen=True, slots=True)
class CloneQuality:
    """Decoding effort when cloning. More steps and stronger guidance stay closer to the clip."""

    num_steps: int = 64
    guidance_scale: float = 3.0


class OmniVoiceEngine:
    """One OmniVoice model shared by every language, loaded on first use."""

    def __init__(self, device: str, clone_quality: CloneQuality | None = None) -> None:
        self._device = device
        self._clone_quality = clone_quality or CloneQuality()
        # The GPU runs one generation at a time; the lock also guards lazy loading.
        self._lock = threading.Lock()
        self._model: OmniVoice | None = None

    def design(self, text: str, language: str, style: VoiceStyle, speed: float) -> list[float]:
        """Speaks with a voice described in words; neutral delivery."""
        return self._generate(
            text=text, language=language, instruct=style.omnivoice_description, speed=speed
        )

    def clone(
        self, text: str, language: str, reference: MoodReference, speed: float
    ) -> list[float]:
        """Speaks with the voice and delivery of a reference clip."""
        return self._generate(
            text=text,
            language=language,
            ref_audio=str(reference.audio_path),
            ref_text=reference.transcript,
            speed=speed,
            num_step=self._clone_quality.num_steps,
            guidance_scale=self._clone_quality.guidance_scale,
        )

    def _generate(self, **arguments: str | float) -> list[float]:
        with self._lock:
            audio: Any = self._load().generate(**arguments)
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
    styles: Mapping[str, VoiceStyle]
    """How each voice id sounds."""
    mood_references: MoodReferenceLibrary

    def synthesize(self, text: str, voice: Voice, mood: Mood) -> Audio:
        style = self.styles[voice.id]
        spoken = to_omnivoice_tags(text)
        reference = self.mood_references.find(voice.id, mood)
        if reference is not None:
            samples = self.engine.clone(spoken, self.language, reference, style.speed)
        else:
            # Without a reference the mood can still set the pace, even if not the feeling.
            speed = style.speed * (MOOD_SCRIPTS[mood].speed if mood in MOOD_SCRIPTS else 1.0)
            samples = self.engine.design(spoken, self.language, style, speed)
        return Audio(encode_pcm16_wav(samples, SAMPLE_RATE))
