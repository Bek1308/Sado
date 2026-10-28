from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from sado.application.reminders import Reminders
from sado.domain.reminder import Reminder
from sado.presentation.dependencies import get_reminders

router = APIRouter(prefix="/reminders", tags=["memory"])

_MAX_REMINDER_LENGTH = 500


class RemindRequest(BaseModel):
    text: str = Field(max_length=_MAX_REMINDER_LENGTH)
    due: datetime


class ReminderResponse(BaseModel):
    id: str
    text: str
    due_at: datetime
    created_at: datetime

    @classmethod
    def of(cls, reminder: Reminder) -> "ReminderResponse":
        return cls(
            id=reminder.id,
            text=reminder.text,
            due_at=reminder.due_at,
            created_at=reminder.created_at,
        )


@router.get("")
def list_reminders(
    reminders: Annotated[Reminders, Depends(get_reminders)],
) -> list[ReminderResponse]:
    return [ReminderResponse.of(reminder) for reminder in reminders.saved()]


@router.post("", status_code=status.HTTP_201_CREATED)
def remind(
    request: RemindRequest,
    reminders: Annotated[Reminders, Depends(get_reminders)],
) -> ReminderResponse:
    return ReminderResponse.of(reminders.remind(request.text, request.due.isoformat()))


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def forget(
    reminder_id: str,
    reminders: Annotated[Reminders, Depends(get_reminders)],
) -> None:
    reminders.forget(reminder_id)
