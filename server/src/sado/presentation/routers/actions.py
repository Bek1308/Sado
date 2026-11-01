from typing import Annotated

from fastapi import APIRouter, Depends, status

from sado.application.converse import Converse
from sado.application.desktop_tools import PendingActions
from sado.domain.errors import SadoError
from sado.presentation.dependencies import get_converse, get_pending_actions
from sado.presentation.routers.replies import ReplyRequest, ReplyResponse, answer

router = APIRouter(prefix="/actions", tags=["desktop"])


@router.post("/{action_id}/confirm")
def confirm(
    action_id: str,
    request: ReplyRequest,
    pending: Annotated[PendingActions, Depends(get_pending_actions)],
    converse: Annotated[Converse, Depends(get_converse)],
) -> ReplyResponse:
    """Runs the action the user said yes to, then lets Sado tell them how it went.

    `request` carries the conversation up to and including the user's yes.
    """
    action = pending.take(action_id)
    try:
        result = action.run()
    except SadoError as error:
        result = f"It failed: {error}"
    return answer(request, converse, action_result=result)


@router.post("/{action_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
def cancel(
    action_id: str,
    pending: Annotated[PendingActions, Depends(get_pending_actions)],
) -> None:
    pending.take(action_id)
