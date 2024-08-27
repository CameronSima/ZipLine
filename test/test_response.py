from multiprocessing import Process
from os import path
import unittest


import uvicorn
import requests
import asyncio
from ziplineio.response import StaticFileResponse
from ziplineio.app import App


def staticfiles(filepath: str, path_prefix: str = "/static"):
    async def handler(req, ctx):
        print(f"Request path: {req.path}")
        if req.path.startswith(path_prefix):
            # remove path prefix
            _filepath = path.join(filepath, req.path[len(path_prefix) :])
            # add filepath
            _filepath = filepath + _filepath
            # get full path
            _filepath = path.abspath(_filepath)
            print(f"Filepath: {_filepath}")
            return StaticFileResponse(_filepath)
        return req, ctx

    return handler


app = App()
app.middleware([staticfiles("test/mocks/static")])


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
        print(r.content)

    async def asyncTearDown(self):
        self.proc.terminate()
