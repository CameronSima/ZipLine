from functools import wraps
from typing import Any

from ziplineio.handler import Handler


class MemoryCache:
    _instance = None
    _cache: dict[str, str]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(cls, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # Ensure the cache is only initialized once
        if not hasattr(self, "_cache"):
            self._cache = {}

    def get(self, key: str) -> str | None:
        return self._cache.get(key, None)

    def set(self, key: str, value: str) -> None:
        self._cache[key] = value

    def __call__(self, handler: Handler) -> Any:
        @wraps(handler)
        def wrapper(*args, **kwargs):
            # Create a key based on the arguments
            key = (args, frozenset(kwargs.items()))

            if key not in self._cache:
                # Call the function and store the result in the cache
                secache[key] = func(*args, **kwargs)
            return cache[key]

        return wrapper


memory_cache1 = MemoryCache()
memory_cache2 = MemoryCache()

print(memory_cache1 is memory_cache2)
