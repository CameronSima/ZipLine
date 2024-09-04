import unittest


from jinja2 import Environment, PackageLoader, select_autoescape
from ziplineio.app import App
from ziplineio.request import Request

from ziplineio.html.jinja import jinja
from ziplineio.response import JinjaResponse


env = Environment(loader=PackageLoader("test.mocks"), autoescape=select_autoescape())


class TestHtml(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.app = App()

    async def test_render_jinja(self):
        @self.app.get("/")
        @jinja(env, "home.html")
        def home(req):
            return {"message": "Hello, world!"}

        req = Request(method="GET", path="/")
        response: JinjaResponse = await self.app._get_and_call_handler("GET", "/", req)

        self.assertEqual(response.status, 200)
        self.assertEqual(response.get_headers()["Content-Type"], "text/html")
        self.assertTrue("<p>Welcome to the home page!</p>" in response.body)
