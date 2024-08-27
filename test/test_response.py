from multiprocessing import Process

import unittest


import uvicorn
import requests
import asyncio

from ziplineio.app import App


app = App()
app.static("test/mocks/static", path_prefix="/static")


@app.get("/")
async def home(req):
    return {"message": "Hello, world!"}


def run_server():
    uvicorn.run(app, port=5050)


class TestResponse(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        """Bring server up."""
        self.proc = Process(target=run_server, args=(), daemon=False)
        self.proc.start()
        await asyncio.sleep(0.2)  # time for the server to start

    async def test_static_file(self):
        r = requests.get("http://localhost:5050/static/css/test.css")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["Content-Type"], "text/css")
        self.assertTrue("background-color: #f0f0f0;" in r.text)
        print(r.content)

    async def asyncTearDown(self):
        self.proc.terminate()
