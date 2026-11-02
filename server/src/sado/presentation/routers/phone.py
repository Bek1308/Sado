from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from sado.application.phone_inbox import PhoneInbox
from sado.presentation.dependencies import get_phone_inbox, is_owner
from sado.presentation.routers.replies import PhoneActionModel

router = APIRouter(prefix="/phone", tags=["phone"])


def _owner(owner: Annotated[bool, Depends(is_owner)]) -> None:
    if not owner:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the owner's phone gets these")


@router.get("/actions", dependencies=[Depends(_owner)])
def take_actions(inbox: Annotated[PhoneInbox, Depends(get_phone_inbox)]) -> list[PhoneActionModel]:
    """What the owner asked for at the computer for their phone to do; each is handed out
    once."""
    return [
        PhoneActionModel(kind=action.kind, details=dict(action.details)) for action in inbox.take()
    ]
