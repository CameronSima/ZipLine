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
    def __init__(self, body: str):
        super().__init__(404, {}, body)


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
    if isinstance(response, bytes):
        raw_response = {
            "headers": [
                (b"content-type", b"text/plain"),
            ],
            "status": 200,
            "body": response,
        }
    elif isinstance(response, str):
        raw_response = {
            "headers": [
                (b"content-type", b"text/plain"),
            ],
            "status": 200,
            "body": bytes(response, "utf-8"),
        }
    elif isinstance(response, dict):
        raw_response = {
            "headers": [
                (b"content-type", b"application/json"),
            ],
            "status": 200,
            "body": bytes(json.dumps(response), "utf-8"),
        }
    elif isinstance(response, Response):
        raw_response = {
            "headers": format_headers(response.get_headers()),
            "status": response.status,
            "body": format_body(response.body),
        }
    elif isinstance(response, BaseHttpException):
        raw_response = {
            "headers": [
                (b"content-type", b"application/json"),
            ],
            "status": response.status_code,
            "body": format_body(response.message),
        }
    elif isinstance(response, Exception):
        raw_response = {
            "headers": [
                (b"content-type", b"text/plain"),
            ],
            "status": 500,
            "body": b"Internal server error: " + bytes(str(response), "utf-8"),
        }
    else:
        raise ValueError("Invalid response type")

    raw_response["headers"].extend(format_headers(default_headers))
    return raw_response
