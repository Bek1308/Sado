"""Reference clips that OmniVoice clones every sentence from.

Each voice has a neutral anchor clip: its one true recording. Cloning every sentence from the
same anchor keeps the voice identical from sentence to sentence. Moods are recorded once by
cloning the anchor on an expressive script, so the feeling changes but the voice does not.
"""

from dataclasses import dataclass
from pathlib import Path

from sado.domain.mood import Mood

MOOD_SCRIPTS = {
    Mood.NEUTRAL: (
        "Assalomu alaykum. Men sizning ovozli yordamchingizman. "
        "Bugun sizga qanday yordam bera olaman?"
    ),
    Mood.HAPPY: "Voy, qanday ajoyib yangilik! [laughter] Men juda xursandman, rahmat sizga!",
    Mood.CALM: (
        "Hammasi joyida. Shoshilmang, chuqur nafas oling. Biz buni birga, sekin-asta hal qilamiz."
    ),
    Mood.SAD: (
        "[sigh] Afsuski, bu safar omad kulib boqmadi... Lekin xafa boʻlmang, hali hammasi oldinda."
    ),
    Mood.EXCITED: (
        "Tezroq qarang! [surprise-oh] Bu haqiqatan ham ajoyib! Men buni kutib turolmayapman!"
    ),
    Mood.SERIOUS: (
        "Diqqat qiling. Bu juda muhim masala. Hujjatni oʻz vaqtida topshirishingiz shart."
    ),
}
MOOD_SCRIPT_LANGUAGE = "uz"


@dataclass(frozen=True, slots=True)
class MoodReference:
    audio_path: Path
    transcript: str


class MoodReferenceLibrary:
    """Clips stored as `<root>/<voice id>/<mood>.wav` with a `.txt` transcript."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def find(self, voice_id: str, mood: Mood) -> MoodReference | None:
        """The clip for this mood, or the voice's neutral anchor when the mood has none."""
        return self._find_exact(voice_id, mood) or self._find_exact(voice_id, Mood.NEUTRAL)

    def save(self, voice_id: str, mood: Mood, wav_bytes: bytes, transcript: str) -> None:
        audio_path, transcript_path = self._paths(voice_id, mood)
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        audio_path.write_bytes(wav_bytes)
        transcript_path.write_text(transcript, encoding="utf-8")

    def has(self, voice_id: str, mood: Mood) -> bool:
        return self._find_exact(voice_id, mood) is not None

    def _find_exact(self, voice_id: str, mood: Mood) -> MoodReference | None:
        audio_path, transcript_path = self._paths(voice_id, mood)
        if not (audio_path.is_file() and transcript_path.is_file()):
            return None
        return MoodReference(audio_path, transcript_path.read_text(encoding="utf-8"))

    def _paths(self, voice_id: str, mood: Mood) -> tuple[Path, Path]:
        base = self._root / voice_id / mood.value
        return base.with_suffix(".wav"), base.with_suffix(".txt")
