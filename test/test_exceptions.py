import unittest

from ziplineio.app import App
from ziplineio.exception import BaseHttpException
from ziplineio.utils import call_handler


class TestExceptions(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Initialize the app
        self.app = App()

    async def test_base_exception(self):
        # Inject the service
        @self.app.get("/exception")
        async def test_handler(req):
            raise BaseHttpException("Hey! We messed up", 409)

        # Call the handler
        response = await call_handler(test_handler, {})
        self.assertEqual(response["body"], b"Hey! We messed up")
        self.assertEqual(response["status"], 409)

    async def test_exception_extends_base_exception(self):
        class CustomHttpException(BaseHttpException):
            pass

        @self.app.get("/exception")
        async def test_handler(req):
            raise CustomHttpException("Hey! We messed up bad", 402)

        # Call the handler
        response = await call_handler(test_handler, {})
        self.assertEqual(response["body"], b"Hey! We messed up bad")
        self.assertEqual(response["status"], 402)
