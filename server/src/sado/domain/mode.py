from enum import StrEnum


class Mode(StrEnum):
    """How Sado talks: the situation the user is in right now."""

    HOME = "home"
    PERSONAL = "personal"
    WORK = "work"
    ON_THE_GO = "on_the_go"
