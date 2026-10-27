import pytest

from sado.infrastructure.languages.uzbek import (
    build_uzbek_normalizer,
    spell_uzbek_number,
    spell_uzbek_ordinal,
    transliterate_uzbek_to_cyrillic,
    transliterate_uzbek_to_latin,
    unify_uzbek_apostrophes,
)


@pytest.mark.parametrize(
    ("number", "words"),
    [
        (0, "nol"),
        (12, "oʻn ikki"),
        (105, "yuz besh"),
        (250, "ikki yuz ellik"),
        (1_000, "ming"),
        (1_999, "ming toʻqqiz yuz toʻqson toʻqqiz"),
        (2_026, "ikki ming yigirma olti"),
        (15_000, "oʻn besh ming"),
        (1_000_000, "bir million"),
        (-3, "minus uch"),
    ],
)
def test_spells_cardinals(number: int, words: str) -> None:
    assert spell_uzbek_number(number) == words


@pytest.mark.parametrize(
    ("number", "words"),
    [
        (1, "birinchi"),
        (2, "ikkinchi"),
        (5, "beshinchi"),
        (20, "yigirmanchi"),
        (27, "yigirma yettinchi"),
        (2_026, "ikki ming yigirma oltinchi"),
    ],
)
def test_spells_ordinals(number: int, words: str) -> None:
    assert spell_uzbek_ordinal(number) == words


@pytest.mark.parametrize(
    ("typed", "official"),
    [
        ("o'zbek do‘st", "oʻzbek doʻst"),
        ("tog`", "togʻ"),
        ("ma'no", "maʼno"),
    ],
)
def test_unifies_apostrophes_to_official_marks(typed: str, official: str) -> None:
    assert unify_uzbek_apostrophes(typed) == official


@pytest.mark.parametrize(
    ("cyrillic", "latin"),
    [
        ("Салом, ўзбек дўстлар!", "Salom, oʻzbek doʻstlar!"),
        ("Шаҳар", "Shahar"),
        ("ер ва лекин", "yer va lekin"),
        ("тоғ", "togʻ"),
        ("маъно", "maʼno"),
        ("Salom", "Salom"),
    ],
)
def test_transliterates_cyrillic_to_latin(cyrillic: str, latin: str) -> None:
    assert transliterate_uzbek_to_latin(cyrillic) == latin


@pytest.mark.parametrize(
    ("latin", "cyrillic"),
    [
        ("Salom, o'zbek do‘stlar!", "Салом, ўзбек дўстлар!"),
        ("Shahar", "Шаҳар"),
        ("ertaga", "эртага"),
        ("yigirma yettinchi", "йигирма еттинчи"),
        ("ma'no", "маъно"),
        ("tog'", "тоғ"),
    ],
)
def test_transliterates_latin_to_cyrillic(latin: str, cyrillic: str) -> None:
    assert transliterate_uzbek_to_cyrillic(latin) == cyrillic


@pytest.mark.parametrize(
    ("text", "spoken"),
    [
        ("2026-yil", "ikki ming yigirma oltinchi yil"),
        ("2026-yilda", "ikki ming yigirma oltinchi yilda"),
        ("27-oktabr", "yigirma yettinchi oktabr"),
        ("27 oktyabr", "yigirma yettinchi oktyabr"),
        ("5ta olma", "beshta olma"),
        ("10dan ortiq", "oʻndan ortiq"),
        ("soat 10 da keling", "soat oʻnda keling"),
        ("5 ga boʻling", "beshga boʻling"),
        ("3 ta kitob", "uchta kitob"),
        ("10 dona olma", "oʻn dona olma"),
        ("narxi 15 000 so'm", "narxi oʻn besh ming soʻm"),
        ("chegirma 20%", "chegirma yigirma foiz"),
        ("Sado AI", "Sado ey ay"),
        ("Бугун 2026-йил", "Bugun ikki ming yigirma oltinchi yil"),
    ],
)
def test_normalizes_to_latin_uzbek(text: str, spoken: str) -> None:
    assert build_uzbek_normalizer().normalize(text) == spoken
