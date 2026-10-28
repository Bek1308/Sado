from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Voice:
    """A character voice the user can pick. How it sounds is up to each speech engine."""

    id: str
    name: str
    description: str = ""
