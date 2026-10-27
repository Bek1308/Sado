import pytest

from sado.domain.audio import Audio
from sado.infrastructure.tts.decorators import FallbackSynthesizer, TransliteratingSynthesizer
from tests.fakes import RecordingSynthesizer


class _BrokenSynthesizer:
    def synthesize(self, text: str) -> Audio:
        raise RuntimeError("CUDA out of memory")


def test_transliterates_before_synthesizing() -> None:
    inner = RecordingSynthesizer()

    TransliteratingSynthesizer(inner, str.upper).synthesize("salom")

    assert inner.spoken_texts == ["SALOM"]


def test_uses_primary_voice_when_it_works() -> None:
    primary, fallback = RecordingSynthesizer(), RecordingSynthesizer()

    FallbackSynthesizer(primary, fallback).synthesize("salom")

    assert primary.spoken_texts == ["salom"]
    assert fallback.spoken_texts == []


def test_switches_to_fallback_voice_when_primary_fails(caplog: pytest.LogCaptureFixture) -> None:
    fallback = RecordingSynthesizer()

    audio = FallbackSynthesizer(_BrokenSynthesizer(), fallback).synthesize("salom")

    assert audio.wav_bytes == b"wav:salom"
    assert "fallback voice" in caplog.text
