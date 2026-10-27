#!/usr/bin/env bash
# Pre-downloads every open model Sado runs locally, so first use is instant.
# Runs on Linux (or WSL): Omnilingual ASR depends on fairseq2, which ships no Windows wheels.
#
# Usage: bash download_models.sh
# Safe to re-run: finished downloads are skipped by the underlying caches.

set -uo pipefail

LOG_FILE="${SADO_DOWNLOAD_LOG:-$HOME/sado/download.log}"
VENV_DIR="${SADO_MODELS_VENV:-$HOME/.venvs/sado-models}"
export HF_HOME="${HF_HOME:-/mnt/c/Users/user/.cache/huggingface}"

MMS_TTS_MODELS=(
  facebook/mms-tts-tgk
  facebook/mms-tts-uzb-script_cyrillic
  facebook/mms-tts-rus
  facebook/mms-tts-eng
)

OMNILINGUAL_MODEL_CARDS=(
  omniASR_CTC_300M_v2
  omniASR_CTC_1B_v2
  omniASR_LLM_1B_v2
)

mkdir -p "$(dirname "$LOG_FILE")"
exec > >(tee -a "$LOG_FILE") 2>&1

log() { printf '[%s] %s\n' "$(date '+%F %T')" "$*"; }

ensure_uv() {
  if ! command -v uv >/dev/null; then
    log "Installing uv"
    curl -LsSf https://astral.sh/uv/install.sh | sh
  fi
  export PATH="$HOME/.local/bin:$PATH"
}

ensure_venv() {
  log "Preparing Python environment at $VENV_DIR"
  uv venv --python 3.12 --allow-existing "$VENV_DIR"
  uv pip install --python "$VENV_DIR/bin/python" omnilingual-asr huggingface_hub
}

download_mms_tts() {
  for repo in "${MMS_TTS_MODELS[@]}"; do
    log "MMS-TTS: $repo"
    "$VENV_DIR/bin/python" -c "from huggingface_hub import snapshot_download; snapshot_download('$repo')" \
      && log "MMS-TTS: $repo ready" \
      || log "MMS-TTS: $repo FAILED"
  done
}

# Loading a pipeline is the supported way to make fairseq2 fetch a model card's weights.
download_omnilingual() {
  for card in "${OMNILINGUAL_MODEL_CARDS[@]}"; do
    log "Omnilingual ASR: $card"
    "$VENV_DIR/bin/python" - "$card" <<'PY' \
      && log "Omnilingual ASR: $card ready" \
      || log "Omnilingual ASR: $card FAILED"
import gc
import sys

import torch
from omnilingual_asr.models.inference.pipeline import ASRInferencePipeline

pipeline = ASRInferencePipeline(model_card=sys.argv[1])
del pipeline
gc.collect()
torch.cuda.empty_cache()
PY
  done
}

log "=== Sado model download started ==="
ensure_uv
ensure_venv
download_mms_tts
download_omnilingual
log "=== Sado model download finished ==="
