import pytest

from sado.domain.audio import Audio
from sado.domain.mood import Mood
from sado.domain.voice import Voice
from sado.infrastructure.tts.decorators import FallbackSynthesizer, TransliteratingSynthesizer
from tests.fakes import SADO_VOICE, RecordingSynthesizer


class _BrokenSynthesizer:
    def synthesize(self, text: str, voice: Voice, mood: Mood) -> Audio:
        raise RuntimeError("CUDA out of memory")


def test_transliterates_before_synthesizing() -> None:
    inner = RecordingSynthesizer()

    TransliteratingSynthesizer(inner, str.upper).synthesize("salom", SADO_VOICE, Mood.NEUTRAL)

    assert inner.spoken == [("SALOM", "sado")]


def test_uses_primary_voice_when_it_works() -> None:
    primary, fallback = RecordingSynthesizer(), RecordingSynthesizer()

    FallbackSynthesizer(primary, fallback).synthesize("salom", SADO_VOICE, Mood.NEUTRAL)

    assert primary.spoken == [("salom", "sado")]
    assert fallback.spoken == []


def test_switches_to_fallback_voice_when_primary_fails(caplog: pytest.LogCaptureFixture) -> None:
    fallback = RecordingSynthesizer()

    audio = FallbackSynthesizer(_BrokenSynthesizer(), fallback).synthesize(
        "salom", SADO_VOICE, Mood.NEUTRAL
    )

    assert audio.wav_bytes == b"wav:sado:salom"
    assert "fallback voice" in caplog.text
