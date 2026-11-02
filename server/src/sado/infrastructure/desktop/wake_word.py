"""Listens on the computer's microphone for "Sado", entirely on the computer.

A small Vosk model hears only a short list of words, so a passing conversation is mostly
heard as other words or as nothing; "Sado" counts only when the model is sure of it.
Nothing that is heard leaves the computer.
"""

import json
import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path

import sounddevice
from vosk import KaldiRecognizer, Model, SetLogLevel

logger = logging.getLogger(__name__)

_RATE = 16_000
_BLOCK = 4_000
_WAKE_WORD = "садо"
# Words that sound like "Sado", so near misses land on them instead of on the wake word.
_DECOYS = (
    "сад", "сало", "сода", "салом", "сегодня", "да", "до", "со", "са", "сам", "сама",
    "надо", "садик", "садовод", "так", "как", "погода", "хорошая", "и", "а", "о",
)  # fmt: skip
_SURE = 0.9
# One call is one call, however long the name is drawn out.
_QUIET_AFTER_WAKE_SECONDS = 3.0


class WakeWordListener:
    def __init__(self, model_dir: Path, on_wake: Callable[[], None]) -> None:
        self._model_dir = model_dir
        self._on_wake = on_wake

    def start(self) -> None:
        threading.Thread(target=self._listen, name="sado-wake-word", daemon=True).start()

    def _listen(self) -> None:
        SetLogLevel(-1)
        try:
            model = Model(str(self._model_dir))
        except Exception:
            logger.exception("Could not load the wake-word model from %s", self._model_dir)
            return
        words = json.dumps([_WAKE_WORD, *_DECOYS, "[unk]"], ensure_ascii=False)
        recognizer = KaldiRecognizer(model, _RATE, words)
        recognizer.SetWords(True)
        last_wake = 0.0
        try:
            with sounddevice.RawInputStream(
                samplerate=_RATE, blocksize=_BLOCK, dtype="int16", channels=1
            ) as microphone:
                logger.info("Listening for 'Sado'")
                while True:
                    block, _ = microphone.read(_BLOCK)
                    if not recognizer.AcceptWaveform(bytes(block)):
                        continue
                    heard = json.loads(recognizer.Result()).get("result", [])
                    called = any(
                        word["word"] == _WAKE_WORD and word["conf"] >= _SURE for word in heard
                    )
                    if called and time.monotonic() - last_wake > _QUIET_AFTER_WAKE_SECONDS:
                        last_wake = time.monotonic()
                        self._on_wake()
        except Exception:
            logger.exception("The microphone stopped; no longer listening for 'Sado'")
