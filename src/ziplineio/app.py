from typing import Any, Callable, List, Tuple, Type


from ziplineio.middleware import middleware, run_middleware_stack
from ziplineio.dependency_injector import inject, injector, DependencyInjector
from ziplineio import settings
from ziplineio.handler import Handler
from ziplineio.request import Request
from ziplineio.response import format_response
from ziplineio.router import Router
from ziplineio.static import staticfiles
from ziplineio.utils import call_handler, parse_scope


class App:
    _router: Router
    _injector: DependencyInjector

    def __init__(self) -> None:
        self._router = Router()
        self._injector = injector

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

    def get_handler(self, method: str, path: str) -> Tuple[Handler, dict]:
        app_level_deps = self._injector._injected_services["app"]
        handler, params = self._router.get_handler(method, path)

        # TODO: Inject deps when added to the router, not here
        # inject app-level dependencies into the handler
        for name, service in app_level_deps.items():
            handler = inject(service, name)(handler)

        return handler, params

    def inject(
        self, service_class: Type, name: str = None
    ) -> Callable[[Callable], Callable]:
        return self._injector.add_injected_service(service_class, name, "app")

    def middleware(self, middlewares: List[Callable]) -> None:
        self._router.middleware(middlewares)

    def static(self, path: str, path_prefix: str = "/static") -> None:
        self.middleware([staticfiles(path, path_prefix)])

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        async def uvicorn_handler(scope: dict, receive: Any, send: Any) -> None:
            if scope["type"] == "http":
                req = parse_scope(scope)
                handler, path_params = self.get_handler(req.method, req.path)
                req.path_params = path_params

                if handler is None:
                    # try running through middlewares

                    req, ctx, res = await run_middleware_stack(
                        self._router._router_level_middelwares, req, **{}
                    )

                    if res is None:
                        response = {"status": 404, "headers": [], "body": b"Not found"}
                    else:
                        response = res

                else:
                    response = await call_handler(handler, req)

                raw_response = format_response(response, settings.DEFAULT_HEADERS)

                print("SENDING RESPONSE")
                print(raw_response)

                await send(
                    {
                        "type": "http.response.start",
                        "status": raw_response["status"],
                        "headers": raw_response["headers"],
                    }
                )

                await send(
                    {
                        "type": "http.response.body",
                        "body": raw_response["body"],
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
@inject(LoggingService)
@middleware([logging_middleware, auth_middleware])
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
