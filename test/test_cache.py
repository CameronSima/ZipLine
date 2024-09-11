import unittest
import random
from ziplineio.app import App
from ziplineio.cache import MemoryCache, set_cache, cache
from ziplineio.dependency_injector import inject
from ziplineio.request import Request


class TestMemoryCache(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.app = App()
        set_cache(MemoryCache())

    async def test_handler_cache(self):
        @self.app.get("/cached_number")
        @cache(5)
        async def handler():
            return random.randint(0, 9999)

        req: Request = Request("GET", "/cached_number")

        first_call = await self.app._get_and_call_handler("GET", "/cached_number", req)
        second_call = await self.app._get_and_call_handler("GET", "/cached_number", req)

        print("HERE", first_call, second_call)

        # Ensure the result is cached
        self.assertEqual(first_call, second_call)

    async def test_handler_cache_with_dep_injector(self):
        class Service:
            def speak():
                return "Hello"

        @self.app.get("/cached_number")
        @inject(Service)
        @cache(5)
        async def handler(s: Service):
            return s.speak() + str(random.randint(0, 9999))

        req: Request = Request("GET", "/cached_number")

        first_call = await self.app._get_and_call_handler("GET", "/cached_number", req)
        second_call = await self.app._get_and_call_handler("GET", "/cached_number", req)

        print("HERE", first_call, second_call)

        # Ensure the result is cached
        self.assertEqual(first_call, second_call)
