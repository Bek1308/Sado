from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from sado.application.lists import Lists
from sado.domain.lists import ListItem
from sado.presentation.dependencies import get_lists

router = APIRouter(prefix="/lists", tags=["memory"])


class ListItemResponse(BaseModel):
    id: str
    text: str


class ListResponse(BaseModel):
    name: str
    items: list[ListItemResponse]


@router.get("")
def list_lists(lists: Annotated[Lists, Depends(get_lists)]) -> list[ListResponse]:
    grouped: dict[str, list[ListItem]] = {}
    for item in lists.everything():
        grouped.setdefault(item.list_name, []).append(item)
    return [
        ListResponse(
            name=name, items=[ListItemResponse(id=item.id, text=item.text) for item in items]
        )
        for name, items in grouped.items()
    ]


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item(item_id: str, lists: Annotated[Lists, Depends(get_lists)]) -> None:
    lists.forget_item(item_id)
