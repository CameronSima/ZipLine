import unittest

from ziplineio.app import App
from ziplineio.request import Request
from ziplineio.response import StaticFileResponse


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
        self.assertTrue(b"background-color: #f0f0f0;" in r.body)
