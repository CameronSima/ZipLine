from typing import Any, Callable
from app.models import Request


class DependencyInjector:
    _injected_services: dict[str, Any]

    def __init__(self) -> None:
        self._injected_services = {}

    def inject(
        self, service_class: Any, name: str = None
    ) -> Callable[[Callable], Callable]:
        def decorator(handler: Callable | None) -> Callable:
            instance, service_name = self.add_injected_service(service_class, name)

            async def wrapped_handler(req: Request, **kwargs):
                return await handler(req, **kwargs, **{service_name: instance})

            return wrapped_handler

        return decorator

    def add_injected_service(self, service_class: Any, name: str = None) -> None:
        service_name = name if name else service_class.__name__.lower()

        if service_name in self._injected_services:
            instance = self._injected_services[service_name]
        elif isinstance(service_class, type):
            instance = service_class()
        else:
            instance = service_class

        self._injected_services[service_name] = instance
        return instance, service_name


injector = DependencyInjector()


# function to inject a service into a handler outside the main file
# (services, etc)
def inject(service_class: Any, name: str = None) -> Callable[[Callable], Callable]:
    print(f"Injecting {service_class} with name {name}")
    return injector.inject(service_class, name)
