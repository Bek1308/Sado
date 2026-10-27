"""Performs every mood once per voice and saves the clips Sado clones its feelings from.

Usage (from the server directory, GPU recommended):
    uv run --extra speech python scripts/build_mood_references.py [--force]
"""

import sys
import time
from pathlib import Path

from sado.infrastructure.settings import get_settings
from sado.infrastructure.tts.mood_references import (
    MOOD_SCRIPT_LANGUAGE,
    MOOD_SCRIPTS,
    MoodReferenceLibrary,
)
from sado.infrastructure.tts.omnivoice import SAMPLE_RATE, OmniVoiceEngine
from sado.infrastructure.tts.voice_presets import VOICE_PRESETS
from sado.infrastructure.tts.wav import encode_pcm16_wav


def main() -> None:
    force = "--force" in sys.argv
    settings = get_settings()
    library = MoodReferenceLibrary(Path(settings.mood_reference_dir))
    engine = OmniVoiceEngine(settings.omnivoice_device)

    for preset in VOICE_PRESETS:
        for mood, script in MOOD_SCRIPTS.items():
            if library.find(preset.voice.id, mood) and not force:
                print(f"{preset.voice.id}/{mood}: exists, skipped")
                continue
            started = time.perf_counter()
            samples = engine.design(
                script.text,
                MOOD_SCRIPT_LANGUAGE,
                preset.style,
                speed=preset.style.speed * script.speed,
            )
            library.save(preset.voice.id, mood, encode_pcm16_wav(samples, SAMPLE_RATE), script.text)
            elapsed = time.perf_counter() - started
            print(f"{preset.voice.id}/{mood}: {len(samples) / SAMPLE_RATE:.1f}s in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
