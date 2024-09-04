from typing import List, Callable, Tuple

from ziplineio.handler import Handler
from ziplineio.request import Request
from ziplineio.response import Response
from ziplineio.utils import call_handler


def middleware(middlewares: List[Callable]) -> Callable[[Callable], Callable]:
    def decorator(handler: Callable) -> Callable:
        async def wrapped_handler(req: Request, **kwargs):
            # Ensure 'ctx' is always present in kwargs

            kwargs.setdefault("ctx", {})
            # Run the middleware stack

            req, kwargs, res = await run_middleware_stack(
                middlewares, req=req, **kwargs
            )

            if res is not None:
                return res
            else:
                return await handler(req, **kwargs)

        return wrapped_handler

    return decorator


async def run_middleware_stack(
    middlewares: list[Handler], req: Request, **kwargs
) -> Tuple[Request, dict, bytes | str | dict | Response | None]:
    for middleware in middlewares:
        # if the middleware func takes params, pass them in. Otherwise, just pass req

        if "ctx" not in kwargs:
            kwargs["ctx"] = {}

        _res = await call_handler(middleware, req=req, **kwargs)

        # regular handlers return a response, but middleware can return a tuple
        if not isinstance(_res, tuple):
            _res = (_res, kwargs)

        if len(_res) != 2:
            req = _res
            middleware_ctx = kwargs["ctx"]
        else:
            req, middleware_ctx = _res
            kwargs["ctx"].update(middleware_ctx)

        if not isinstance(req, Request):
            response = req
            return req, kwargs, response

    return req, kwargs, None
