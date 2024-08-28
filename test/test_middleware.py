from operator import call
import unittest
from ziplineio import settings
from ziplineio.request import Request
from ziplineio.app import App
from ziplineio.middleware import middleware
from ziplineio.response import format_response
from ziplineio.utils import call_handler


class TestMiddleware(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Initialize the app
        self.app = App()

    async def test_middleware_injection(self):
        # Mock request data
        req = Request(method="GET", path="/with-middleware")

        async def my_middleware(req, **kwargs):
            return req, {"example_ctx": "some_value"}

        # Define a handler with middleware
        @self.app.get("/with-middleware")
        @middleware([my_middleware])
        async def test_handler_with_middleware(req: Request, ctx: dict):
            return {**ctx, "message": "Middleware test"}

        # Call the route
        handler, params = self.app._router.get_handler("GET", "/with-middleware")
        response = await handler(req)

        # Assertions
        self.assertEqual(response["message"], "Middleware test")
        self.assertEqual(response["example_ctx"], "some_value")

    async def test_multiple_middlewares(self):
        # Mock request data
        req = Request(method="GET", path="/with-middleware")

        async def middleware1(req, **kwargs):
            return req, {"example_ctx1": "some_value1"}

        async def middleware2(req, **kwargs):
            return req, {"example_ctx2": "some_value2"}

        async def middleware3(req, **kwargs):
            return req, {"example_ctx3": "some_value3"}

        # Define a handler with middleware
        @self.app.get("/with-middleware")
        @middleware([middleware1, middleware2, middleware3])
        async def test_handler_with_middleware(req: Request, ctx: dict):
            return {**ctx, "message": "Middleware test"}

        # Call the route
        handler, params = self.app._router.get_handler("GET", "/with-middleware")
        response = await handler(req)

        # Assertions
        self.assertEqual(response["message"], "Middleware test")
        self.assertEqual(response["example_ctx2"], "some_value2")
        self.assertEqual(len(response.keys()), 4)

    async def test_middlewares_that_throw(self):
        # Mock request data
        req = Request(method="GET", path="/with-middleware")

        async def middleware1(req, **kwargs):
            return req, {"example_ctx1": "some_value1"}

        async def middleware2(req, **kwargs):
            raise Exception("Middleware 2 failed")

        async def middleware3(req, **kwargs):
            return req, {"example_ctx3": "some_value3"}

        # Define a handler with middleware
        @self.app.get("/with-middleware")
        @middleware([middleware1, middleware2, middleware3])
        async def test_handler_with_middleware(req: Request, ctx: dict):
            return {**ctx, "message": "Middleware test"}

        # Call the route
        handler, params = self.app._router.get_handler("GET", "/with-middleware")
        response = await call_handler(handler, req)
        response = format_response(response, settings.DEFAULT_HEADERS)

        print(f"response: {response}")

        # Assertions
        self.assertEqual(response["status"], 500)
        self.assertEqual(
            response["body"], b"Internal server error: Middleware 2 failed"
        )

    async def test_middlewares_that_return(self):
        # Mock request data
        req = Request(method="GET", path="/with-middleware")

        async def middleware1(req, **kwargs):
            return req, {"example_ctx1": "some_value1"}

        async def middleware2(req, **kwargs):
            return {
                "message": "Hi from middleware 2",
            }

        async def middleware3(req, **kwargs):
            return req, {"example_ctx3": "some_value3"}

        # Define a handler with middleware
        @self.app.get("/with-middleware")
        @middleware([middleware1, middleware2, middleware3])
        async def test_handler_with_middleware(req: Request, ctx: dict):
            return {**ctx, "message": "Middleware test"}

        # Call the route
        handler, params = self.app._router.get_handler("GET", "/with-middleware")
        response = await call_handler(handler, req)

        print(response)

        # Assertions
        self.assertEqual(response["message"], "Hi from middleware 2")

    async def test_app_level_middleware(self):
        # Mock request data
        req = Request(method="GET", path="/with-middleware")

        async def app_level_middleware(req, **kwargs):
            return req, {"app_ctx": "some_value"}

        self.app.middleware([app_level_middleware])

        # Define a handler without explicit middleware
        @self.app.get("/with-middleware-1")
        async def test_handler_with_middleware(req: Request, ctx: dict):
            return {**ctx, "message": "Middleware test 1"}

        # Define another handler without explicit middleware
        @self.app.get("/without-middleware-2")
        async def test_handler_without_middleware(req: Request, ctx: dict):
            return {**ctx, "message": "Middleware test 2"}

        # Call the route
        handler, params = self.app._router.get_handler("GET", "/with-middleware-1")
        response = await handler(req)

        # Assertions
        self.assertEqual(response["message"], "Middleware test 1")
        self.assertEqual(response["app_ctx"], "some_value")

        # Call the route
        handler, params = self.app._router.get_handler("GET", "/without-middleware-2")
        response = await handler(req)

        # Assertions

        self.assertEqual(response["message"], "Middleware test 2")
        self.assertEqual(response["app_ctx"], "some_value")


if __name__ == "__main__":
    unittest.main()
