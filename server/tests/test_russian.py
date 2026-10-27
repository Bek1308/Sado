import pytest

from sado.infrastructure.languages.russian import build_russian_normalizer


@pytest.mark.parametrize(
    ("text", "spoken"),
    [
        (
            "27 октября 2026 года",
            "двадцать седьмого октября две тысячи двадцать шестого года",
        ),
        ("в 2026 году", "в две тысячи двадцать шестом году"),
        ("5-й этаж", "пятый этаж"),
        ("в 2026-м", "в две тысячи двадцать шестом"),
        ("до 10-го числа", "до десятого числа"),
        ("купил 3 книги", "купил три книги"),
        ("ВВП вырос", "вэ вэ пэ вырос"),
        ("Меня зовут Sado", "Меня зовут Садо"),
    ],
)
def test_normalizes_russian_text(text: str, spoken: str) -> None:
    assert build_russian_normalizer().normalize(text) == spoken
