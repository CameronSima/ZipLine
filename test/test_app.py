import unittest
from unittest.mock import AsyncMock
from app.models import Request
from app.app import App


class LoggingService:
    pass


LoggingService.log = AsyncMock()


class TestApp(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Initialize the app
        self.app = App()

        # Example middleware that just passes through the request
        async def example_middleware(req):
            return req, {"example_ctx": "some_value"}

        # Register middlewares for testing
        self.example_middleware = [example_middleware]

    async def test_basic_route(self):
        # Mock request data
        req = Request(method="GET", path="/")
        req.query_params = {"bar": "baz"}

        # Define a simple handler for testing
        @self.app.get("/")
        async def test_handler(req: Request, ctx: dict):
            return {"message": "Hello, world!"}

        # Call the route
        handler = self.app.router.get_handler("GET", "/")
        response = await handler(req, {})

        # Assertions
        self.assertEqual(response["message"], "Hello, world!")

    async def test_middleware_injection(self):
        # Mock request data
        req = Request(method="GET", path="/with-middleware")

        # Define a handler with middleware
        @self.app.get("/with-middleware")
        @self.app.middleware(self.example_middleware)
        async def test_handler_with_middleware(req: Request, ctx: dict):
            return {**ctx, "message": "Middleware test"}

        # Call the route
        handler = self.app.router.get_handler("GET", "/with-middleware")
        response = await handler(req)

        # Assertions
        self.assertEqual(response["message"], "Middleware test")
        self.assertEqual(response["example_ctx"], "some_value")

    async def test_dependency_injection(self):
        # Mock request data
        req = Request(method="GET", path="/with-middleware")

        # Define a handler with middleware
        @self.app.get("/")
        @self.app.inject(LoggingService, name="logger")
        async def test_handler_with_dependency(
            req: Request, ctx: dict, logger: LoggingService
        ):
            await logger.log("Dependency test")
            return {**ctx, "message": "Middleware test"}

        # Call the route
        handler = self.app.router.get_handler("GET", "/")
        await handler(req, {})

        # Assertions

        LoggingService.log.assert_called_with("Dependency test")

    async def test_route_not_found(self):
        # Call the route
        handler = self.app.router.get_handler("GET", "/not-found")

        # Assertions
        self.assertIsNone(handler)

    async def test_post_route(self):
        # Mock request data for a POST route
        req = Request(method="POST", path="/submit")

        # Define a POST handler
        @self.app.post("/submit")
        async def post_handler(req: Request):
            return {"message": "Post received"}

        # Call the route
        handler = self.app.router.get_handler("POST", "/submit")
        response = await handler(req)

        # Assertions
        self.assertEqual(response["message"], "Post received")


if __name__ == "__main__":
    unittest.main()
