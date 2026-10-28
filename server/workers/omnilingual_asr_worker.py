"""Speech-to-text worker around Meta's Omnilingual ASR.

Runs on Linux only: the fairseq2 runtime behind Omnilingual ships no Windows build. During
development it runs inside WSL; in production it can run on any Linux GPU host.

    ASR_MODEL_CARD=omniASR_LLM_1B_v2 uvicorn omnilingual_asr_worker:app --host 0.0.0.0 --port 8011

Requires the environment built by `scripts/download_models.sh`, plus ffmpeg.
"""

import os
import subprocess
import tempfile
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

import soundfile as sf
from fastapi import FastAPI, Form, HTTPException, UploadFile, status
from omnilingual_asr.models.inference.pipeline import ASRInferencePipeline

MODEL_CARD = os.environ.get("ASR_MODEL_CARD", "omniASR_LLM_1B_v2")
SAMPLE_RATE = 16_000
# The non-"Unlimited" Omnilingual models accept at most forty seconds per utterance.
MAX_SECONDS = 40.0

_pipeline: ASRInferencePipeline | None = None


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    global _pipeline  # noqa: PLW0603 - one model per process, loaded once at startup
    _pipeline = ASRInferencePipeline(model_card=MODEL_CARD)
    yield


app = FastAPI(title="Omnilingual ASR worker", lifespan=lifespan)


def _to_wav_16k(data: bytes, folder: Path) -> Path:
    """Devices send webm, m4a, mp3 or wav; the model reads 16 kHz mono WAV."""
    source, target = folder / "input", folder / "speech.wav"
    source.write_bytes(data)
    result = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(source), "-ac", "1",
         "-ar", str(SAMPLE_RATE), str(target)],
        capture_output=True,
        check=False,
    )  # fmt: skip
    if result.returncode != 0:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Unreadable audio")
    return target


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "model": MODEL_CARD}


@app.post("/transcribe")
def transcribe(audio: UploadFile, language: Annotated[str, Form()]) -> dict[str, str]:
    assert _pipeline is not None
    with tempfile.TemporaryDirectory() as folder:
        wav_path = _to_wav_16k(audio.file.read(), Path(folder))
        seconds = sf.info(str(wav_path)).duration
        if seconds > MAX_SECONDS:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                f"Recording is {seconds:.0f} s; the limit is {MAX_SECONDS:.0f} s",
            )
        text = _pipeline.transcribe([str(wav_path)], lang=[language], batch_size=1)[0]
    return {"text": text}
