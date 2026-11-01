from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PhoneAction:
    """Something the user's phone does itself once Sado's reply arrives.

    The server never touches the phone: it only says what to do, and the app does it
    with the phone's own screens, so a call or a message still waits for the user's tap.
    Contact names are resolved on the phone and never leave it.
    """

    kind: str
    details: Mapping[str, str]
