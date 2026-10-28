from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from sado.application.converse import Converse
from sado.domain.conversation import Message, Speaker
from sado.domain.language import Language
from sado.presentation.dependencies import get_converse

router = APIRouter(prefix="/replies", tags=["conversation"])

_MAX_MESSAGES = 30
_MAX_MESSAGE_LENGTH = 2_000


class MessageModel(BaseModel):
    speaker: Speaker
    text: str = Field(max_length=_MAX_MESSAGE_LENGTH)


class ReplyRequest(BaseModel):
    language: Language
    messages: list[MessageModel] = Field(min_length=1, max_length=_MAX_MESSAGES)


class ReplyResponse(BaseModel):
    reply: str
    remembered: list[str]


@router.post("")
def reply(
    request: ReplyRequest,
    converse: Annotated[Converse, Depends(get_converse)],
) -> ReplyResponse:
    conversation = [Message(message.speaker, message.text) for message in request.messages]
    answer = converse.execute(conversation, request.language)
    return ReplyResponse(reply=answer.text, remembered=list(answer.remembered))
