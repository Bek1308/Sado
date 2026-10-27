from sado.domain.language import Language


class SadoError(Exception):
    """Base class for every error the domain and application layers raise on purpose."""


class EmptyTextError(SadoError):
    def __init__(self) -> None:
        super().__init__("Text must contain at least one non-whitespace character")


class UnsupportedLanguageError(SadoError):
    def __init__(self, language: Language) -> None:
        super().__init__(f"No language pack is available for '{language}'")
        self.language = language
