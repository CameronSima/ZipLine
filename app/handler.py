from typing import Generic, Protocol, TypeVar

from app.models import Request
from app.response import Response

T = TypeVar("T")


class Handler(Protocol, Generic[T]):
    async def __call__(self, req: Request, ctx: T) -> bytes | str | Response:
        pass
