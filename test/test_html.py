import asyncio
from multiprocessing import Process
import unittest

import requests
import uvicorn
from jinja2 import Environment, PackageLoader, select_autoescape
from ziplineio.app import App

from ziplineio.html.jinja import jinja

env = Environment(loader=PackageLoader("test.mocks"), autoescape=select_autoescape())

app = App()


@app.get("/")
@jinja(env, "home.html")
def home(req):
    return {"message": "Hello, world!"}


def run_server():
    uvicorn.run(app, port=5050)


class TestHtml(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        """Bring server up."""
        self.proc = Process(target=run_server, args=(), daemon=False)
        self.proc.start()
        await asyncio.sleep(0.2)  # time for the server to start

    async def test_render_jinja(self):
        response = requests.get("http://localhost:5050/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "text/html")
        self.assertTrue("<p>Welcome to the home page!</p>" in response.text)

    async def asyncTearDown(self):
        self.proc.terminate()
