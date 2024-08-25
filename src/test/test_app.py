import unittest
from unittest.mock import AsyncMock
from ziplineio.dependency_injector import inject
from ziplineio.models import Request
from ziplineio.app import App, Router


class LoggingService:
    pass


LoggingService.log = AsyncMock()


class TestApp(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Initialize the app
        self.app = App()

        # Example middleware that just passes through the request
        async def example_middleware(req, **kwargs):
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
        handler, params = self.app._router.get_handler("GET", "/")
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
        handler, params = self.app._router.get_handler("GET", "/with-middleware")
        response = await handler(req)

        # Assertions
        self.assertEqual(response["message"], "Middleware test")
        self.assertEqual(response["example_ctx"], "some_value")

    async def test_dependency_injection(self):
        # Mock request data
        req = Request(method="GET", path="/with-middleware")

        # Define a handler with middleware
        @self.app.get("/")
        @inject(LoggingService, name="logger")
        async def test_handler_with_dependency(
            req: Request, ctx: dict, logger: LoggingService
        ):
            await logger.log("Dependency test")
            return {**ctx, "message": "Middleware test"}

        # Call the route
        handler, params = self.app._router.get_handler("GET", "/")
        await handler(req, ctx={})

        # Assertions

        LoggingService.log.assert_called_with("Dependency test")

    async def test_route_not_found(self):
        # Call the route
        handler, params = self.app._router.get_handler("GET", "/not-found")

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
        handler, params = self.app._router.get_handler("POST", "/submit")
        response = await handler(req)

        # Assertions
        self.assertEqual(response["message"], "Post received")

    async def test_sub_route(self):
        # Mock request data for a POST route
        req = Request(method="GET", path="/submit")

        @self.app.get("/userform/submit")
        async def post_handler(req: Request):
            return {"message": "Post received"}

        # Call the route
        handler, params = self.app._router.get_handler("GET", "/userform/submit")
        response = await handler(req)

        # Assertions
        self.assertEqual(response["message"], "Post received")

    async def test_sub_routers(self):
        foo_router = Router("/b")

        @foo_router.get("/c")
        async def bar_handler(req: Request):
            return {"message": "Foo Bar received"}

        req = Request(method="GET", path="/a/b/c")

        self.app.router("/a", foo_router)

        # Call the route
        handler, params = self.app._router.get_handler("GET", "/a/b/c")
        response = await handler(req)

        # Assertions
        self.assertEqual(response["message"], "Foo Bar received")

    async def test_wildcard_route(self):
        # Mock request data for a POST route
        req = Request(method="GET", path="/user/123")

        @self.app.get("/user/:id")
        async def user_handler(req: Request):
            return {"message": f"User {req.path_params['id']} received"}

        # Call the route
        handler, params = self.app._router.get_handler("GET", "/user/123")
        req.path_params = params
        response = await handler(req)

        # Assertions
        self.assertEqual(response["message"], "User 123 received")


if __name__ == "__main__":
    unittest.main()
