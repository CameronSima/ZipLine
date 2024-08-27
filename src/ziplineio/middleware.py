import re
from typing import List, Callable, Tuple
from ziplineio import response
from ziplineio.handler import Handler
from ziplineio.request import Request
from ziplineio.response import Response


def middleware(middlewares: List[Callable]) -> Callable[[Callable], Callable]:
    def decorator(handler: Callable) -> Callable:
        async def wrapped_handler(req: Request, **kwargs):
            # Ensure 'ctx' is always present in kwargs

            kwargs.setdefault("ctx", {})
            # Run the middleware stack
            try:
                req, kwargs, res = await run_middleware_stack(middlewares, req, kwargs)
            except Exception as e:
                return {
                    "status": 500,
                    "headers": [],
                    "body": b"Internal server error: " + str(e).encode(),
                }

            if res is not None:
                return res
            else:
                return await handler(req, **kwargs)

        return wrapped_handler

    return decorator


async def run_middleware_stack(
    middlewares: list[Handler], request: Request, kwargs
) -> Tuple[Request, dict, bytes | str | dict | Response | None]:
    for middleware in middlewares:
        # if the middleware func takes params, pass them in. Otherwise, just pass req

        if "ctx" not in kwargs:
            kwargs["ctx"] = {}

        print("KWARGS")
        print(kwargs)
        print(middleware.__code__.co_varnames)
        if len(middleware.__code__.co_varnames) > 1:
            _res = await middleware(request, **kwargs)
        else:
            _res = await middleware(request)

        print("RES")
        print(_res)

        if len(_res) != 2:
            req = _res
            middleware_ctx = kwargs["ctx"]
        else:
            req, middleware_ctx = _res
            kwargs["ctx"].update(middleware_ctx)

        if not isinstance(req, Request):
            response = req
            return request, kwargs, response

    return request, kwargs, None