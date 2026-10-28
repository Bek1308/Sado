from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from sado.application.memories import Memories
from sado.domain.memory import Memory
from sado.presentation.dependencies import get_memories

router = APIRouter(prefix="/memories", tags=["memory"])

_MAX_MEMORY_LENGTH = 500


class RememberRequest(BaseModel):
    text: str = Field(max_length=_MAX_MEMORY_LENGTH)


class MemoryResponse(BaseModel):
    id: str
    text: str
    created_at: datetime

    @classmethod
    def of(cls, memory: Memory) -> "MemoryResponse":
        return cls(id=memory.id, text=memory.text, created_at=memory.created_at)


@router.get("")
def list_memories(
    memories: Annotated[Memories, Depends(get_memories)],
) -> list[MemoryResponse]:
    return [MemoryResponse.of(memory) for memory in memories.saved()]


@router.post("", status_code=status.HTTP_201_CREATED)
def remember(
    request: RememberRequest,
    memories: Annotated[Memories, Depends(get_memories)],
) -> MemoryResponse:
    return MemoryResponse.of(memories.remember(request.text))


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def forget(
    memory_id: str,
    memories: Annotated[Memories, Depends(get_memories)],
) -> None:
    memories.forget(memory_id)
