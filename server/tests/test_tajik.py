import pytest

from sado.infrastructure.languages.tajik import build_tajik_normalizer


@pytest.mark.parametrize(
    ("text", "spoken"),
    [
        ("27-уми октябр", "бисту ҳафтуми октябр"),
        ("синфи 5-ум", "синфи панҷум"),
        ("27 октябри соли 2026", "бисту ҳафтуми октябри соли ду ҳазору бисту шаш"),
        ("5-то китоб", "панҷто китоб"),
        ("5то китоб", "панҷто китоб"),
        ("соли 2026-ро", "соли ду ҳазору бисту шашро"),
        ("нарх 15 000 сомонӣ", "нарх понздаҳ ҳазор сомонӣ"),
        ("20% тахфиф", "бист фоиз тахфиф"),
        ("Ман Sado ҳастам", "Ман Садо ҳастам"),
        ("Дар Instagram", "Дар Инстаграм"),
        ("AI ёрдамчӣ", "эй ай ёрдамчӣ"),
        ("Zoom", "Зум"),
    ],
)
def test_normalizes_tajik_text(text: str, spoken: str) -> None:
    assert build_tajik_normalizer().normalize(text) == spoken
