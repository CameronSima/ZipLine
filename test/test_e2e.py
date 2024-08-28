from multiprocessing import Process
import asyncio
import requests
import uvicorn
import unittest
import unittest.async_case


from ziplineio.app import App
from ziplineio.router import Router


app = App()


@app.get("/bytes")
async def bytes_handler(req):
    return b"Hello, world!"


@app.get("/dict")
async def dict_handler(req):
    return {"message": "Hello, world!"}


@app.get("/str")
async def str_handler(req):
    return "Hello, world!"


# Will be made multithreaded
@app.get("/sync-thread")
def sync_handler(req):
    return {"message": "Hello, sync world!"}


user_router = Router("/user")


@user_router.get("/:id")
async def user_handler(req):
    return {"message": f"User {req.path_params['id']} received"}


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
        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Hello, world!"})

    async def test_sync_route(self):
        response = requests.get("http://localhost:5050/sync-thread")
        print(response.content)
        self.assertEqual(response.status_code, 200)

    async def test_404(self):
        response = requests.get("http://localhost:5050/some-random-route")
        self.assertEqual(response.status_code, 404)

    async def asyncTearDown(self):
        self.proc.terminate()
