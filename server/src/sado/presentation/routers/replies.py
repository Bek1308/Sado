from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, model_validator

from sado.application.converse import Converse
from sado.domain.conversation import Message, Speaker
from sado.domain.language import Language
from sado.domain.mode import Mode
from sado.presentation.dependencies import get_converse

router = APIRouter(prefix="/replies", tags=["conversation"])

_MAX_MESSAGES = 30
_MAX_USER_MESSAGE_LENGTH = 2_000
# Sado's own turns can be long document explanations; they are context, not new input.
_MAX_HISTORY_MESSAGE_LENGTH = 20_000
_MAX_UTC_OFFSET_MINUTES = 14 * 60


class MessageModel(BaseModel):
    speaker: Speaker
    text: str = Field(max_length=_MAX_HISTORY_MESSAGE_LENGTH)

    @model_validator(mode="after")
    def _limit_user_text(self) -> "MessageModel":
        if self.speaker is Speaker.USER and len(self.text) > _MAX_USER_MESSAGE_LENGTH:
            raise ValueError(f"A message can be at most {_MAX_USER_MESSAGE_LENGTH} characters")
        return self


class ReplyRequest(BaseModel):
    language: Language
    mode: Mode = Mode.PERSONAL
    utc_offset_minutes: int = Field(
        default=0, ge=-_MAX_UTC_OFFSET_MINUTES, le=_MAX_UTC_OFFSET_MINUTES
    )
    """The user's clock, so "tomorrow at 9" means their 9 o'clock."""
    messages: list[MessageModel] = Field(min_length=1, max_length=_MAX_MESSAGES)


class PendingActionModel(BaseModel):
    id: str
    description: str


class ReplyResponse(BaseModel):
    reply: str
    remembered: list[str]
    reminded: list[str]
    lists_changed: bool
    pending_action: PendingActionModel | None = None
    """Something Sado wants to do on the computer; it runs only after the user's yes."""


@router.post("")
def reply(
    request: ReplyRequest,
    converse: Annotated[Converse, Depends(get_converse)],
) -> ReplyResponse:
    return answer(request, converse)


def answer(
    request: ReplyRequest, converse: Converse, action_result: str | None = None
) -> ReplyResponse:
    conversation = [Message(message.speaker, message.text) for message in request.messages]
    reply = converse.execute(
        conversation,
        request.language,
        request.mode,
        timedelta(minutes=request.utc_offset_minutes),
        action_result,
    )
    pending = reply.pending_action
    return ReplyResponse(
        reply=reply.text,
        remembered=list(reply.remembered),
        reminded=list(reply.reminded),
        lists_changed=reply.lists_changed,
        pending_action=(
            PendingActionModel(id=pending.id, description=pending.description) if pending else None
        ),
    )
