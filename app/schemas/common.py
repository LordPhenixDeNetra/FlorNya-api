import enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SortOrder(str, enum.Enum):
    asc = "asc"
    desc = "desc"


class PaginationParams(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    skip: int
    limit: int
    has_more: bool


class CursorPaginationParams(BaseModel):
    cursor: str | None = Field(default=None)
    limit: int = Field(default=20, ge=1, le=100)


class CursorPaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None
    has_more: bool
