from pathlib import Path

from sado.domain.mood import Mood
from sado.infrastructure.tts.mood_references import MOOD_SCRIPTS, MoodReferenceLibrary


def test_finds_nothing_before_a_reference_is_saved(tmp_path: Path) -> None:
    assert MoodReferenceLibrary(tmp_path).find("sado", Mood.HAPPY) is None


def test_saves_and_finds_a_reference(tmp_path: Path) -> None:
    library = MoodReferenceLibrary(tmp_path)

    library.save("sado", Mood.HAPPY, b"RIFF", "Voy, ajoyib!")
    reference = library.find("sado", Mood.HAPPY)

    assert reference is not None
    assert reference.audio_path == tmp_path / "sado" / "happy.wav"
    assert reference.audio_path.read_bytes() == b"RIFF"
    assert reference.transcript == "Voy, ajoyib!"


def test_every_mood_except_neutral_has_a_script() -> None:
    assert set(MOOD_SCRIPTS) == set(Mood) - {Mood.NEUTRAL}
