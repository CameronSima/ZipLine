from typing import TypedDict, List, Tuple, Optional, Dict, Any, Protocol


class ASGISend(Protocol):
    async def __call__(self, message: Dict[str, Any]) -> None:
        pass


class ASGIScope(TypedDict):
    type: str  # Typically 'http' or 'websocket'
    http_version: str  # '1.1' for HTTP/1.1, '2' for HTTP/2
    method: str  # HTTP method (e.g., 'GET', 'POST')
    scheme: str  # 'http' or 'https'
    path: str  # URL path (e.g., '/hello')
    raw_path: bytes  # The raw path as bytes
    query_string: bytes  # Raw query string in bytes (e.g., b'name=John')
    headers: List[Tuple[bytes, bytes]]  # List of (header_name, header_value) as bytes
    client: Optional[Tuple[str, int]]  # Client address (IP, port)
    server: Optional[Tuple[str, int]]  # Server address (IP, port)
    root_path: str  # The root path for routing
    app: dict  # App-specific data, typically empty
    state: dict  # State shared across different parts of the application
    extensions: dict  # ASGI extensions in use (if any)
