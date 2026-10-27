"""Mood references: short clips that teach OmniVoice how a voice sounds in a given mood.

OmniVoice's voice design cannot express emotion, but voice cloning copies the delivery of its
reference clip: pace, intonation and feeling. So each mood is first performed once from an
expressive script, saved, and from then on every sentence in that mood is cloned from it.
"""

from dataclasses import dataclass
from pathlib import Path

from sado.domain.mood import Mood


@dataclass(frozen=True, slots=True)
class MoodScript:
    """What a voice says, and how fast, to perform a mood for its reference clip."""

    text: str
    speed: float


MOOD_SCRIPTS = {
    Mood.HAPPY: MoodScript(
        "Voy, qanday ajoyib yangilik! [laughter] Men juda xursandman, rahmat sizga!", 1.08
    ),
    Mood.CALM: MoodScript(
        "Hammasi joyida. Shoshilmang, chuqur nafas oling. Biz buni birga, sekin-asta hal qilamiz.",
        0.9,
    ),
    Mood.SAD: MoodScript(
        "[sigh] Afsuski, bu safar omad kulib boqmadi... Lekin xafa boʻlmang, hali hammasi oldinda.",
        0.85,
    ),
    Mood.EXCITED: MoodScript(
        "Tezroq qarang! [surprise-oh] Bu haqiqatan ham ajoyib! Men buni kutib turolmayapman!", 1.15
    ),
    Mood.SERIOUS: MoodScript(
        "Diqqat qiling. Bu juda muhim masala. Hujjatni oʻz vaqtida topshirishingiz shart.", 0.95
    ),
}
MOOD_SCRIPT_LANGUAGE = "uz"


@dataclass(frozen=True, slots=True)
class MoodReference:
    audio_path: Path
    transcript: str


class MoodReferenceLibrary:
    """Reference clips stored as `<root>/<voice id>/<mood>.wav` with a `.txt` transcript."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def find(self, voice_id: str, mood: Mood) -> MoodReference | None:
        audio_path, transcript_path = self._paths(voice_id, mood)
        if not (audio_path.is_file() and transcript_path.is_file()):
            return None
        return MoodReference(audio_path, transcript_path.read_text(encoding="utf-8"))

    def save(self, voice_id: str, mood: Mood, wav_bytes: bytes, transcript: str) -> None:
        audio_path, transcript_path = self._paths(voice_id, mood)
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        audio_path.write_bytes(wav_bytes)
        transcript_path.write_text(transcript, encoding="utf-8")

    def _paths(self, voice_id: str, mood: Mood) -> tuple[Path, Path]:
        base = self._root / voice_id / mood.value
        return base.with_suffix(".wav"), base.with_suffix(".txt")
