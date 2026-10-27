from sado.domain.expression import Expression, remove_expression_cues, split_expression_cues
from sado.infrastructure.languages.tajik import build_tajik_normalizer
from sado.infrastructure.languages.uzbek import build_uzbek_normalizer
from sado.infrastructure.tts.decorators import CueFreeSynthesizer
from sado.infrastructure.tts.omnivoice import to_omnivoice_tags
from tests.fakes import SADO_VOICE, RecordingSynthesizer


def test_splits_text_around_cues() -> None:
    assert split_expression_cues("Voy! [surprise] Rostdanmi? [laugh]") == [
        "Voy! ",
        Expression.SURPRISE,
        " Rostdanmi? ",
        Expression.LAUGH,
    ]


def test_leaves_unknown_brackets_as_text() -> None:
    assert split_expression_cues("Bu [eslatma] edi") == ["Bu [eslatma] edi"]


def test_removes_cues_for_engines_that_cannot_perform_them() -> None:
    assert remove_expression_cues("Voy! [surprise] Rostdanmi? [laugh]") == "Voy! Rostdanmi?"


def test_normalizers_keep_cues_while_spelling_numbers_around_them() -> None:
    assert (
        build_uzbek_normalizer().normalize("5ta olma [laugh] 2026-yil")
        == "beshta olma [laugh] ikki ming yigirma oltinchi yil"
    )
    assert build_tajik_normalizer().normalize("[sigh] 5-то") == "[sigh] панҷто"


def test_maps_cues_to_omnivoice_tags() -> None:
    assert to_omnivoice_tags("Voy! [surprise] [laugh]") == "Voy! [surprise-oh] [laughter]"


def test_cue_free_synthesizer_strips_cues() -> None:
    inner = RecordingSynthesizer()

    CueFreeSynthesizer(inner).synthesize("Voy! [surprise] Rostdanmi?", SADO_VOICE)

    assert inner.spoken == [("Voy! Rostdanmi?", "sado")]
