import inspect
from typing import Any, Callable
from ziplineio.request import Request
from ziplineio.service import Service, is_service_class


# Injected services is a dictionary that stores the services that are injected.
# Services are stored in the dictionary based on the scope of the service.
# Default, handler-level services are stored in the 'func' scope.
# App-level services are stored in the 'app' scope.
# Router level services are stored in the scope of router's id.

# ***
# {
#    "func": {},
#    "app": {},
#    "<some-uuid>": {}
# }


class DependencyInjector:
    _injected_services: dict[str, Any]

    def __init__(self) -> None:
        self._injected_services = {
            "app": {},
            "func": {},
        }

    def inject(
        self, service_class: Any, name: str = None, scope: str = "func"
    ) -> Callable[[Callable], Callable]:
        def decorator(handler: Callable | None) -> Callable:
            instance, service_name = self.add_injected_service(
                service_class, name, scope
            )

            async def wrapped_handler(req: Request, **kwargs):
                return await handler(req, **kwargs, **{service_name: instance})

            return wrapped_handler

        return decorator

    def add_injected_service(
        self, service_class: Any, name: str = None, scope: str = "func"
    ) -> None:
        if scope not in self._injected_services:
            self._injected_services[scope] = {}

        if name:
            service_name = name
        elif hasattr(service_class, "name"):
            service_name = service_class.name
        else:
            service_name = service_class.__name__.lower()

        services = self._injected_services[scope]

        # Check if the service class is a subclass of `Service`
        if is_service_class(service_class):
            sig = inspect.signature(service_class.__init__)
            services_in_scope = self.get_injected_services(scope)

            # Prepare dependencies for the current service instance
            service_kwargs = {
                name: service
                for name, service in services_in_scope.items()
                if isinstance(service, Service) and name in sig.parameters
            }

            # Create a new instance of the service
            instance = service_class(**service_kwargs)
            services[service_name] = instance

            # Inject this service instance into all other services within the scope
            for _name, service in services_in_scope.items():
                if isinstance(service, Service):
                    sig = inspect.signature(service.__init__)
                    if service_name in sig.parameters:
                        setattr(service, service_name, instance)

            return instance, service_name
        else:
            # Handle services that are not subclasses of `Service`
            if service_name in services:
                instance = services[service_name]
            elif isinstance(service_class, type):
                instance = service_class()
            else:
                instance = service_class

            services[service_name] = instance
            return instance, service_name

    def get_injected_services(self, scope: str = "func") -> dict[str, Any]:
        if scope not in self._injected_services:
            self._injected_services[scope] = {}
        return self._injected_services.get(scope, {})


injector = DependencyInjector()


# function to inject a service into a handler outside the main file
# (services, etc)
def inject(
    service_class: Any, name: str = None, scope: str = "func"
) -> Callable[[Callable], Callable]:
    return injector.inject(service_class, name, scope)
