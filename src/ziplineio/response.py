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
        self.headers = headers
        self.body = body

    status: int
    headers: Dict[str, str]
    body: str


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
    raise ValueError("Invalid body type")


def format_response(response: bytes | dict | str | Response) -> RawResponse:
    if isinstance(response, bytes):
        return {
            "headers": [
                (b"content-type", b"text/plain"),
            ],
            "status": 200,
            "body": response,
        }
    elif isinstance(response, str):
        return {
            "headers": [
                (b"content-type", b"text/plain"),
            ],
            "status": 200,
            "body": bytes(response, "utf-8"),
        }
    elif isinstance(response, dict):
        return {
            "headers": [
                (b"content-type", b"application/json"),
            ],
            "status": 200,
            "body": bytes(json.dumps(response), "utf-8"),
        }
    elif isinstance(response, Response):
        return {
            "headers": format_headers(response.headers),
            "status": response.status,
            "body": format_body(response.body),
        }
    elif isinstance(response, BaseHttpException):
        return {
            "headers": [
                (b"content-type", b"application/json"),
            ],
            "status": response.status_code,
            "body": format_body(response.message),
        }
    print(type(response))
    raise ValueError("Invalid response type")
