from collections.abc import Callable
from typing import Any, Dict, Union
from datetime import datetime, timedelta


from ziplineio.request_context import get_request
from ziplineio.utils import call_handler


class BaseCache:
    pass

    async def get(self, key: str) -> Any:
        pass

    async def set(self, key: str, value: Any, duration: Union[int, float] = 0) -> None:
        pass

    async def clear(self) -> None:
        pass


_cache: BaseCache = None


class MemoryCache(BaseCache):
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._expiry_times: Dict[str, datetime] = {}

    async def get(self, key: str) -> Any:
        """Get a cache entry."""
        if await self.is_expired(key):
            # remove the expired cache entry
            self._cache.pop(key, None)
            self._expiry_times.pop(key, None)
            return None
        return self._cache.get(key, None)

    async def set(self, key: str, value: Any, duration: Union[int, float] = 0) -> None:
        """Set a cache entry."""
        self._cache[key] = value
        self._expiry_times[key] = datetime.now() + timedelta(seconds=duration)

    async def is_expired(self, key: str) -> bool:
        """Check if a cache entry has expired."""
        if key not in self._expiry_times:
            return True
        return datetime.now() >= self._expiry_times[key]

    def clear(self):
        """Clears the cache."""
        self._cache.clear()
        self._expiry_times.clear()


def cache(duration: Union[int, float] = 0):
    """Cache decorator that accepts duration in seconds."""

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            req = get_request()

            url = req.path
            query_params_str = "&".join(
                [f"{k}={v}" for k, v in req.query_params.items()]
            )
            key = f"{func.__name__}:{kwargs}:{url}:{query_params_str}"

            # Check if the cache has expired or does not exist
            value = await _cache.get(key)
            if value is None:
                result = await call_handler(func, **kwargs)
                await _cache.set(key, result, duration)
                return result
            else:
                return value

        return wrapper

    return decorator


def get_cache() -> BaseCache:
    """Get the cache instance."""
    return _cache


def set_cache(cache: BaseCache) -> None:
    """Set the cache instance."""
    global _cache
    _cache = cache
    return None
