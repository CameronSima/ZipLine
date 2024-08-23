from typing import Any, Callable, List, Tuple, Type

from app.dependency_injector import DependencyInjector
from app.handler import Handler
from app.models import Request
from app.response import format_response
from app.router import Router
from app.utils import parse_scope


class App:
    _router: Router
    _injector: DependencyInjector

    def __init__(self) -> None:
        self._router = Router()
        self._injector = DependencyInjector()

    def router(self, prefix: str, router: Router) -> None:
        self._router.add_sub_router(prefix, router)

    def get(self, path: str) -> Callable[[Handler], Callable]:
        return self._router.get(path)

    def post(self, path: str) -> Callable[[Handler], Callable]:
        return self._router.post(path)

    def put(self, path: str) -> Callable[[Handler], Callable]:
        return self._router.put(path)

    def delete(self, path: str) -> Callable[[Handler], Callable]:
        return self._router.delete(path)

    def inject(
        self, service_class: Type, name: str = None
    ) -> Callable[[Callable], Callable]:
        return self._injector.inject(service_class, name)

    def middleware(self, middlewares: List[Callable]) -> Callable[[Callable], Callable]:
        def decorator(handler: Callable) -> Callable:
            async def wrapped_handler(req: Request, *args, **kwargs):
                # Ensure 'ctx' is always present in kwargs
                kwargs.setdefault("ctx", {})

                for middleware in middlewares:
                    # Call middleware with req and the kwargs including ctx
                    req, middleware_ctx = await middleware(req, **kwargs)
                    # Update the context with any changes from middleware
                    kwargs["ctx"].update(middleware_ctx)

                # Call the final handler with the updated kwargs including ctx
                return await handler(req, **kwargs)

            return wrapped_handler

        return decorator

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        async def uvicorn_handler(scope: dict, receive: Any, send: Any) -> None:
            if scope["type"] == "http":
                req = parse_scope(scope)
                handler, path_params = self._router.get_handler(req.method, req.path)
                if handler is None:
                    response = {"status": 404, "headers": [], "body": b"Not found"}
                else:
                    req.path_params = path_params
                    print(f"Path params: {path_params}")
                    raw_response = await handler(req, {})
                    response = format_response(raw_response)

                await send(
                    {
                        "type": "http.response.start",
                        "status": response["status"],
                        "headers": response["headers"],
                    }
                )

                await send(
                    {
                        "type": "http.response.body",
                        "body": response["body"],
                    }
                )

        return uvicorn_handler


app = App()


async def logging_middleware(req: Request) -> Tuple[Request, dict]:
    print(f"Received request: {req.method} {req.path}")
    # Pass along request and an empty context (no modifications)
    return req, {}


async def auth_middleware(req: Request) -> Tuple[Request, dict]:
    # Modify the context with some auth information
    return req, {"auth": "Unauthorized"}


class LoggingService:
    def log(self, message: str) -> None:
        print(f"Logging: {message}")


@app.get("/")
@app.inject(LoggingService)
@app.middleware([logging_middleware, auth_middleware])
async def handler(req: Request, ctx: dict, LoggingService: LoggingService) -> dict:
    res = {"message": "Hello, world!"}

    # Use the injected LoggingService
    LoggingService.log(f"Params: {req.query_params.get('bar')}")

    return {**res, **ctx}


@app.get("/foo/:bar")
async def handler2(req: Request) -> dict:
    bar = req.path_params.get("bar")
    res = {"message": f"Hello, {bar}!"}

    return res
