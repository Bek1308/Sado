"""Records each voice's neutral anchor and its mood clips.

    uv run --extra speech python scripts/build_mood_references.py [--force]
    uv run --extra speech python scripts/build_mood_references.py --anchor sado REC.wav "Transcript"

With `--anchor`, a real recording becomes the voice's anchor; it is trimmed to at most
eight seconds of speech and peak-normalized. Otherwise the anchor is designed once from the
voice description. Mood clips are then cloned from the anchor, so every mood keeps the voice.
"""

import argparse
import io
import time
import wave
from pathlib import Path

from sado.domain.mood import Mood
from sado.infrastructure.settings import get_settings
from sado.infrastructure.tts.audio_tools import normalize_peak, trim_silence
from sado.infrastructure.tts.mood_references import (
    MOOD_SCRIPT_LANGUAGE,
    MOOD_SCRIPTS,
    MoodReferenceLibrary,
)
from sado.infrastructure.tts.omnivoice import SAMPLE_RATE, OmniVoiceEngine
from sado.infrastructure.tts.voice_presets import VOICE_PRESETS
from sado.infrastructure.tts.wav import encode_pcm16_wav

_MAX_ANCHOR_SECONDS = 8.0
_EDGE_MARGIN = int(SAMPLE_RATE * 0.05)


def _clean(samples: list[float]) -> bytes:
    trimmed = trim_silence(samples, keep=_EDGE_MARGIN)[: int(SAMPLE_RATE * _MAX_ANCHOR_SECONDS)]
    return encode_pcm16_wav(normalize_peak(trimmed), SAMPLE_RATE)


def _read_wav(path: Path) -> list[float]:
    import librosa  # noqa: PLC0415 - resampling dependency, only needed for imports

    samples, _ = librosa.load(str(path), sr=SAMPLE_RATE, mono=True)
    return [float(sample) for sample in samples]


def _seconds(wav_bytes: bytes) -> float:
    with wave.open(io.BytesIO(wav_bytes)) as wav_file:
        return wav_file.getnframes() / wav_file.getframerate()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--anchor", nargs=3, metavar=("VOICE_ID", "WAV", "TRANSCRIPT"))
    args = parser.parse_args()

    settings = get_settings()
    library = MoodReferenceLibrary(Path(settings.mood_reference_dir))
    engine = OmniVoiceEngine(settings.omnivoice_device)

    if args.anchor:
        voice_id, wav_path, transcript = args.anchor
        clip = _clean(_read_wav(Path(wav_path)))
        library.save(voice_id, Mood.NEUTRAL, clip, transcript)
        print(f"{voice_id}/neutral: imported {_seconds(clip):.1f}s recording")

    for preset in VOICE_PRESETS:
        voice_id = preset.voice.id
        if args.force or not library.has(voice_id, Mood.NEUTRAL):
            started = time.perf_counter()
            script = MOOD_SCRIPTS[Mood.NEUTRAL]
            clip = _clean(engine.design(script, MOOD_SCRIPT_LANGUAGE, preset.style))
            library.save(voice_id, Mood.NEUTRAL, clip, script)
            print(f"{voice_id}/neutral: designed in {time.perf_counter() - started:.1f}s")

        anchor = library.find(voice_id, Mood.NEUTRAL)
        assert anchor is not None
        for mood, script in MOOD_SCRIPTS.items():
            if mood is Mood.NEUTRAL or (library.has(voice_id, mood) and not args.force):
                continue
            started = time.perf_counter()
            clip = _clean(engine.clone(script, MOOD_SCRIPT_LANGUAGE, anchor))
            library.save(voice_id, mood, clip, script)
            print(
                f"{voice_id}/{mood}: {_seconds(clip):.1f}s in {time.perf_counter() - started:.1f}s"
            )


if __name__ == "__main__":
    main()
