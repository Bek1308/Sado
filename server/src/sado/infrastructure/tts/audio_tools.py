"""Small signal-processing helpers on plain sample lists (mono, range -1.0 to 1.0)."""

from collections.abc import Sequence

_SILENCE_THRESHOLD = 0.01
_PEAK_TARGET = 0.97


def trim_silence(samples: Sequence[float], keep: int = 0) -> list[float]:
    """Removes near-silent samples from both ends, keeping `keep` samples of margin."""
    loud = [index for index, sample in enumerate(samples) if abs(sample) > _SILENCE_THRESHOLD]
    if not loud:
        return []
    start = max(loud[0] - keep, 0)
    end = min(loud[-1] + 1 + keep, len(samples))
    return list(samples[start:end])


def normalize_peak(samples: Sequence[float]) -> list[float]:
    peak = max((abs(sample) for sample in samples), default=0.0)
    if peak == 0:
        return list(samples)
    return [sample / peak * _PEAK_TARGET for sample in samples]


def join_with_pauses(pieces: Sequence[Sequence[float]], pause_samples: int) -> list[float]:
    joined: list[float] = []
    for index, piece in enumerate(pieces):
        if index:
            joined.extend([0.0] * pause_samples)
        joined.extend(piece)
    return joined
