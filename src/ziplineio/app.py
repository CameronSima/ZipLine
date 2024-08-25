from typing import Any, Callable, List, Tuple, Type
import inspect
import asyncio
from ziplineio.dependency_injector import inject, injector, DependencyInjector
from ziplineio.exception import BaseHttpException
from ziplineio.handler import Handler
from ziplineio.models import Request
from ziplineio.response import RawResponse, format_response
from ziplineio.router import Router
from ziplineio.utils import parse_scope


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
            print(f"Service: {service}")
            handler = inject(service, name)(handler)

        return handler, params

    def inject(
        self, service_class: Type, name: str = None
    ) -> Callable[[Callable], Callable]:
        return self._injector.add_injected_service(service_class, name, "app")

    def middleware(self, middlewares: List[Callable]) -> Callable[[Callable], Callable]:
        def decorator(handler: Callable) -> Callable:
            async def wrapped_handler(req: Request, **kwargs):
                # Ensure 'ctx' is always present in kwargs
                print(f"Kwargs: {kwargs}")
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

    async def call_handler(self, handler: Handler, req: Request) -> RawResponse:
        try:
            if not inspect.iscoroutinefunction(handler):
                response = await asyncio.to_thread(handler, req)
            else:
                response = await handler(req)
            print(f"Response in call_handler: {response}")
            print(f"Response type: {type(response)}")

        except BaseHttpException as e:
            response = e
        except Exception as e:
            response = BaseHttpException(e, 500)

        print(f"Response: {response}")

        return format_response(response)

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        async def uvicorn_handler(scope: dict, receive: Any, send: Any) -> None:
            if scope["type"] == "http":
                req = parse_scope(scope)
                handler, path_params = self.get_handler(req.method, req.path)
                if handler is None:
                    response = {"status": 404, "headers": [], "body": b"Not found"}
                else:
                    req.path_params = path_params
                    response = await self.call_handler(handler, req)

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
@inject(LoggingService)
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
