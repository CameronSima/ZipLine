from typing import List, Callable
from ziplineio.request import Request


def middleware(middlewares: List[Callable]) -> Callable[[Callable], Callable]:
    def decorator(handler: Callable) -> Callable:
        async def wrapped_handler(req: Request, **kwargs):
            # Ensure 'ctx' is always present in kwargs

            kwargs.setdefault("ctx", {})

            for middleware in middlewares:
                try:
                    # if the middleware func takes params, pass them in. Otherwise, just pass req
                    if len(middleware.__code__.co_varnames) > 1:
                        _res = await middleware(req, **kwargs)
                    else:
                        _res = await middleware(req)

                    if len(_res) != 2:
                        req = _res
                    else:
                        req, middleware_ctx = _res

                    kwargs["ctx"].update(middleware_ctx)
                except Exception as e:
                    return {
                        "status": 500,
                        "headers": [],
                        "body": b"Internal server error: " + str(e).encode(),
                    }

                # check if the middleware returned a response
                if not isinstance(req, Request):
                    return req

            # Call the final handler with the updated kwargs including ctx
            return await handler(req, **kwargs)

        return wrapped_handler

    return decorator
