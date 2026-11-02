from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Person:
    """Someone signed in to Sado with their Google account."""

    id: str
    email: str | None
    """Only set once Google has verified it."""


class IdentityVerifier(Protocol):
    def verify(self, token: str) -> Person:
        """Who a sign-in token belongs to; raises InvalidIdentityError for a bad one."""
        ...
