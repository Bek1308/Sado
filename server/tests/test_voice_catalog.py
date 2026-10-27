import pytest

from sado.application.voices import VoiceCatalog
from sado.domain.errors import UnknownVoiceError
from sado.domain.voice import Voice
from sado.infrastructure.tts.voice_presets import VOICE_PRESETS
from tests.fakes import OPA_VOICE, SADO_VOICE, fake_voice_catalog


def test_returns_default_voice_when_none_is_requested() -> None:
    assert fake_voice_catalog().find(None) == SADO_VOICE


def test_finds_voice_by_id() -> None:
    assert fake_voice_catalog().find("opa") == OPA_VOICE


def test_rejects_unknown_voice_id() -> None:
    with pytest.raises(UnknownVoiceError):
        fake_voice_catalog().find("robot")


def test_default_must_belong_to_the_catalog() -> None:
    with pytest.raises(ValueError, match="default voice"):
        VoiceCatalog(voices=[SADO_VOICE], default=Voice("ghost", "Ghost"))


def test_presets_have_unique_ids() -> None:
    ids = [preset.voice.id for preset in VOICE_PRESETS]

    assert len(ids) == len(set(ids))
