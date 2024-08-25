import unittest

from app.app import App
from app.router import Router
from app.dependency_injector import DependencyInjector, inject
import app.dependency_injector


class MockService:
    pass


class TestDependencyInjection(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Initialize the app
        self.app = App()

        # reset the injector
        app.dependency_injector.injector = DependencyInjector()
        self.app._injector = app.dependency_injector.injector

    async def test_inject_service(self):
        # Define a service to inject
        class Service:
            def __init__(self):
                self.value = "Service value"

        # Inject the service
        @inject(Service)
        async def test_handler(req, service: Service):
            return {"message": service.value}

        # Call the handler
        response = await test_handler({})
        self.assertEqual(response["message"], "Service value")

    async def test_multiple_inject_same_instance(self):
        # Define a service to inject
        class Service:
            def __init__(self):
                self.value = "Service value"

        # Inject the service
        @inject(Service, name="service")
        async def test_handler1(req, service: Service):
            return {"message": service.value}

        # Inject the service again
        @inject(Service, name="service")
        async def test_handler2(req, service: Service):
            return {"message": service.value}

        # expect 1 instance of the service
        self.assertEqual(len(self.app._injector._injected_services["func"]), 1)

    async def inject_without_params(self):
        # Define a service to inject
        class Service:
            def __init__(self):
                self.value = "Service value"

        # Inject the service
        @inject(Service)
        async def test_handler(req):
            return {"message": "No service"}

        # Call the handler; should not raise an error
        response = await test_handler({})
        self.assertEqual(response["message"], "No service")

    async def test_inject_service_with_name(self):
        # Define a service to inject
        class Service:
            def __init__(self):
                self.value = "Service value"

        # Inject the service
        @inject(Service, name="my_service")
        async def test_handler(req, my_service: Service):
            return {"message": my_service.value}

        # Call the handler
        response = await test_handler({})
        self.assertEqual(response["message"], "Service value")

    async def test_inject_app_level_service(self):
        # Inject the service at the app level

        self.app.inject(MockService, name="service")

        @self.app.get("/")
        async def test_handler1(req, service: MockService):
            return {"message": f"Service {MockService} injected"}

        # doesn't throw an error
        @self.app.get("/no-service")
        async def test_handler2(req):
            return {"message": "No service injected"}

        # Call the handler
        handler, params = self.app.get_handler("GET", "/")
        response = await handler({})
        self.assertEqual(response["message"], f"Service {MockService} injected")

    async def test_inject_router_level(self):
        # Define a service to inject
        class Service:
            def __init__(self):
                self.value = "Service"

        # Create a router
        router = Router()

        # Inject the service at the router level
        router.inject(Service, name="service")

        @router.get("/")
        async def test_handler(req, service: Service):
            return {"message": service.value}

        # Call the handler
        handler, params = router.get_handler("GET", "/")
        response = await handler({})
        self.assertEqual(response["message"], "Service")
