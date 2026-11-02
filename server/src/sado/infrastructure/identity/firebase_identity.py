"""Checks Firebase sign-in tokens, so Sado knows whose phone is talking to it.

Firebase signs the tokens with Google's keys; checking the signature, the expiry and that
the token was made for this project needs no secret and no service account.
"""

from dataclasses import dataclass, field

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2 import id_token

from sado.domain.errors import InvalidIdentityError
from sado.domain.identity import Person


@dataclass(frozen=True, slots=True)
class FirebaseIdentity:
    project_id: str
    _transport: Request = field(default_factory=Request)

    def verify(self, token: str) -> Person:
        try:
            # google-auth ships without type hints for this helper.
            claims = id_token.verify_firebase_token(  # type: ignore[no-untyped-call]
                token, self._transport, self.project_id
            )
        except (GoogleAuthError, ValueError) as error:
            raise InvalidIdentityError from error
        if not claims or not isinstance(claims.get("sub"), str):
            raise InvalidIdentityError
        email = claims.get("email") if claims.get("email_verified") else None
        return Person(id=claims["sub"], email=email if isinstance(email, str) else None)
