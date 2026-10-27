import pytest

from sado.infrastructure.tts.audio_tools import join_with_pauses, normalize_peak, trim_silence
from sado.infrastructure.tts.sentences import split_into_sentences


def test_trims_silence_and_keeps_a_margin() -> None:
    assert trim_silence([0.0, 0.0, 0.5, -0.4, 0.0, 0.0], keep=1) == [0.0, 0.5, -0.4, 0.0]


def test_trims_pure_silence_to_nothing() -> None:
    assert trim_silence([0.0, 0.001]) == []


def test_normalizes_the_loudest_sample_to_the_peak_target() -> None:
    assert max(abs(sample) for sample in normalize_peak([0.1, -0.5, 0.25])) == pytest.approx(0.97)


def test_joins_pieces_with_silence_between_them() -> None:
    assert join_with_pauses([[1.0], [2.0]], pause_samples=2) == [1.0, 0.0, 0.0, 2.0]


def test_splits_text_into_sentences() -> None:
    assert split_into_sentences("Salom! Qalaysiz? Men yaxshiman.") == [
        "Salom!",
        "Qalaysiz?",
        "Men yaxshiman.",
    ]


def test_breaks_overly_long_sentences_at_commas() -> None:
    sentence = "birinchi qism, ikkinchi qism, uchinchi qism."

    assert split_into_sentences(sentence, max_chars=20) == [
        "birinchi qism,",
        "ikkinchi qism,",
        "uchinchi qism.",
    ]
