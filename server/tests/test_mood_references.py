from pathlib import Path

from sado.domain.mood import Mood
from sado.infrastructure.tts.mood_references import MOOD_SCRIPTS, MoodReferenceLibrary


def test_finds_nothing_before_any_clip_is_saved(tmp_path: Path) -> None:
    assert MoodReferenceLibrary(tmp_path).find("sado", Mood.HAPPY) is None


def test_finds_the_exact_mood_clip(tmp_path: Path) -> None:
    library = MoodReferenceLibrary(tmp_path)
    library.save("sado", Mood.NEUTRAL, b"anchor", "Salom.")
    library.save("sado", Mood.HAPPY, b"happy", "Voy, ajoyib!")

    reference = library.find("sado", Mood.HAPPY)

    assert reference is not None
    assert reference.audio_path == tmp_path / "sado" / "happy.wav"
    assert reference.transcript == "Voy, ajoyib!"


def test_falls_back_to_the_neutral_anchor_for_missing_moods(tmp_path: Path) -> None:
    library = MoodReferenceLibrary(tmp_path)
    library.save("sado", Mood.NEUTRAL, b"anchor", "Salom.")

    reference = library.find("sado", Mood.SAD)

    assert reference is not None
    assert reference.audio_path.read_bytes() == b"anchor"


def test_every_mood_has_a_script() -> None:
    assert set(MOOD_SCRIPTS) == set(Mood)
