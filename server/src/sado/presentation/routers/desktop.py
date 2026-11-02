from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel

from sado.application.wake import WakeSignal
from sado.presentation.dependencies import at_the_computer

router = APIRouter(prefix="/desktop", tags=["desktop"])

_LONGEST_WAIT_SECONDS = 25.0


class WakeResponse(BaseModel):
    count: int


def _computer(computer: Annotated[bool, Depends(at_the_computer)]) -> None:
    if not computer:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the computer's own app may ask")


@router.get("/wake", dependencies=[Depends(_computer)])
def wait_for_wake(request: Request, after: Annotated[int, Query()] = -1) -> WakeResponse:
    """Waits until the user calls "Sado" more times than `after`, or a little while."""
    signal: WakeSignal = request.app.state.wake
    timeout = 0.0 if after < 0 else _LONGEST_WAIT_SECONDS
    return WakeResponse(count=signal.wait(after, timeout))
