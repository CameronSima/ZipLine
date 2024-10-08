from typing import Generic, Protocol, TypeVar

from ziplineio.request import Request
from ziplineio.response import Response

T = TypeVar("T")


class Handler(Protocol, Generic[T]):
    async def __call__(self, req: Request, ctx: T) -> bytes | str | dict | Response:
        pass
