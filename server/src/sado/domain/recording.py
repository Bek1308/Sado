from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Recording:
    """Audio captured from the user, in whatever format the device produced (wav, webm, m4a…)."""

    data: bytes
    media_type: str


@dataclass(frozen=True, slots=True)
class Transcript:
    text: str
