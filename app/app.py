from typing import Any, Callable, List, Tuple, Type

from app.handler import Handler
from app.models import Request
from app.response import format_response
from app.utils import parse_scope


class Router:
    _handlers: dict[str, dict[str, Handler]]

    def __init__(self) -> None:
        self._handlers = {"GET": {}, "POST": {}, "PUT": {}, "DELETE": {}}

    def get_handler(self, method: str, path: str) -> Handler:
        return self._handlers[method].get(path)

    def route(self, method: str, path: str) -> Callable[[Handler], Callable]:
        def decorator(handler: Handler) -> Callable:
            # Register the handler for the given path and method
            self._handlers[method][path] = handler
            return handler  # Return the handler unchanged

        return decorator

    def get(self, path: str) -> Callable[[Handler], Callable]:
        return self.route("GET", path)

    def post(self, path: str) -> Callable[[Handler], Callable]:
        return self.route("POST", path)

    def put(self, path: str) -> Callable[[Handler], Callable]:
        return self.route("PUT", path)

    def delete(self, path: str) -> Callable[[Handler], Callable]:
        return self.route("DELETE", path)


class DependencyInjector:
    _injected_services: dict[str, Any]

    def __init__(self) -> None:
        self._injected_services = {}

    def inject(
        self, service_class: Type, name: str = None
    ) -> Callable[[Callable], Callable]:
        def decorator(handler: Callable) -> Callable:
            instance = service_class()
            service_name = name if name else service_class.__name__
            self._injected_services[service_name] = instance

            async def wrapped_handler(req: Request, ctx: dict, *args, **kwargs):
                return await handler(
                    req, ctx, *args, **kwargs, **{service_name: instance}
                )

            return wrapped_handler

        return decorator


class App:
    def __init__(self) -> None:
        # Compose the Router and DependencyInjector
        self.router = Router()
        self.injector = DependencyInjector()

    def get(self, path: str) -> Callable[[Handler], Callable]:
        return self.router.get(path)

    def post(self, path: str) -> Callable[[Handler], Callable]:
        return self.router.post(path)

    def put(self, path: str) -> Callable[[Handler], Callable]:
        return self.router.put(path)

    def delete(self, path: str) -> Callable[[Handler], Callable]:
        return self.router.delete(path)

    def inject(
        self, service_class: Type, name: str = None
    ) -> Callable[[Callable], Callable]:
        return self.injector.inject(service_class, name)

    def middleware(self, middlewares: List[Callable]) -> Callable[[Callable], Callable]:
        def decorator(handler: Callable) -> Callable:
            async def wrapped_handler(req: Request, *args, **kwargs):
                ctx = {}
                for middleware in middlewares:
                    # Each middleware returns the modified request and context
                    req, middleware_ctx = await middleware(req)
                    # Merge the context from each middleware
                    ctx.update(middleware_ctx)

                # Call the original handler with the modified request and context
                return await handler(req, ctx=ctx, **kwargs)

            return wrapped_handler

        return decorator

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        async def uvicorn_handler(scope: dict, receive: Any, send: Any) -> None:
            if scope["type"] == "http":
                req = parse_scope(scope)

                handler = self.router.get_handler(req.method, req.path)
                if handler is None:
                    # Handle 404 not found
                    response = {"status": 404, "headers": [], "body": b"Not found"}
                else:
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

        # Return uvicorn_handler as the callable for ASGI app
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


@app.get("/:foo/:bar")
async def handler2(req: Request) -> dict:
    res = {"message": "Hello, foo!"}

    return res
