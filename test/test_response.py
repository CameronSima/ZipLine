import unittest

from ziplineio.app import App
from ziplineio.exception import BaseHttpException
from ziplineio.request import Body, Request
from ziplineio.response import (
    Response,
    StaticFileResponse,
    format_body,
    format_response,
)


class TestResponse(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.app = App()
        self.app.static("test/mocks/static", path_prefix="/static")

        @self.app.get("/")
        async def home(req):
            return {"message": "Hello, world!"}

    async def test_static_file(self):
        req = Request(method="GET", path="/static/css/test.css")
        r: StaticFileResponse = await self.app._get_and_call_handler(
            "GET", "/static/css/test.css", req
        )

        self.assertEqual(r.status, 200)
        self.assertEqual(r.get_headers()["Content-Type"], "text/css")
        self.assertTrue("background-color: #f0f0f0;" in str(r.body))


class TestFormatBody(unittest.TestCase):
    def test_format_body_dict(self):
        body = format_body({"message": "Hello, world!"})
        self.assertEqual(body, b'{"message": "Hello, world!"}')

    def test_format_body_bytes(self):
        body = format_body(b"Hello, world!")
        self.assertEqual(body, b"Hello, world!")

    def test_format_body_str(self):
        body = format_body("Hello, world!")
        self.assertEqual(body, b"Hello, world!")


class TestFormatResponse(unittest.TestCase):
    def test_format_bytes(self):
        response = b"Hello, world!"
        headers = {}
        formatted = format_response(response, headers)

        self.assertEqual(formatted["status"], 200)
        self.assertEqual(formatted["headers"], [(b"content-type", b"text/plain")])
        self.assertEqual(formatted["body"], response)

    def test_format_str(self):
        response = "Hello, world!"
        headers = {}
        formatted = format_response(response, headers)

        self.assertEqual(formatted["status"], 200)
        self.assertEqual(formatted["headers"], [(b"content-type", b"text/plain")])
        self.assertEqual(formatted["body"], b"Hello, world!")

    def test_format_dict(self):
        response = {"message": "Hello, world!"}
        headers = {}
        formatted = format_response(response, headers)

        self.assertEqual(formatted["status"], 200)
        self.assertEqual(formatted["headers"], [(b"content-type", b"application/json")])
        self.assertEqual(formatted["body"], b'{"message": "Hello, world!"}')

    def test_format_response_object(self):
        response = Response(
            200, {"Content-Type": "CUSTOM-TYPE"}, Body.from_str("Hello, world!")
        )

        formatted = format_response(response, {})
        self.assertEqual(formatted["status"], 200)
        self.assertEqual(formatted["headers"], [(b"Content-Type", b"CUSTOM-TYPE")])
        self.assertEqual(formatted["body"], b"Hello, world!")

    def test_format_exception(self):
        response = Exception("Hello, world!")
        headers = {}
        formatted = format_response(response, headers)

        self.assertEqual(formatted["status"], 500)
        self.assertEqual(formatted["headers"], [(b"content-type", b"text/plain")])
        self.assertEqual(formatted["body"], b"Internal server error: Hello, world!")

    def test_format_http_exception(self):
        response = BaseHttpException("Hello, world!", 444)
        headers = {}
        formatted = format_response(response, headers)

        self.assertEqual(formatted["status"], 444)
        self.assertEqual(formatted["headers"], [(b"content-type", b"application/json")])
        self.assertEqual(formatted["body"], b"Hello, world!")

    def test_format_bytes_with_headers(self):
        response = b"Hello, world!"
        headers = {}
        formatted = format_response(response, headers)

        self.assertEqual(formatted["status"], 200)
        self.assertEqual(formatted["headers"], [(b"content-type", b"text/plain")])
        self.assertEqual(formatted["body"], response)
