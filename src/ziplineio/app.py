import inspect
from typing import Any, Callable, List, Tuple, Type

from ziplineio.exception import NotFoundHttpException
from ziplineio.middleware import run_middleware_stack
from ziplineio.dependency_injector import inject, injector, DependencyInjector
from ziplineio import settings
from ziplineio.handler import Handler
from ziplineio.request import Request
from ziplineio.request_context import set_request
from ziplineio.response import Response, NotFoundResponse, format_response
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
        def decorator(handler: Handler) -> Callable:
            wrapped_handler = self.app_services_wrapper(handler)
            return self._router.get(path)(wrapped_handler)

        return decorator

    def post(self, path: str) -> Callable[[Handler], Callable]:
        # return self._router.post(path)
        def decorator(handler: Handler) -> Callable:
            wrapped_handler = self.app_services_wrapper(handler)
            return self._router.post(path)(wrapped_handler)

        return decorator

    def put(self, path: str) -> Callable[[Handler], Callable]:
        def decorator(handler: Handler) -> Callable:
            wrapped_handler = self.app_services_wrapper(handler)
            return self._router.put(path)(wrapped_handler)

        return decorator

    def delete(self, path: str) -> Callable[[Handler], Callable]:
        def decorator(handler: Handler) -> Callable:
            wrapped_handler = self.app_services_wrapper(handler)
            return self._router.delete(path)(wrapped_handler)

        return decorator

    def not_found(self, handler: Handler) -> None:
        self._router.not_found(handler)

    def app_services_wrapper(self, handler: Handler) -> Callable:
        app_level_deps = self._injector.get_injected_services("app")
        sig = inspect.signature(handler)

        filtered_kwargs_names = [
            name
            for name, param in sig.parameters.items()
            if param.default == inspect.Parameter.empty
        ]

        # Inject each service into the handler
        for name, service in app_level_deps.items():
            if "kwargs" in sig.parameters or name in filtered_kwargs_names:
                handler = inject(service, name)(handler)

        return handler

    def get_handler(self, method: str, path: str) -> Tuple[Handler, dict]:
        handler, params = self._router.get_handler(method, path)

        if handler is None:
            return None, {}

        return handler, params

    def inject(
        self, service_class: Type, name: str = None
    ) -> Callable[[Callable], Callable]:
        if isinstance(service_class, list):
            for service in service_class:
                self._injector.add_injected_service(service, name, "app")
            return None
        return self._injector.add_injected_service(service_class, name, "app")

    def middleware(self, middlewares: List[Callable]) -> None:
        self._router.middleware(middlewares)

    def static(self, path: str, path_prefix: str = "/static") -> None:
        self.middleware([staticfiles(path, path_prefix)])

    async def _get_and_call_handler(
        self, method: str, path: str, req: Request
    ) -> Callable:
        # Retrieve the handler and path parameters for the given method and path
        handler, path_params = self.get_handler(method, path)
        req.path_params = path_params

        # set request context
        set_request(req)

        if handler is not None:
            # If a handler is found, call it with the request
            return await call_handler(handler, req=req)

        # If no handler was found, attempt to run middlewares.
        # (If a handler was found, middlewares will be run by `call_handler`)
        req, ctx, res = await run_middleware_stack(
            self._router._router_level_middelwares, req=req
        )

        # If middleware does not provide a response, return a 404 Not Found
        # return res if res is not None else NotFoundHttpException()
        if res is not None:
            return res

        if self._router._not_found_handler:
            response = await call_handler(self._router._not_found_handler, req=req)
            headers = isinstance(response, Response) and response._headers or {}
            return NotFoundResponse(response, headers)

        return NotFoundHttpException()

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        async def uvicorn_handler(scope: dict, receive: Any, send: Any) -> None:
            if scope["type"] == "http":
                req = await parse_scope(scope, receive)
                response = await self._get_and_call_handler(req.method, req.path, req)
                raw_response = format_response(response, settings.DEFAULT_HEADERS)

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
