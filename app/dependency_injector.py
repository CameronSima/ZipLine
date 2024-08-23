from typing import Any, Type, Callable
from app.models import Request


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

            async def wrapped_handler(req: Request, **kwargs):
                return await handler(req, **kwargs, **{service_name: instance})

            return wrapped_handler

        return decorator
