from multiprocessing import Process
import asyncio
import requests
import uvicorn
import unittest
import unittest.async_case

from app.app import App


app = App()


@app.get("/")
async def handler(req):
    return {"message": "Hello, world!"}


@app.get("/sync")
def sync_handler(req):
    return {"message": "Hello, sync world!"}


def run_server():
    uvicorn.run(app, port=5050)


class TestE2E(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        """Bring server up."""
        self.proc = Process(target=run_server, args=(), daemon=False)
        self.proc.start()
        await asyncio.sleep(0.2)  # time for the server to start

    # async def test_basic_route(self):
    #     response = requests.get("http://localhost:5050/")
    #     print(response.json())
    #     self.assertEqual(response.status_code, 200)

    async def test_sync_route(self):
        response = requests.get("http://localhost:5050/sync")
        print(response.content)
        self.assertEqual(response.status_code, 200)

    async def asyncTearDown(self):
        self.proc.terminate()