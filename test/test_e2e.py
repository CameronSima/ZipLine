from multiprocessing import Process
import asyncio
from jinja2 import Environment, PackageLoader, select_autoescape
import requests
import uvicorn
import unittest
import unittest.async_case


from ziplineio.app import App
from ziplineio.html.jinja import jinja
from ziplineio.router import Router
from ziplineio.service import Service

env = Environment(loader=PackageLoader("test.mocks"), autoescape=select_autoescape())

app = App()


class Service1(Service):
    name = "service1"


class Service2(Service):
    name = "service2"

    def __init__(self, service1: Service1):
        self.service1 = service1


app.inject([Service1, Service2])


@app.get("/jinja")
@jinja(env, "home.html")
def jinja_handler(service2: Service2):
    return {"content": service2.service1.name + " content"}


@app.get("/bytes")
async def bytes_handler():
    return b"Hello, world!"


@app.get("/dict")
async def dict_handler(req):
    return {"message": "Hello, world!"}


@app.get("/str")
async def str_handler():
    return "Hello, world!"


# Will be made multithreaded
@app.get("/sync-thread")
def sync_handler():
    return {"message": "Hello, sync world!"}


user_router = Router("/user")


@user_router.get("/:id")
async def user_handler(req):
    return {"message": f"User {req.path_params['id']} received"}


@app.not_found
@jinja(env, "404.html")
def not_found():
    return {"current_route": "404"}


def run_server():
    uvicorn.run(app, port=5050)


class TestE2E(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        """Bring server up."""
        self.proc = Process(target=run_server, args=(), daemon=False)
        self.proc.start()
        await asyncio.sleep(0.2)  # time for the server to start

    async def test_handler_returns_bytes(self):
        response = requests.get("http://localhost:5050/bytes")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Hello, world!")

    async def test_handler_returns_str(self):
        response = requests.get("http://localhost:5050/str")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "Hello, world!")

    async def test_handler_returns_dict(self):
        response = requests.get("http://localhost:5050/dict")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Hello, world!"})

    async def test_sync_route(self):
        response = requests.get("http://localhost:5050/sync-thread")
        self.assertEqual(response.status_code, 200)

    async def test_jinja(self):
        response = requests.get("http://localhost:5050/jinja")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("service1 content" in response.text)

    async def test_404_jinja(self):
        response = requests.get("http://localhost:5050/some-random-route")
        self.assertEqual(response.status_code, 404)
        self.assertTrue("404" in response.text)
        self.assertEqual(response.headers["Content-Type"], "text/html")

    async def asyncTearDown(self):
        self.proc.terminate()
