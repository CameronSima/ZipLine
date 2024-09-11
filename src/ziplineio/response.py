import json
from typing import List, Tuple, TypedDict, Dict


from ziplineio.exception import BaseHttpException


class RawResponse(TypedDict):
    headers: List[Tuple[bytes, bytes]]
    status: int
    body: bytes


class Response:
    def __init__(self, status: int, headers: Dict[str, str], body: str):
        self.status = status
        self._headers = headers
        self.body = body

    status: int
    _headers: Dict[str, str]
    body: str

    # If content-type is not provided, infer content-type from the body
    def get_headers(self) -> Dict[str, str]:
        headers = self._headers.copy()
        if "Content-Type" not in headers:
            if isinstance(self.body, bytes):
                headers["Content-Type"] = "text/plain"
            elif isinstance(self.body, str):
                headers["Content-Type"] = "text/html"
            elif isinstance(self.body, dict):
                headers["Content-Type"] = "application/json"
            else:
                headers["Content-Type"] = "text/plain"
        return headers

    def __len__(self) -> int:
        return 1


class StaticFileResponse(Response):
    def __init__(self, file_path: str, headers: Dict[str, str]):
        body = self.get_file(file_path)
        super().__init__(200, headers, body)

    def get_file(self, file_path: str) -> bytes:
        with open(file_path, "rb") as file:
            return file.read()


class JinjaResponse(Response):
    def __init__(self, body: str):
        super().__init__(200, {"Content-Type": "text/html"}, body)


class NotFoundResponse(Response):
    def __init__(self, body: str, headers: Dict[str, str] = {}):
        super().__init__(404, headers, body)


def format_headers(headers: Dict[str, str] | None) -> List[Tuple[bytes, bytes]]:
    if headers is None:
        return []
    return [(bytes(k, "utf-8"), bytes(v, "utf-8")) for k, v in headers.items()]


def format_body(body: bytes | str | dict) -> bytes:
    if isinstance(body, bytes):
        return body
    elif isinstance(body, str):
        return bytes(body, "utf-8")
    elif isinstance(body, dict):
        return bytes(json.dumps(body), "utf-8")
    elif isinstance(body, Response):
        return format_body(body.body)
    raise ValueError("Invalid body type")


def format_response(
    response: bytes | dict | str | Response | Exception, default_headers: dict[str, str]
) -> RawResponse:
    # Helper to merge and deduplicate headers

    # Format different response types
    if isinstance(response, bytes):
        headers = [(b"content-type", b"text/plain")]
        body = response
        status = 200

    elif isinstance(response, str):
        headers = [(b"content-type", b"text/plain")]
        body = response.encode("utf-8")
        status = 200

    elif isinstance(response, dict):
        headers = [(b"content-type", b"application/json")]
        body = json.dumps(response).encode("utf-8")
        status = 200

    elif isinstance(response, Response):
        headers = format_headers(response.get_headers())
        body = format_body(response.body)
        status = response.status

    elif isinstance(response, BaseHttpException):
        headers = [(b"content-type", b"application/json")]
        body = format_body(response.message)
        status = response.status_code

    elif isinstance(response, Exception):
        headers = [(b"content-type", b"text/plain")]
        body = f"Internal server error: {str(response)}".encode("utf-8")
        status = 500

    else:
        raise ValueError("Invalid response type")

    default_headers = format_headers(default_headers)

    return {"headers": default_headers + headers, "status": status, "body": body}
