class MemoryCache:
    _cache: dict[str, str]

    def __init__(self) -> None:
        self._cache = {}

    def get(self, key: str) -> str | None:
        return self._cache.get(key, None)

    def set(self, key: str, value: str) -> None:
        self._cache[key] = value


memory_cache = MemoryCache()
