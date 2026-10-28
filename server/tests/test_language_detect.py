from sado.domain.language import Language
from sado.domain.language_detect import detect_language


def test_detects_tajik_by_its_own_letters() -> None:
    assert detect_language("Ман ғоят хурсанд ҳастам") is Language.TAJIK


def test_detects_tajik_greetings() -> None:
    assert detect_language("Салом, чӣ хел?") is Language.TAJIK


def test_detects_uzbek_latin() -> None:
    assert detect_language("Salom, sen yaxshimisan?") is Language.UZBEK


def test_detects_uzbek_cyrillic() -> None:
    assert detect_language("Мен сен билан гаплашаман") is Language.UZBEK


def test_detects_russian() -> None:
    assert detect_language("Привет, как дела?") is Language.RUSSIAN


def test_detects_bare_cyrillic_as_russian() -> None:
    assert detect_language("Блабла карнавал") is Language.RUSSIAN


def test_detects_english() -> None:
    assert detect_language("Hello, how are you?") is Language.ENGLISH


def test_returns_none_without_any_signal() -> None:
    assert detect_language("") is None
    assert detect_language("123!?") is None
    assert detect_language("xyz blq") is None
