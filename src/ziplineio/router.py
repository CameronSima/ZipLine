import re

import uuid
import inspect
from typing import Any, Callable, Dict, List, Union
from ziplineio.dependency_injector import DependencyInjector, inject, injector
from ziplineio.handler import Handler
from ziplineio.middleware import middleware


class Router:
    _id: str
    _handlers: Dict[str, Dict[str, Callable]]
    _router_level_middelwares: List[Handler]
    _not_found_handler: Handler
    _sub_routers: Dict[str, "Router"]
    _prefix: str
    _injector: DependencyInjector

    def __init__(self, prefix: str = "") -> None:
        self._id = str(uuid.uuid4())
        self._handlers = {"GET": {}, "POST": {}, "PUT": {}, "DELETE": {}}
        self._router_level_middelwares = []
        self._not_found_handler = None
        self._sub_routers = {}
        self._prefix = prefix.rstrip("/")
        self._injector = injector

    def middleware(self, middlewares: List[Handler]) -> None:
        self._router_level_middelwares.extend(middlewares)

    def inject(self, service_class: Any, name: str = None) -> None:
        if isinstance(service_class, list):
            for service in service_class:
                self._injector.add_injected_service(service, name, self._id)
            return None
        self._injector.add_injected_service(service_class, name, self._id)

    def _convert_path_to_regex(self, path: str) -> str:
        # Convert a path like '/user/:id' to a regex pattern like '/user/(?P<id>[^/]+)'
        return re.sub(r":(\w+)", r"(?P<\1>[^/]+)", path) + "$"

    def route(self, method: str, path: str) -> Callable[[Callable], Callable]:
        def decorator(handler: Callable) -> Callable:
            # inject router-level dependencies into the handler
            services = injector.get_injected_services(self._id)

            sig = inspect.signature(handler)

            filtered_kwargs_names = [
                name
                for name, param in sig.parameters.items()
                if param.default == inspect.Parameter.empty
            ]

            for name, service in services.items():
                if name in filtered_kwargs_names:
                    handler = inject(service, name)(handler)

            # wrap the handler with router-level middlewares
            if len(self._router_level_middelwares) > 0:
                handler = middleware(self._router_level_middelwares)(handler)

            # Convert the path into a regex pattern
            path_regex = self._convert_path_to_regex(self._prefix + path)
            self._handlers[method][path_regex] = handler
            return handler

        return decorator

    def get(self, path: str) -> Callable[[Callable], Callable]:
        return self.route("GET", path)

    def post(self, path: str) -> Callable[[Callable], Callable]:
        return self.route("POST", path)

    def put(self, path: str) -> Callable[[Callable], Callable]:
        return self.route("PUT", path)

    def delete(self, path: str) -> Callable[[Callable], Callable]:
        return self.route("DELETE", path)

    def not_found(self, handler: Handler) -> None:
        self._not_found_handler = handler

    def add_sub_router(self, prefix: str, sub_router: "Router") -> None:
        self._sub_routers[prefix.rstrip("/")] = sub_router

    def _match_route(
        self, method: str, path: str
    ) -> Union[Callable, None, Dict[str, Any]]:
        # First, try to match in the current router
        for route_regex, handler in self._handlers[method].items():
            match = re.match(route_regex, path)
            if match:
                # Extract the path parameters
                return handler, match.groupdict()

        # Next, try to match in sub-routers
        for prefix, sub_router in self._sub_routers.items():
            if path.startswith(prefix):
                sub_path = path[len(prefix) :]
                return sub_router._match_route(method, sub_path)

        return None, {}

    def get_handler(
        self, method: str, path: str
    ) -> Union[Callable, None, Dict[str, Any]]:
        handler, params = self._match_route(method, path)
        return handler, params
